"""
Modelo de Asignación Cliente-Usuario para SGM v2.
"""

from django.db import models


class AsignacionClienteUsuario(models.Model):
    """
    Asignación de un cliente a un usuario (analista).
    Define qué analistas trabajan con qué clientes.
    """
    
    cliente = models.ForeignKey(
        'Cliente',
        on_delete=models.CASCADE,
        related_name='asignaciones',
        verbose_name='Cliente'
    )
    usuario = models.ForeignKey(
        'Usuario',
        on_delete=models.CASCADE,
        related_name='asignaciones',
        verbose_name='Usuario'
    )
    
    # Usuario que hizo la asignación
    asignado_por = models.ForeignKey(
        'Usuario',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='asignaciones_realizadas',
        verbose_name='Asignado por'
    )
    
    # Rol en la asignación
    es_principal = models.BooleanField(
        'Es Principal',
        default=True,
        help_text='Indica si es el analista principal del cliente'
    )
    
    # Estado
    activa = models.BooleanField(
        'Activa',
        default=True
    )
    
    # Timestamps
    fecha_asignacion = models.DateTimeField(
        'Fecha de Asignación',
        auto_now_add=True
    )
    fecha_desasignacion = models.DateTimeField(
        'Fecha de Desasignación',
        null=True,
        blank=True
    )
    
    # Notas
    notas = models.TextField(
        'Notas',
        blank=True
    )
    
    class Meta:
        verbose_name = 'Asignación Cliente-Usuario'
        verbose_name_plural = 'Asignaciones Cliente-Usuario'
        unique_together = ['cliente', 'usuario']
        ordering = ['cliente', 'usuario']
    
    def __str__(self):
        return f"{self.usuario.get_full_name()} → {self.cliente.nombre_display}"
    
    @classmethod
    def get_clientes_por_usuario(cls, usuario):
        """Obtiene todos los clientes asignados a un usuario."""
        return cls.objects.filter(
            usuario=usuario,
            activa=True
        ).select_related('cliente')
    
    @classmethod
    def get_usuarios_por_cliente(cls, cliente):
        """Obtiene todos los usuarios asignados a un cliente."""
        return cls.objects.filter(
            cliente=cliente,
            activa=True
        ).select_related('usuario')
    
    @classmethod
    def get_analista_principal(cls, cliente):
        """Obtiene el analista principal de un cliente."""
        asignacion = cls.objects.filter(
            cliente=cliente,
            activa=True,
            es_principal=True
        ).select_related('usuario').first()
        
        return asignacion.usuario if asignacion else None
