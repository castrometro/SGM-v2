"""
Serializers de Cliente para SGM v2.
"""

from rest_framework import serializers
from apps.core.models import Cliente, Industria


class IndustriaSerializer(serializers.ModelSerializer):
    """Serializer de Industria."""
    
    class Meta:
        model = Industria
        fields = ['id', 'nombre', 'descripcion', 'activa']


class ClienteSerializer(serializers.ModelSerializer):
    """Serializer básico de Cliente."""
    
    industria_nombre = serializers.CharField(source='industria.nombre', read_only=True, allow_null=True)
    nombre_display = serializers.CharField(read_only=True)
    
    class Meta:
        model = Cliente
        fields = [
            'id',
            'rut',
            'razon_social',
            'nombre_comercial',
            'nombre_display',
            'industria',
            'industria_nombre',
            'bilingue',
            'activo',
            'fecha_registro',
        ]
        read_only_fields = ['id', 'fecha_registro']


class ClienteDetailSerializer(serializers.ModelSerializer):
    """Serializer detallado de Cliente."""
    
    industria = IndustriaSerializer(read_only=True)
    nombre_display = serializers.CharField(read_only=True)
    servicios_activos = serializers.SerializerMethodField()
    analistas_asignados = serializers.SerializerMethodField()
    
    class Meta:
        model = Cliente
        fields = [
            'id',
            'rut',
            'razon_social',
            'nombre_comercial',
            'nombre_display',
            'industria',
            'bilingue',
            'contacto_nombre',
            'contacto_email',
            'contacto_telefono',
            'activo',
            'notas',
            'fecha_registro',
            'fecha_actualizacion',
            'servicios_activos',
            'analistas_asignados',
        ]
    
    def get_servicios_activos(self, obj):
        """Retorna los servicios activos del cliente."""
        from .servicio import ServicioClienteSerializer
        servicios = obj.get_servicios_activos()
        return ServicioClienteSerializer(servicios, many=True).data
    
    def get_analistas_asignados(self, obj):
        """Retorna los analistas asignados al cliente."""
        from .usuario import UsuarioSerializer
        analistas = obj.get_analistas_asignados()
        return UsuarioSerializer(analistas, many=True).data


class ClienteCreateSerializer(serializers.ModelSerializer):
    """Serializer para crear/actualizar Cliente."""
    
    class Meta:
        model = Cliente
        fields = [
            'rut',
            'razon_social',
            'nombre_comercial',
            'industria',
            'bilingue',
            'contacto_nombre',
            'contacto_email',
            'contacto_telefono',
            'activo',
            'notas',
        ]
    
    def validate_rut(self, value):
        """Valida el formato del RUT."""
        # Limpiar el RUT (quitar puntos y espacios)
        rut = value.replace('.', '').replace(' ', '').upper()
        
        # Validar formato básico (8-9 dígitos + guion + dígito verificador)
        import re
        if not re.match(r'^\d{7,8}-[\dK]$', rut):
            raise serializers.ValidationError(
                'Formato de RUT inválido. Use el formato: 12345678-9'
            )
        
        return rut
