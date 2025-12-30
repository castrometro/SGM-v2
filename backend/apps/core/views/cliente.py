"""
Views de Cliente para SGM v2.
"""

from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from apps.core.models import Cliente, Industria, AsignacionClienteUsuario
from apps.core.serializers import (
    ClienteSerializer,
    ClienteDetailSerializer,
    ClienteCreateSerializer,
    IndustriaSerializer,
)
from shared.permissions import IsGerente, IsSupervisor


class IndustriaViewSet(viewsets.ModelViewSet):
    """ViewSet para gestión de industrias."""
    
    queryset = Industria.objects.all()
    serializer_class = IndustriaSerializer
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['nombre']
    ordering = ['nombre']
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), IsGerente()]
        return [IsAuthenticated()]


class ClienteViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión de clientes.
    Los usuarios solo ven los clientes a los que tienen acceso.
    """
    
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['industria', 'activo', 'bilingue']
    search_fields = ['razon_social', 'nombre_comercial', 'rut']
    ordering_fields = ['razon_social', 'fecha_registro']
    ordering = ['razon_social']
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return ClienteDetailSerializer
        if self.action in ['create', 'update', 'partial_update']:
            return ClienteCreateSerializer
        return ClienteSerializer
    
    def get_permissions(self):
        if self.action in ['create', 'destroy']:
            return [IsAuthenticated(), IsGerente()]
        if self.action in ['update', 'partial_update']:
            return [IsAuthenticated(), IsSupervisor()]
        return [IsAuthenticated()]
    
    def get_queryset(self):
        """Filtra clientes según el rol del usuario."""
        user = self.request.user
        queryset = Cliente.objects.select_related('industria')
        
        # Gerentes ven todos los clientes
        if user.tipo_usuario == 'gerente':
            return queryset
        
        # Supervisores ven clientes de sus analistas
        if user.tipo_usuario == 'supervisor':
            analistas_ids = user.analistas_supervisados.values_list('id', flat=True)
            clientes_ids = AsignacionClienteUsuario.objects.filter(
                usuario_id__in=analistas_ids,
                activa=True
            ).values_list('cliente_id', flat=True)
            return queryset.filter(id__in=clientes_ids)
        
        # Analistas y seniors ven solo sus clientes asignados
        clientes_ids = user.asignaciones.filter(activa=True).values_list('cliente_id', flat=True)
        return queryset.filter(id__in=clientes_ids)
    
    @action(detail=True, methods=['get'])
    def cierres(self, request, pk=None):
        """Obtiene los cierres de un cliente específico."""
        cliente = self.get_object()
        # Importar aquí para evitar dependencia circular
        from apps.validador.models import Cierre
        from apps.validador.serializers import CierreListSerializer
        
        cierres = Cierre.objects.filter(cliente=cliente).order_by('-periodo')
        serializer = CierreListSerializer(cierres, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def mis_clientes(self, request):
        """Obtiene solo los clientes asignados directamente al usuario."""
        user = request.user
        clientes_ids = user.asignaciones.filter(activa=True).values_list('cliente_id', flat=True)
        clientes = Cliente.objects.filter(id__in=clientes_ids)
        serializer = ClienteSerializer(clientes, many=True)
        return Response(serializer.data)
