"""
Views de Asignación para SGM v2.
"""

from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend

from apps.core.models import AsignacionClienteUsuario
from apps.core.serializers import AsignacionClienteUsuarioSerializer
from shared.permissions import IsGerente, IsSupervisor


class AsignacionClienteUsuarioViewSet(viewsets.ModelViewSet):
    """ViewSet para gestión de asignaciones cliente-usuario."""
    
    serializer_class = AsignacionClienteUsuarioSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['cliente', 'usuario', 'activa', 'es_principal']
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), IsSupervisor()]
        return [IsAuthenticated()]
    
    def get_queryset(self):
        user = self.request.user
        queryset = AsignacionClienteUsuario.objects.select_related('cliente', 'usuario')
        
        # Gerentes ven todas las asignaciones
        if user.tipo_usuario == 'gerente':
            return queryset
        
        # Supervisores ven asignaciones de sus analistas
        if user.tipo_usuario == 'supervisor':
            analistas_ids = list(user.analistas_supervisados.values_list('id', flat=True))
            analistas_ids.append(user.id)
            return queryset.filter(usuario_id__in=analistas_ids)
        
        # Otros solo ven sus propias asignaciones
        return queryset.filter(usuario=user)
    
    def perform_destroy(self, instance):
        """En lugar de eliminar, desactiva la asignación."""
        from django.utils import timezone
        instance.activa = False
        instance.fecha_desasignacion = timezone.now()
        instance.save()
