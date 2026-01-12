"""
Serializers para AuditLog.
"""

from rest_framework import serializers
from apps.core.models import AuditLog


class AuditLogSerializer(serializers.ModelSerializer):
    """
    Serializer para lectura de AuditLog.
    
    Incluye información del usuario y formato legible de datos.
    """
    
    usuario_nombre = serializers.SerializerMethodField()
    accion_display = serializers.SerializerMethodField()
    
    class Meta:
        model = AuditLog
        fields = [
            'id',
            'timestamp',
            'usuario',
            'usuario_email',
            'usuario_nombre',
            'ip_address',
            'accion',
            'accion_display',
            'modelo',
            'objeto_id',
            'objeto_repr',
            'cliente_id',
            'datos_anteriores',
            'datos_nuevos',
            'endpoint',
            'metodo_http',
        ]
        read_only_fields = fields
    
    def get_usuario_nombre(self, obj):
        """Obtiene el nombre completo del usuario."""
        if obj.usuario:
            return obj.usuario.get_full_name() or obj.usuario.email
        return obj.usuario_email or 'Usuario eliminado'
    
    def get_accion_display(self, obj):
        """Obtiene la acción en formato legible."""
        from apps.core.constants import AccionAudit
        for codigo, nombre in AccionAudit.CHOICES:
            if codigo == obj.accion:
                return nombre
        return obj.accion


class AuditLogListSerializer(serializers.ModelSerializer):
    """
    Serializer resumido para listados de AuditLog.
    
    Excluye datos_anteriores y datos_nuevos para mejor rendimiento.
    """
    
    usuario_nombre = serializers.SerializerMethodField()
    
    class Meta:
        model = AuditLog
        fields = [
            'id',
            'timestamp',
            'usuario_email',
            'usuario_nombre',
            'accion',
            'modelo',
            'objeto_id',
            'objeto_repr',
            'cliente_id',
        ]
        read_only_fields = fields
    
    def get_usuario_nombre(self, obj):
        if obj.usuario:
            return obj.usuario.get_full_name() or obj.usuario.email
        return obj.usuario_email or 'Usuario eliminado'
