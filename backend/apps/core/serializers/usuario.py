"""
Serializers de Usuario para SGM v2.
"""

from rest_framework import serializers
from apps.core.models import Usuario


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
        """Retorna los permisos del usuario basados en su rol."""
        permisos = {
            'puede_crear_cierre': True,
            'puede_aprobar_cierre': obj.tipo_usuario in ['supervisor', 'gerente'],
            'puede_ver_todos_clientes': obj.tipo_usuario == 'gerente',
            'puede_gestionar_usuarios': obj.tipo_usuario == 'gerente',
            'puede_ver_reportes_globales': obj.tipo_usuario in ['supervisor', 'gerente'],
        }
        return permisos
    
    def get_clientes_asignados(self, obj):
        """Retorna los IDs de clientes asignados al usuario."""
        if obj.tipo_usuario == 'gerente':
            return []  # Gerentes ven todos
        
        from apps.core.models import AsignacionClienteUsuario
        
        if obj.tipo_usuario == 'supervisor':
            # Obtener clientes de analistas supervisados
            analistas_ids = obj.analistas_supervisados.values_list('id', flat=True)
            return list(AsignacionClienteUsuario.objects.filter(
                usuario_id__in=analistas_ids,
                activa=True
            ).values_list('cliente_id', flat=True).distinct())
        
        # Analistas y seniors: sus clientes directos
        return list(obj.asignaciones.filter(activa=True).values_list('cliente_id', flat=True))


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
        if value and value.tipo_usuario not in ['supervisor', 'gerente']:
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

