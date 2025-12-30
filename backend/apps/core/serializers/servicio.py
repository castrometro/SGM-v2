"""
Serializers de Servicio para SGM v2.
"""

from rest_framework import serializers
from apps.core.models import Servicio, ServicioCliente


class ServicioSerializer(serializers.ModelSerializer):
    """Serializer de Servicio."""
    
    class Meta:
        model = Servicio
        fields = ['id', 'codigo', 'nombre', 'descripcion', 'activo']


class ServicioClienteSerializer(serializers.ModelSerializer):
    """Serializer de ServicioCliente."""
    
    servicio = ServicioSerializer(read_only=True)
    servicio_id = serializers.PrimaryKeyRelatedField(
        queryset=Servicio.objects.all(),
        source='servicio',
        write_only=True
    )
    esta_vigente = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = ServicioCliente
        fields = [
            'id',
            'cliente',
            'servicio',
            'servicio_id',
            'activo',
            'fecha_inicio',
            'fecha_fin',
            'configuracion',
            'notas',
            'esta_vigente',
            'fecha_registro',
        ]
        read_only_fields = ['id', 'fecha_registro']
