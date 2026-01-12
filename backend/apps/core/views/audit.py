"""
ViewSet para consulta de logs de auditoría.

Solo accesible por gerentes.
Proporciona filtros por usuario, acción, modelo, cliente y fecha.
"""

from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from django_filters import rest_framework as filters

from apps.core.models import AuditLog
from apps.core.serializers.audit import AuditLogSerializer, AuditLogListSerializer
from shared.permissions import IsGerente


class AuditLogFilter(filters.FilterSet):
    """
    Filtros para AuditLog.
    
    Permite filtrar por:
        - fecha_desde/fecha_hasta: Rango de fechas
        - usuario_email: Búsqueda parcial por email
        - accion: Tipo de acción (create, update, delete, etc.)
        - modelo: Modelo afectado (ej: validador.cierre)
        - cliente_id: ID del cliente
        - usuario: ID del usuario
    """
    
    fecha_desde = filters.DateTimeFilter(field_name='timestamp', lookup_expr='gte')
    fecha_hasta = filters.DateTimeFilter(field_name='timestamp', lookup_expr='lte')
    usuario_email = filters.CharFilter(lookup_expr='icontains')
    modelo = filters.CharFilter(lookup_expr='icontains')
    
    class Meta:
        model = AuditLog
        fields = ['accion', 'modelo', 'cliente_id', 'usuario', 'usuario_email', 'objeto_id']


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet de solo lectura para logs de auditoría.
    
    Endpoints:
        GET /api/v1/core/audit-logs/           - Lista logs con filtros
        GET /api/v1/core/audit-logs/{id}/      - Detalle de un log
    
    Filtros disponibles:
        - accion: create, update, delete, login, logout, export
        - modelo: validador.cierre, validador.archivoerp, etc.
        - cliente_id: ID del cliente
        - usuario: ID del usuario
        - usuario_email: búsqueda parcial por email
        - fecha_desde: ISO datetime (ej: 2026-01-01T00:00:00)
        - fecha_hasta: ISO datetime
        - objeto_id: ID del objeto específico
    
    Ordenamiento por defecto: -timestamp (más reciente primero)
    
    Permisos: Solo gerentes pueden acceder.
    
    Compliance:
        - ISO 27001:2022 (A.8.15) - Revisión de logs
        - Ley 21.719 Chile - Auditoría de acceso a datos personales
    """
    
    permission_classes = [IsAuthenticated, IsGerente]
    filterset_class = AuditLogFilter
    
    def get_queryset(self):
        """Retorna queryset con select_related para optimizar."""
        return AuditLog.objects.select_related('usuario').all()
    
    def get_serializer_class(self):
        """Usa serializer resumido para listados, completo para detalle."""
        if self.action == 'list':
            return AuditLogListSerializer
        return AuditLogSerializer
