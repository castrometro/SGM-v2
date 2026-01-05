"""
Serializers de Asignación para SGM v2.
"""

from rest_framework import serializers
from apps.core.models import AsignacionClienteUsuario, Cliente, Usuario


class UsuarioMiniSerializer(serializers.ModelSerializer):
    """Serializer mínimo de Usuario para asignaciones."""
    
    nombre_completo = serializers.SerializerMethodField()
    
    class Meta:
        model = Usuario
        fields = ['id', 'email', 'nombre', 'apellido', 'nombre_completo', 'tipo_usuario']
    
    def get_nombre_completo(self, obj):
        return obj.get_full_name()


class AsignacionClienteUsuarioSerializer(serializers.ModelSerializer):
    """Serializer de AsignacionClienteUsuario."""
    
    cliente_nombre = serializers.CharField(source='cliente.nombre_display', read_only=True)
    usuario_nombre = serializers.CharField(source='usuario.get_full_name', read_only=True)
    usuario_info = UsuarioMiniSerializer(source='usuario', read_only=True)
    asignado_por_info = UsuarioMiniSerializer(source='asignado_por', read_only=True)
    
    class Meta:
        model = AsignacionClienteUsuario
        fields = [
            'id',
            'cliente',
            'cliente_nombre',
            'usuario',
            'usuario_nombre',
            'usuario_info',
            'es_principal',
            'activa',
            'fecha_asignacion',
            'fecha_desasignacion',
            'asignado_por',
            'asignado_por_info',
            'notas',
        ]
        read_only_fields = ['id', 'fecha_asignacion', 'asignado_por']


class AsignarAnalistaSerializer(serializers.Serializer):
    """Serializer para asignar un analista a un cliente."""
    
    usuario_id = serializers.IntegerField()
    es_principal = serializers.BooleanField(default=False)
    notas = serializers.CharField(required=False, allow_blank=True, default='')
    
    def validate_usuario_id(self, value):
        """Valida que el usuario exista y sea analista."""
        try:
            usuario = Usuario.objects.get(id=value)
        except Usuario.DoesNotExist:
            raise serializers.ValidationError('Usuario no encontrado')
        
        if usuario.tipo_usuario not in ['analista', 'supervisor']:
            raise serializers.ValidationError('El usuario debe ser analista o supervisor')
        
        if not usuario.is_active:
            raise serializers.ValidationError('El usuario no está activo')
        
        return value


class AsignarSupervisorSerializer(serializers.Serializer):
    """Serializer para asignar un supervisor a un cliente."""
    
    supervisor_id = serializers.IntegerField(allow_null=True, required=False)
    
    def validate_supervisor_id(self, value):
        """Valida que el supervisor exista y tenga el rol correcto."""
        if value is None:
            return value
            
        try:
            usuario = Usuario.objects.get(id=value)
        except Usuario.DoesNotExist:
            raise serializers.ValidationError('Supervisor no encontrado')
        
        if usuario.tipo_usuario not in ['supervisor', 'gerente']:
            raise serializers.ValidationError('El usuario debe ser supervisor o gerente')
        
        if not usuario.is_active:
            raise serializers.ValidationError('El supervisor no está activo')
        
        return value


class ClienteConAsignacionesSerializer(serializers.ModelSerializer):
    """Serializer de Cliente con sus asignaciones."""
    
    industria_nombre = serializers.CharField(source='industria.nombre', read_only=True, allow_null=True)
    nombre_display = serializers.CharField(read_only=True)
    supervisor_info = UsuarioMiniSerializer(source='supervisor', read_only=True)
    supervisor_nombre = serializers.SerializerMethodField()
    analistas = serializers.SerializerMethodField()
    total_analistas = serializers.SerializerMethodField()
    
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
            'supervisor',
            'supervisor_info',
            'supervisor_nombre',
            'analistas',
            'total_analistas',
            'activo',
            'fecha_registro',
        ]
    
    def get_supervisor_nombre(self, obj):
        """Retorna el nombre del supervisor o None."""
        if obj.supervisor:
            return obj.supervisor.get_full_name()
        return None
    
    def get_analistas(self, obj):
        """Retorna los analistas asignados al cliente."""
        asignaciones = AsignacionClienteUsuario.objects.filter(
            cliente=obj,
            activa=True
        ).select_related('usuario', 'asignado_por')
        return AsignacionClienteUsuarioSerializer(asignaciones, many=True).data
    
    def get_total_analistas(self, obj):
        """Retorna el número de analistas asignados."""
        return AsignacionClienteUsuario.objects.filter(
            cliente=obj,
            activa=True
        ).count()


class CargaTrabajoSupervisorSerializer(serializers.ModelSerializer):
    """Serializer para mostrar la carga de trabajo de un supervisor."""
    
    nombre_completo = serializers.SerializerMethodField()
    total_clientes = serializers.SerializerMethodField()
    total_analistas = serializers.SerializerMethodField()
    clientes = serializers.SerializerMethodField()
    
    class Meta:
        model = Usuario
        fields = [
            'id',
            'email',
            'nombre',
            'apellido',
            'nombre_completo',
            'total_clientes',
            'total_analistas',
            'clientes',
        ]
    
    def get_nombre_completo(self, obj):
        return obj.get_full_name()
    
    def get_total_clientes(self, obj):
        return Cliente.objects.filter(supervisor=obj, activo=True).count()
    
    def get_total_analistas(self, obj):
        return Usuario.objects.filter(supervisor=obj, is_active=True).count()
    
    def get_clientes(self, obj):
        clientes = Cliente.objects.filter(supervisor=obj, activo=True)
        return [{
            'id': c.id,
            'nombre': c.nombre_display,
            'rut': c.rut,
        } for c in clientes]
