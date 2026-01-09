"""
Views de ERP para SGM v2.
"""

from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from apps.core.models import ERP, ConfiguracionERPCliente
from apps.core.serializers import (
    ERPSerializer,
    ERPDetailSerializer,
    ERPCreateSerializer,
    ConfiguracionERPClienteSerializer,
    ConfiguracionERPClienteDetailSerializer,
    ConfiguracionERPClienteCreateSerializer,
)
from shared.permissions import IsGerente, IsSupervisor


class ERPViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión de ERPs.
    
    Endpoints:
    - GET /erps/ - Lista todos los ERPs
    - POST /erps/ - Crea un ERP (solo gerentes)
    - GET /erps/{id}/ - Detalle de un ERP
    - PUT/PATCH /erps/{id}/ - Actualiza ERP (solo gerentes)
    - DELETE /erps/{id}/ - Elimina ERP (solo gerentes)
    - GET /erps/activos/ - Lista ERPs activos
    """
    
    queryset = ERP.objects.all()
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['activo', 'requiere_api']
    search_fields = ['nombre', 'slug', 'descripcion']
    ordering_fields = ['nombre', 'created_at']
    ordering = ['nombre']
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return ERPDetailSerializer
        if self.action in ['create', 'update', 'partial_update']:
            return ERPCreateSerializer
        return ERPSerializer
    
    def get_permissions(self):
        """Solo gerentes pueden crear/editar/eliminar ERPs."""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), IsGerente()]
        return [IsAuthenticated()]
    
    @action(detail=False, methods=['get'])
    def activos(self, request):
        """Lista solo ERPs activos (para selectores en frontend)."""
        erps = ERP.objects.filter(activo=True).order_by('nombre')
        serializer = ERPSerializer(erps, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def clientes(self, request, pk=None):
        """Lista clientes que usan este ERP."""
        erp = self.get_object()
        configuraciones = ConfiguracionERPCliente.objects.filter(
            erp=erp,
            activo=True
        ).select_related('cliente')
        
        data = [
            {
                'id': config.cliente.id,
                'nombre': config.cliente.nombre_display,
                'rut': config.cliente.rut,
                'esta_vigente': config.esta_vigente,
                'fecha_activacion': config.fecha_activacion,
            }
            for config in configuraciones
        ]
        return Response(data)


class ConfiguracionERPClienteViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión de configuraciones ERP de clientes.
    
    Endpoints:
    - GET /configuraciones-erp/ - Lista configuraciones
    - POST /configuraciones-erp/ - Crea configuración
    - GET /configuraciones-erp/{id}/ - Detalle
    - PUT/PATCH /configuraciones-erp/{id}/ - Actualiza
    - DELETE /configuraciones-erp/{id}/ - Elimina
    - GET /configuraciones-erp/por-cliente/{cliente_id}/ - Por cliente
    """
    
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['cliente', 'erp', 'activo']
    search_fields = ['cliente__razon_social', 'erp__nombre']
    ordering_fields = ['cliente', 'fecha_activacion']
    ordering = ['cliente']
    
    def get_queryset(self):
        """
        Filtra configuraciones según permisos del usuario.
        """
        user = self.request.user
        queryset = ConfiguracionERPCliente.objects.select_related(
            'cliente', 'erp'
        )
        
        # Gerentes ven todas las configuraciones
        if user.tipo_usuario == 'gerente':
            return queryset
        
        # Supervisores ven configuraciones de sus clientes
        if user.tipo_usuario == 'supervisor':
            from django.db.models import Q
            return queryset.filter(
                Q(cliente__usuario_asignado=user) | 
                Q(cliente__usuario_asignado__supervisor=user)
            )
        
        # Analistas ven solo configuraciones de sus clientes asignados
        return queryset.filter(cliente__usuario_asignado=user)
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return ConfiguracionERPClienteDetailSerializer
        if self.action in ['create', 'update', 'partial_update']:
            return ConfiguracionERPClienteCreateSerializer
        return ConfiguracionERPClienteSerializer
    
    def get_permissions(self):
        """Solo supervisores y gerentes pueden gestionar configuraciones."""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), IsSupervisor()]
        return [IsAuthenticated()]
    
    @action(detail=False, methods=['get'], url_path='por-cliente/(?P<cliente_id>[^/.]+)')
    def por_cliente(self, request, cliente_id=None):
        """Lista configuraciones de un cliente específico."""
        configuraciones = self.get_queryset().filter(cliente_id=cliente_id)
        serializer = ConfiguracionERPClienteSerializer(configuraciones, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def vigentes(self, request):
        """Lista solo configuraciones vigentes."""
        from django.utils import timezone
        today = timezone.now().date()
        
        configuraciones = self.get_queryset().filter(
            activo=True,
            fecha_activacion__lte=today
        ).filter(
            models.Q(fecha_expiracion__isnull=True) |
            models.Q(fecha_expiracion__gte=today)
        )
        serializer = ConfiguracionERPClienteSerializer(configuraciones, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def por_expirar(self, request):
        """Lista configuraciones próximas a expirar (30 días)."""
        from django.utils import timezone
        from datetime import timedelta
        
        today = timezone.now().date()
        limite = today + timedelta(days=30)
        
        configuraciones = self.get_queryset().filter(
            activo=True,
            fecha_expiracion__isnull=False,
            fecha_expiracion__gte=today,
            fecha_expiracion__lte=limite
        ).order_by('fecha_expiracion')
        
        serializer = ConfiguracionERPClienteSerializer(configuraciones, many=True)
        return Response(serializer.data)


# Importar models para el action vigentes
from django.db import models
