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
        # Todos ven SOLO sus cierres directos (donde son el analista asignado)
        # Para ver cierres del equipo, usar acción específica cierres_equipo
        if user.tipo_usuario in ['analista', 'supervisor']:
            queryset = queryset.filter(analista=user)
        elif user.tipo_usuario == 'senior':
            # Senior ve sus cierres y los de su equipo
            queryset = queryset.filter(
                Q(analista=user) | 
                Q(analista__in=user.supervisados.all())
            )
        # gerente ve todo
        
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

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated, IsSupervisor])
    def cierres_equipo(self, request):
        """
        Obtiene el cierre más reciente por cliente de los analistas supervisados.
        Solo para supervisores y gerentes.
        
        Retorna:
        - Lista de cierres agrupados por analista
        - Solo el cierre más reciente de cada cliente
        """
        from django.db.models import Max, Subquery, OuterRef
        from apps.core.models import Usuario, Cliente
        
        user = request.user
        
        # Obtener analistas del equipo
        if user.tipo_usuario == 'gerente':
            # Gerente ve todos los analistas
            analistas = Usuario.objects.filter(
                tipo_usuario='analista',
                is_active=True
            )
        else:
            # Supervisor ve solo sus analistas
            analistas = user.analistas_supervisados.filter(is_active=True)
        
        # Para cada analista, obtener el cierre más reciente de cada cliente
        resultado = []
        
        for analista in analistas:
            # Obtener clientes del analista
            clientes_analista = Cliente.objects.filter(
                usuario_asignado=analista,
                activo=True
            )
            
            cierres_recientes = []
            for cliente in clientes_analista:
                # Obtener cierre más reciente de este cliente
                cierre = Cierre.objects.filter(
                    cliente=cliente,
                    analista=analista
                ).order_by('-periodo', '-fecha_creacion').first()
                
                if cierre:
                    cierres_recientes.append({
                        'id': cierre.id,
                        'cliente': {
                            'id': cliente.id,
                            'nombre': cliente.nombre_comercial or cliente.razon_social,
                            'rut': cliente.rut,
                        },
                        'periodo': cierre.periodo,
                        'mes': cierre.mes,
                        'anio': cierre.anio,
                        'estado': cierre.estado,
                        'estado_display': cierre.get_estado_display(),
                        'fecha_creacion': cierre.fecha_creacion,
                        'fecha_actualizacion': cierre.fecha_actualizacion,
                    })
            
            if cierres_recientes or clientes_analista.exists():
                resultado.append({
                    'analista': {
                        'id': analista.id,
                        'nombre': analista.get_full_name(),
                        'email': analista.email,
                    },
                    'total_clientes': clientes_analista.count(),
                    'total_cierres': len(cierres_recientes),
                    'cierres': cierres_recientes
                })
        
        # Estadísticas generales
        total_cierres = sum(item['total_cierres'] for item in resultado)
        cierres_en_proceso = sum(
            1 for item in resultado 
            for c in item['cierres'] 
            if c['estado'] not in ['completado', 'finalizado', 'rechazado']
        )
        
        return Response({
            'equipo': resultado,
            'estadisticas': {
                'total_analistas': len(resultado),
                'total_cierres': total_cierres,
                'cierres_en_proceso': cierres_en_proceso,
            }
        })
