"""
Views de Servicio para SGM v2.
"""

from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend

from apps.core.models import Servicio, ServicioCliente
from apps.core.serializers import ServicioSerializer, ServicioClienteSerializer
from shared.permissions import IsGerente, IsSupervisor


class ServicioViewSet(viewsets.ModelViewSet):
    """ViewSet para gestión del catálogo de servicios."""
    
    queryset = Servicio.objects.all()
    serializer_class = ServicioSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['activo']
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), IsGerente()]
        return [IsAuthenticated()]


class ServicioClienteViewSet(viewsets.ModelViewSet):
    """ViewSet para gestión de servicios contratados por clientes."""
    
    serializer_class = ServicioClienteSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['cliente', 'servicio', 'activo']
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), IsSupervisor()]
        return [IsAuthenticated()]
    
    def get_queryset(self):
        return ServicioCliente.objects.select_related('cliente', 'servicio')
