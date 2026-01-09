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


class UsuarioAsignadoSerializer(serializers.Serializer):
    """Serializer mínimo para mostrar usuario asignado."""
    id = serializers.IntegerField()
    nombre = serializers.CharField(source='get_full_name')
    email = serializers.EmailField()
    tipo_usuario = serializers.CharField()


class ClienteSerializer(serializers.ModelSerializer):
    """Serializer básico de Cliente."""
    
    industria_nombre = serializers.CharField(source='industria.nombre', read_only=True, allow_null=True)
    nombre_display = serializers.CharField(read_only=True)
    usuario_asignado_info = serializers.SerializerMethodField()
    supervisor_heredado_info = serializers.SerializerMethodField()
    erp_activo = serializers.SerializerMethodField()
    
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
            'usuario_asignado',
            'usuario_asignado_info',
            'supervisor_heredado_info',
            'erp_activo',
            'bilingue',
            'activo',
            'fecha_registro',
        ]
        read_only_fields = ['id', 'fecha_registro']
    
    def get_usuario_asignado_info(self, obj):
        """Retorna información del usuario asignado."""
        if obj.usuario_asignado:
            return {
                'id': obj.usuario_asignado.id,
                'nombre': obj.usuario_asignado.get_full_name(),
                'email': obj.usuario_asignado.email,
                'tipo_usuario': obj.usuario_asignado.tipo_usuario,
            }
        return None
    
    def get_supervisor_heredado_info(self, obj):
        """Retorna información del supervisor que hereda acceso."""
        supervisor = obj.get_supervisor_heredado()
        if supervisor:
            return {
                'id': supervisor.id,
                'nombre': supervisor.get_full_name(),
                'email': supervisor.email,
            }
        return None
    
    def get_erp_activo(self, obj):
        """Retorna información del ERP activo del cliente."""
        # Usar la caché del prefetch_related si existe
        configs = getattr(obj, '_prefetched_objects_cache', {}).get('configuraciones_erp')
        if configs is not None:
            # Filtrar en memoria (ya está prefetched)
            config = next((c for c in configs if c.activo), None)
        else:
            # Fallback: hacer query
            config = obj.configuraciones_erp.filter(activo=True).first()
        
        if config:
            return {
                'id': config.erp.id,
                'nombre': config.erp.nombre,
                'slug': config.erp.slug,
            }
        return None


class ClienteDetailSerializer(serializers.ModelSerializer):
    """Serializer detallado de Cliente."""
    
    industria = IndustriaSerializer(read_only=True)
    nombre_display = serializers.CharField(read_only=True)
    servicios_activos = serializers.SerializerMethodField()
    usuario_asignado_info = serializers.SerializerMethodField()
    supervisor_heredado_info = serializers.SerializerMethodField()
    erp_activo = serializers.SerializerMethodField()
    
    class Meta:
        model = Cliente
        fields = [
            'id',
            'rut',
            'razon_social',
            'nombre_comercial',
            'nombre_display',
            'industria',
            'usuario_asignado',
            'usuario_asignado_info',
            'supervisor_heredado_info',
            'erp_activo',
            'bilingue',
            'contacto_nombre',
            'contacto_email',
            'contacto_telefono',
            'activo',
            'notas',
            'fecha_registro',
            'fecha_actualizacion',
            'servicios_activos',
        ]
    
    def get_servicios_activos(self, obj):
        """Retorna los servicios activos del cliente."""
        from .servicio import ServicioClienteSerializer
        servicios = obj.get_servicios_activos()
        return ServicioClienteSerializer(servicios, many=True).data
    
    def get_usuario_asignado_info(self, obj):
        """Retorna información del usuario asignado."""
        if obj.usuario_asignado:
            return {
                'id': obj.usuario_asignado.id,
                'nombre': obj.usuario_asignado.get_full_name(),
                'email': obj.usuario_asignado.email,
                'tipo_usuario': obj.usuario_asignado.tipo_usuario,
            }
        return None
    
    def get_supervisor_heredado_info(self, obj):
        """Retorna información del supervisor que hereda acceso."""
        supervisor = obj.get_supervisor_heredado()
        if supervisor:
            return {
                'id': supervisor.id,
                'nombre': supervisor.get_full_name(),
                'email': supervisor.email,
            }
        return None
    
    def get_erp_activo(self, obj):
        """Retorna información del ERP activo del cliente."""
        # Usar la caché del prefetch_related si existe
        configs = getattr(obj, '_prefetched_objects_cache', {}).get('configuraciones_erp')
        if configs is not None:
            # Filtrar en memoria (ya está prefetched)
            config = next((c for c in configs if c.activo), None)
        else:
            # Fallback: hacer query
            config = obj.configuraciones_erp.filter(activo=True).first()
        
        if config:
            return {
                'id': config.erp.id,
                'nombre': config.erp.nombre,
                'slug': config.erp.slug,
            }
        return None


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
