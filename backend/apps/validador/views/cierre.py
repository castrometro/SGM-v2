"""
ViewSets para Cierre.

Las views son responsables de:
- Autenticación y autorización
- Serialización de entrada/salida
- Llamar a los servicios de negocio

La lógica de negocio está en: apps.validador.services.CierreService
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
from ..services import CierreService, EquipoService
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
        
        # Usar el servicio para la lógica de negocio
        result = CierreService.cambiar_estado(
            cierre=cierre,
            nuevo_estado=nuevo_estado,
            user=request.user,
            validar_transicion=True
        )
        
        if not result.success:
            return Response(
                {'error': result.error},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = CierreDetailSerializer(result.data)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def resumen(self, request, pk=None):
        """Obtener resumen del estado del cierre."""
        cierre = self.get_object()
        
        # Usar el servicio para obtener el resumen
        resumen = CierreService.obtener_resumen(cierre)
        return Response(resumen)
    
    @action(detail=True, methods=['post'])
    def consolidar(self, request, pk=None):
        """Consolidar el cierre (discrepancias = 0)."""
        cierre = self.get_object()
        
        # Usar el servicio para la consolidación
        result = CierreService.consolidar(cierre, user=request.user)
        
        if not result.success:
            return Response(
                {'error': result.error},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        cierre_actualizado = result.data
        mensaje = 'Cierre consolidado'
        
        if cierre_actualizado.estado == 'finalizado':
            mensaje = 'Cierre consolidado y finalizado (primer cierre del cliente)'
        elif cierre_actualizado.estado == 'deteccion_incidencias':
            mensaje = 'Cierre consolidado. Detectando incidencias...'
        
        return Response({
            'message': mensaje,
            'cierre': CierreDetailSerializer(cierre_actualizado).data
        })
    
    @action(detail=True, methods=['post'])
    def finalizar(self, request, pk=None):
        """Finalizar el cierre."""
        cierre = self.get_object()
        
        # Usar el servicio para finalizar
        result = CierreService.finalizar(cierre, user=request.user)
        
        if not result.success:
            return Response(
                {'error': result.error},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        return Response({
            'message': 'Cierre finalizado exitosamente',
            'cierre': CierreDetailSerializer(result.data).data
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
        # Usar el servicio para obtener los datos
        result = EquipoService.obtener_cierres_equipo(
            supervisor=request.user,
            solo_activos=request.query_params.get('solo_activos', 'false').lower() == 'true'
        )
        
        if not result.success:
            return Response(
                {'error': result.error},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        return Response(result.data)
