"""
ViewSets para Cierre.
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.db.models import Q

from ..models import Cierre
from ..serializers import (
    CierreListSerializer,
    CierreDetailSerializer,
    CierreCreateSerializer,
)
from shared.permissions import IsAnalista, IsSupervisor


class CierreViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión de Cierres.
    
    list: Lista cierres (filtrados por rol)
    retrieve: Detalle de un cierre
    create: Crear nuevo cierre
    """
    
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        queryset = Cierre.objects.select_related(
            'cliente', 'analista'
        ).all()
        
        # Filtrar según tipo de usuario
        if user.tipo_usuario == 'analista':
            queryset = queryset.filter(analista=user)
        elif user.tipo_usuario == 'senior':
            # Senior ve sus cierres y los de su equipo
            queryset = queryset.filter(
                Q(analista=user) | 
                Q(analista__in=user.supervisados.all())
            )
        # supervisor y gerente ven todo
        
        # Filtros opcionales
        cliente_id = self.request.query_params.get('cliente')
        periodo = self.request.query_params.get('periodo')
        estado = self.request.query_params.get('estado')
        
        if cliente_id:
            queryset = queryset.filter(cliente_id=cliente_id)
        if periodo:
            queryset = queryset.filter(periodo=periodo)
        if estado:
            queryset = queryset.filter(estado=estado)
        
        return queryset.order_by('-periodo', '-fecha_creacion')
    
    def get_serializer_class(self):
        if self.action == 'list':
            return CierreListSerializer
        elif self.action == 'create':
            return CierreCreateSerializer
        return CierreDetailSerializer
    
    def perform_create(self, serializer):
        """Asignar el usuario actual como analista al crear un cierre."""
        serializer.save(analista=self.request.user)
    
    @action(detail=True, methods=['post'])
    def cambiar_estado(self, request, pk=None):
        """Cambiar el estado del cierre."""
        cierre = self.get_object()
        nuevo_estado = request.data.get('estado')
        
        estados_validos = dict(Cierre.ESTADO_CHOICES).keys()
        if nuevo_estado not in estados_validos:
            return Response(
                {'error': f'Estado inválido. Válidos: {list(estados_validos)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        cierre.estado = nuevo_estado
        
        if nuevo_estado == 'consolidado':
            cierre.fecha_consolidacion = timezone.now()
        elif nuevo_estado == 'finalizado':
            cierre.fecha_finalizacion = timezone.now()
            cierre.finalizado_por = request.user
        
        cierre.save()
        
        serializer = CierreDetailSerializer(cierre)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def resumen(self, request, pk=None):
        """Obtener resumen del estado del cierre."""
        cierre = self.get_object()
        
        archivos_erp = cierre.archivos_erp.filter(es_version_actual=True)
        archivos_analista = cierre.archivos_analista.filter(es_version_actual=True)
        
        return Response({
            'id': cierre.id,
            'estado': cierre.estado,
            'estado_display': cierre.get_estado_display(),
            
            'archivos': {
                'erp': {
                    'libro_remuneraciones': archivos_erp.filter(tipo='libro_remuneraciones').exists(),
                    'movimientos_mes': archivos_erp.filter(tipo='movimientos_mes').exists(),
                },
                'analista': {
                    'novedades': archivos_analista.filter(tipo='novedades').exists(),
                    'asistencias': archivos_analista.filter(tipo='asistencias').exists(),
                    'finiquitos': archivos_analista.filter(tipo='finiquitos').exists(),
                    'ingresos': archivos_analista.filter(tipo='ingresos').exists(),
                },
            },
            
            'requiere_clasificacion': cierre.requiere_clasificacion,
            'conceptos_sin_clasificar': cierre.cliente.conceptos.filter(clasificado=False).count(),
            
            'requiere_mapeo': cierre.requiere_mapeo,
            
            'discrepancias': {
                'total': cierre.total_discrepancias,
                'resueltas': cierre.discrepancias_resueltas,
                'pendientes': cierre.total_discrepancias - cierre.discrepancias_resueltas,
            },
            
            'incidencias': {
                'total': cierre.total_incidencias,
                'aprobadas': cierre.incidencias_aprobadas,
                'pendientes': cierre.total_incidencias - cierre.incidencias_aprobadas,
            },
            
            'puede_consolidar': cierre.puede_consolidar,
            'puede_finalizar': cierre.puede_finalizar,
            'es_primer_cierre': cierre.es_primer_cierre,
        })
    
    @action(detail=True, methods=['post'])
    def consolidar(self, request, pk=None):
        """Consolidar el cierre (discrepancias = 0)."""
        cierre = self.get_object()
        
        if not cierre.puede_consolidar:
            return Response(
                {'error': 'No se puede consolidar. Hay discrepancias pendientes.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # TODO: Llamar task de consolidación
        cierre.estado = 'consolidado'
        cierre.fecha_consolidacion = timezone.now()
        cierre.save()
        
        # Si es primer cierre, saltar detección de incidencias
        if cierre.es_primer_cierre:
            cierre.estado = 'finalizado'
            cierre.fecha_finalizacion = timezone.now()
            cierre.finalizado_por = request.user
            cierre.save()
            
            return Response({
                'message': 'Cierre consolidado y finalizado (primer cierre del cliente)',
                'cierre': CierreDetailSerializer(cierre).data
            })
        
        # Detectar incidencias
        cierre.estado = 'deteccion_incidencias'
        cierre.save()
        
        # TODO: Llamar task de detección de incidencias
        
        return Response({
            'message': 'Cierre consolidado. Detectando incidencias...',
            'cierre': CierreDetailSerializer(cierre).data
        })
    
    @action(detail=True, methods=['post'])
    def finalizar(self, request, pk=None):
        """Finalizar el cierre."""
        cierre = self.get_object()
        
        if not cierre.puede_finalizar:
            return Response(
                {'error': 'No se puede finalizar. Hay incidencias pendientes.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        cierre.estado = 'finalizado'
        cierre.fecha_finalizacion = timezone.now()
        cierre.finalizado_por = request.user
        cierre.save()
        
        return Response({
            'message': 'Cierre finalizado exitosamente',
            'cierre': CierreDetailSerializer(cierre).data
        })
