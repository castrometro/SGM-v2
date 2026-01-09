"""
Serializers de ERP para SGM v2.
"""

from rest_framework import serializers
from apps.core.models import ERP, ConfiguracionERPCliente


class ERPSerializer(serializers.ModelSerializer):
    """Serializer básico de ERP para listados."""
    
    formatos_display = serializers.CharField(read_only=True)
    
    class Meta:
        model = ERP
        fields = [
            'id',
            'slug',
            'nombre',
            'descripcion',
            'activo',
            'requiere_api',
            'formatos_soportados',
            'formatos_display',
        ]


class ERPDetailSerializer(serializers.ModelSerializer):
    """Serializer detallado de ERP."""
    
    formatos_display = serializers.CharField(read_only=True)
    clientes_count = serializers.SerializerMethodField()
    
    class Meta:
        model = ERP
        fields = [
            'id',
            'slug',
            'nombre',
            'descripcion',
            'activo',
            'requiere_api',
            'formatos_soportados',
            'formatos_display',
            'schema_credenciales',
            'configuracion_parseo',
            'clientes_count',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_clientes_count(self, obj):
        """Cuenta clientes que usan este ERP."""
        return obj.configuraciones.filter(activo=True).count()


class ERPCreateSerializer(serializers.ModelSerializer):
    """Serializer para crear/actualizar ERP."""
    
    class Meta:
        model = ERP
        fields = [
            'slug',
            'nombre',
            'descripcion',
            'activo',
            'requiere_api',
            'formatos_soportados',
            'schema_credenciales',
            'configuracion_parseo',
        ]
    
    def validate_formatos_soportados(self, value):
        """Valida que sea una lista de strings."""
        if value:
            if not isinstance(value, list):
                raise serializers.ValidationError('Debe ser una lista de extensiones')
            for formato in value:
                if not isinstance(formato, str):
                    raise serializers.ValidationError('Cada formato debe ser un string')
        return value


class ConfiguracionERPClienteSerializer(serializers.ModelSerializer):
    """Serializer básico de ConfiguracionERPCliente."""
    
    erp_nombre = serializers.CharField(source='erp.nombre', read_only=True)
    erp_slug = serializers.CharField(source='erp.slug', read_only=True)
    cliente_nombre = serializers.CharField(source='cliente.nombre_display', read_only=True)
    esta_vigente = serializers.BooleanField(read_only=True)
    dias_para_expirar = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = ConfiguracionERPCliente
        fields = [
            'id',
            'cliente',
            'cliente_nombre',
            'erp',
            'erp_nombre',
            'erp_slug',
            'fecha_activacion',
            'fecha_expiracion',
            'activo',
            'esta_vigente',
            'dias_para_expirar',
            'notas',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class ConfiguracionERPClienteDetailSerializer(serializers.ModelSerializer):
    """Serializer detallado con información del ERP."""
    
    erp = ERPSerializer(read_only=True)
    cliente_nombre = serializers.CharField(source='cliente.nombre_display', read_only=True)
    cliente_rut = serializers.CharField(source='cliente.rut', read_only=True)
    esta_vigente = serializers.BooleanField(read_only=True)
    dias_para_expirar = serializers.IntegerField(read_only=True)
    # Nota: credenciales se excluyen del serializer por seguridad
    tiene_credenciales = serializers.SerializerMethodField()
    
    class Meta:
        model = ConfiguracionERPCliente
        fields = [
            'id',
            'cliente',
            'cliente_nombre',
            'cliente_rut',
            'erp',
            'fecha_activacion',
            'fecha_expiracion',
            'activo',
            'esta_vigente',
            'dias_para_expirar',
            'tiene_credenciales',
            'notas',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_tiene_credenciales(self, obj):
        """Indica si hay credenciales configuradas sin exponerlas."""
        return bool(obj.credenciales)


class ConfiguracionERPClienteCreateSerializer(serializers.ModelSerializer):
    """Serializer para crear/actualizar configuración ERP de cliente."""
    
    class Meta:
        model = ConfiguracionERPCliente
        fields = [
            'cliente',
            'erp',
            'credenciales',
            'fecha_activacion',
            'fecha_expiracion',
            'activo',
            'notas',
        ]
    
    def validate(self, data):
        """Validaciones adicionales."""
        fecha_activacion = data.get('fecha_activacion')
        fecha_expiracion = data.get('fecha_expiracion')
        
        if fecha_activacion and fecha_expiracion:
            if fecha_expiracion < fecha_activacion:
                raise serializers.ValidationError({
                    'fecha_expiracion': 'Debe ser posterior a la fecha de activación'
                })
        
        return data


class ConfiguracionERPClienteMinimalSerializer(serializers.ModelSerializer):
    """Serializer mínimo para incluir en otros serializers (ej: ClienteDetailSerializer)."""
    
    erp_nombre = serializers.CharField(source='erp.nombre', read_only=True)
    erp_slug = serializers.CharField(source='erp.slug', read_only=True)
    esta_vigente = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = ConfiguracionERPCliente
        fields = [
            'id',
            'erp',
            'erp_nombre',
            'erp_slug',
            'fecha_activacion',
            'fecha_expiracion',
            'activo',
            'esta_vigente',
        ]
