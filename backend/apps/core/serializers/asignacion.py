"""
Serializers de Asignación para SGM v2.
"""

from rest_framework import serializers
from apps.core.models import AsignacionClienteUsuario


class AsignacionClienteUsuarioSerializer(serializers.ModelSerializer):
    """Serializer de AsignacionClienteUsuario."""
    
    cliente_nombre = serializers.CharField(source='cliente.nombre_display', read_only=True)
    usuario_nombre = serializers.CharField(source='usuario.get_full_name', read_only=True)
    
    class Meta:
        model = AsignacionClienteUsuario
        fields = [
            'id',
            'cliente',
            'cliente_nombre',
            'usuario',
            'usuario_nombre',
            'es_principal',
            'activa',
            'fecha_asignacion',
            'notas',
        ]
        read_only_fields = ['id', 'fecha_asignacion']
