"""
Serializers de Usuario para SGM v2.
"""

from rest_framework import serializers
from apps.core.models import Usuario
from apps.core.constants import TipoUsuario, Permisos


class UsuarioSerializer(serializers.ModelSerializer):
    """Serializer básico de Usuario."""
    
    nombre_completo = serializers.CharField(source='get_full_name', read_only=True)
    supervisor_nombre = serializers.CharField(
        source='supervisor.get_full_name', 
        read_only=True,
        allow_null=True
    )
    
    class Meta:
        model = Usuario
        fields = [
            'id',
            'email',
            'nombre',
            'apellido',
            'nombre_completo',
            'tipo_usuario',
            'cargo',
            'supervisor',
            'supervisor_nombre',
            'is_active',
            'fecha_registro',
        ]
        read_only_fields = ['id', 'fecha_registro']


class UsuarioCreateSerializer(serializers.ModelSerializer):
    """Serializer para crear usuarios."""
    
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)
    
    class Meta:
        model = Usuario
        fields = [
            'email',
            'nombre',
            'apellido',
            'tipo_usuario',
            'cargo',
            'supervisor',
            'password',
            'password_confirm',
        ]
    
    def validate(self, attrs):
        if attrs['password'] != attrs.pop('password_confirm'):
            raise serializers.ValidationError({
                'password_confirm': 'Las contraseñas no coinciden.'
            })
        return attrs
    
    def create(self, validated_data):
        password = validated_data.pop('password')
        usuario = Usuario(**validated_data)
        usuario.set_password(password)
        usuario.save()
        return usuario


class UsuarioMeSerializer(serializers.ModelSerializer):
    """Serializer para el usuario actual (me)."""
    
    nombre_completo = serializers.CharField(source='get_full_name', read_only=True)
    permisos = serializers.SerializerMethodField()
    clientes_asignados = serializers.SerializerMethodField()
    
    class Meta:
        model = Usuario
        fields = [
            'id',
            'email',
            'nombre',
            'apellido',
            'nombre_completo',
            'tipo_usuario',
            'cargo',
            'is_active',
            'permisos',
            'clientes_asignados',
        ]
    
    def get_permisos(self, obj):
        """
        Retorna los permisos del usuario basados en su rol.
        El frontend consume estos permisos desde usePermissions.js
        """
        tipo = obj.tipo_usuario
        return {
            # Permisos de cierre
            Permisos.CAN_CREATE_CIERRE: True,
            Permisos.CAN_VIEW_ALL_CIERRES: tipo in TipoUsuario.PUEDEN_SUPERVISAR,
            Permisos.CAN_APPROVE_CIERRE: tipo in TipoUsuario.PUEDEN_APROBAR,
            
            # Permisos de archivos
            Permisos.CAN_UPLOAD_FILES: True,
            Permisos.CAN_CLASSIFY_CONCEPTS: True,
            Permisos.CAN_MAP_NOVEDADES: True,
            
            # Permisos de incidencias
            Permisos.CAN_RESPOND_INCIDENCIA: True,
            Permisos.CAN_APPROVE_INCIDENCIA: tipo in TipoUsuario.PUEDEN_APROBAR,
            Permisos.CAN_VIEW_ALL_INCIDENCIAS: tipo in TipoUsuario.PUEDEN_SUPERVISAR,
            
            # Permisos de equipo
            Permisos.CAN_VIEW_TEAM: tipo in TipoUsuario.PUEDEN_SUPERVISAR,
            
            # Permisos de administración
            Permisos.CAN_MANAGE_USERS: tipo in TipoUsuario.PUEDEN_ADMINISTRAR,
            Permisos.CAN_MANAGE_CLIENTS: tipo in TipoUsuario.PUEDEN_ADMINISTRAR,
            Permisos.CAN_MANAGE_SERVICES: tipo in TipoUsuario.PUEDEN_ADMINISTRAR,
            
            # Permisos de reportes
            Permisos.CAN_VIEW_EXECUTIVE_DASHBOARD: tipo in TipoUsuario.PUEDEN_ADMINISTRAR,
            Permisos.CAN_VIEW_ALL_REPORTS: tipo in TipoUsuario.PUEDEN_ADMINISTRAR,
            Permisos.CAN_VIEW_GLOBAL_REPORTS: tipo in TipoUsuario.PUEDEN_SUPERVISAR,
        }
    
    def get_clientes_asignados(self, obj):
        """Retorna los IDs de clientes asignados al usuario."""
        if obj.tipo_usuario == TipoUsuario.GERENTE:
            return []  # Gerentes ven todos
        
        from apps.core.models import Cliente
        from django.db.models import Q
        
        if obj.tipo_usuario == TipoUsuario.SUPERVISOR:
            # Clientes asignados directamente + clientes de analistas supervisados
            return list(Cliente.objects.filter(
                Q(usuario_asignado=obj) | Q(usuario_asignado__supervisor=obj)
            ).values_list('id', flat=True).distinct())
        
        # Analistas: solo sus clientes directos
        return list(Cliente.objects.filter(usuario_asignado=obj).values_list('id', flat=True))


class UsuarioUpdateSerializer(serializers.ModelSerializer):
    """Serializer para actualizar usuarios (sin password)."""
    
    class Meta:
        model = Usuario
        fields = [
            'email',
            'nombre',
            'apellido',
            'tipo_usuario',
            'cargo',
            'supervisor',
            'is_active',
        ]
    
    def validate_supervisor(self, value):
        """Valida que el supervisor sea válido."""
        if value and value.tipo_usuario not in TipoUsuario.PUEDEN_SER_SUPERVISORES:
            raise serializers.ValidationError(
                'El supervisor debe tener rol de Supervisor o Gerente.'
            )
        return value


class ResetPasswordSerializer(serializers.Serializer):
    """Serializer para resetear contraseña."""
    
    new_password = serializers.CharField(write_only=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True)
    
    def validate(self, attrs):
        if attrs['new_password'] != attrs['confirm_password']:
            raise serializers.ValidationError({
                'confirm_password': 'Las contraseñas no coinciden.'
            })
        return attrs


class ChangePasswordSerializer(serializers.Serializer):
    """Serializer para que el usuario cambie su propia contraseña."""
    
    current_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True)
    
    def validate(self, attrs):
        if attrs['new_password'] != attrs['confirm_password']:
            raise serializers.ValidationError({
                'confirm_password': 'Las contraseñas no coinciden.'
            })
        return attrs

