"""
Modelo de Usuario personalizado para SGM v2.
"""

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.core.exceptions import ValidationError


class UsuarioManager(BaseUserManager):
    """Manager personalizado para el modelo Usuario."""
    
    def create_user(self, email, password=None, **extra_fields):
        """Crea y guarda un usuario regular."""
        if not email:
            raise ValueError('El email es obligatorio')
        
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, password=None, **extra_fields):
        """Crea y guarda un superusuario."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('tipo_usuario', 'gerente')
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser debe tener is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser debe tener is_superuser=True.')
        
        return self.create_user(email, password, **extra_fields)


class Usuario(AbstractBaseUser, PermissionsMixin):
    """
    Modelo de Usuario personalizado.
    Usa email como identificador único en lugar de username.
    """
    
    TIPO_USUARIO_CHOICES = [
        ('analista', 'Analista'),
        ('senior', 'Senior'),
        ('supervisor', 'Supervisor'),
        ('gerente', 'Gerente'),
    ]
    
    # Campos de identificación
    email = models.EmailField(
        'Email',
        unique=True,
        help_text='Email corporativo (usado para login)'
    )
    nombre = models.CharField('Nombre', max_length=100)
    apellido = models.CharField('Apellido', max_length=100)
    
    # Campos de rol y organización
    tipo_usuario = models.CharField(
        'Tipo de Usuario',
        max_length=20,
        choices=TIPO_USUARIO_CHOICES,
        default='analista'
    )
    cargo = models.CharField(
        'Cargo',
        max_length=100,
        blank=True,
        help_text='Cargo dentro de la organización'
    )
    
    # Relación supervisor-analista
    supervisor = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='analistas_supervisados',
        help_text='Supervisor asignado a este usuario'
    )
    
    # Campos de estado
    is_active = models.BooleanField('Activo', default=True)
    is_staff = models.BooleanField('Es Staff', default=False)
    
    # Timestamps
    fecha_registro = models.DateTimeField('Fecha de Registro', auto_now_add=True)
    fecha_actualizacion = models.DateTimeField('Última Actualización', auto_now=True)
    
    objects = UsuarioManager()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['nombre', 'apellido']
    
    class Meta:
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'
        ordering = ['apellido', 'nombre']
    
    def __str__(self):
        return f"{self.nombre} {self.apellido}"
    
    def get_full_name(self):
        """Retorna el nombre completo del usuario."""
        return f"{self.nombre} {self.apellido}"
    
    def get_short_name(self):
        """Retorna el nombre corto del usuario."""
        return self.nombre
    
    def clean(self):
        """Validaciones del modelo."""
        super().clean()
        
        # Solo analistas y seniors pueden tener supervisor
        if self.supervisor:
            if self.tipo_usuario not in ['analista', 'senior']:
                raise ValidationError({
                    'supervisor': 'Solo analistas y seniors pueden tener un supervisor asignado.'
                })
            
            # El supervisor debe ser supervisor o gerente
            if self.supervisor.tipo_usuario not in ['supervisor', 'gerente']:
                raise ValidationError({
                    'supervisor': 'El supervisor debe tener rol de supervisor o gerente.'
                })
    
    @property
    def es_supervisor_o_superior(self):
        """Verifica si el usuario es supervisor o tiene rol superior."""
        return self.tipo_usuario in ['supervisor', 'gerente']
    
    @property
    def es_gerente(self):
        """Verifica si el usuario es gerente."""
        return self.tipo_usuario == 'gerente'
    
    def get_clientes_asignados(self):
        """Obtiene los clientes asignados a este usuario."""
        return [asig.cliente for asig in self.asignaciones.select_related('cliente').all()]
    
    def get_clientes_supervisados(self):
        """
        Para supervisores: obtiene los clientes de sus analistas supervisados.
        """
        if not self.es_supervisor_o_superior:
            return []
        
        from .asignacion import AsignacionClienteUsuario
        analistas_ids = self.analistas_supervisados.values_list('id', flat=True)
        return [
            asig.cliente 
            for asig in AsignacionClienteUsuario.objects
                .filter(usuario_id__in=analistas_ids)
                .select_related('cliente')
        ]
