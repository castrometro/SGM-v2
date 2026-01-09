"""
Modelos de Cliente e Industria para SGM v2.
"""

from django.db import models
from ..constants import TipoUsuario


class Industria(models.Model):
    """Catálogo de industrias para clasificar clientes."""
    
    nombre = models.CharField(
        'Nombre',
        max_length=100,
        unique=True
    )
    descripcion = models.TextField(
        'Descripción',
        blank=True
    )
    activa = models.BooleanField(
        'Activa',
        default=True
    )
    
    class Meta:
        verbose_name = 'Industria'
        verbose_name_plural = 'Industrias'
        ordering = ['nombre']
    
    def __str__(self):
        return self.nombre


class Cliente(models.Model):
    """
    Modelo de Cliente.
    Representa a las empresas que contratan servicios de nómina.
    """
    
    # Identificación
    rut = models.CharField(
        'RUT',
        max_length=12,
        unique=True,
        help_text='RUT de la empresa (formato: 12345678-9)'
    )
    razon_social = models.CharField(
        'Razón Social',
        max_length=200,
        help_text='Nombre legal de la empresa'
    )
    nombre_comercial = models.CharField(
        'Nombre Comercial',
        max_length=200,
        blank=True,
        help_text='Nombre con el que se conoce comúnmente'
    )
    
    # Clasificación
    industria = models.ForeignKey(
        Industria,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='clientes',
        verbose_name='Industria'
    )
    
    # Usuario asignado (analista o supervisor)
    # Si es analista, su supervisor hereda acceso automáticamente
    usuario_asignado = models.ForeignKey(
        'Usuario',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='clientes_asignados',
        limit_choices_to={'tipo_usuario__in': TipoUsuario.PUEDEN_SER_ASIGNADOS_CLIENTE},
        verbose_name='Usuario Asignado',
        help_text='Usuario responsable de este cliente (analista o supervisor)'
    )
    
    # Configuración
    bilingue = models.BooleanField(
        'Bilingüe',
        default=False,
        help_text='¿Requiere informes en español e inglés?'
    )
    
    # Contacto
    contacto_nombre = models.CharField(
        'Nombre del Contacto',
        max_length=200,
        blank=True
    )
    contacto_email = models.EmailField(
        'Email del Contacto',
        blank=True
    )
    contacto_telefono = models.CharField(
        'Teléfono del Contacto',
        max_length=20,
        blank=True
    )
    
    # Estado
    activo = models.BooleanField(
        'Activo',
        default=True
    )
    
    # Timestamps
    fecha_registro = models.DateTimeField(
        'Fecha de Registro',
        auto_now_add=True
    )
    fecha_actualizacion = models.DateTimeField(
        'Última Actualización',
        auto_now=True
    )
    
    # Notas
    notas = models.TextField(
        'Notas',
        blank=True,
        help_text='Notas internas sobre el cliente'
    )
    
    class Meta:
        verbose_name = 'Cliente'
        verbose_name_plural = 'Clientes'
        ordering = ['razon_social']
    
    def __str__(self):
        if self.nombre_comercial:
            return f"{self.nombre_comercial} ({self.rut})"
        return f"{self.razon_social} ({self.rut})"
    
    @property
    def nombre_display(self):
        """Retorna el nombre para mostrar (comercial si existe, sino razón social)."""
        return self.nombre_comercial or self.razon_social
    
    def get_servicios_activos(self):
        """Obtiene los servicios activos contratados por el cliente."""
        return self.servicios_contratados.filter(activo=True).select_related('servicio')
    
    def get_supervisor_heredado(self):
        """
        Obtiene el supervisor que hereda acceso al cliente.
        Si usuario_asignado es analista, retorna su supervisor.
        Si usuario_asignado es supervisor, retorna None (no hay herencia).
        """
        if self.usuario_asignado and self.usuario_asignado.tipo_usuario == TipoUsuario.ANALISTA:
            return self.usuario_asignado.supervisor
        return None
    
    def tiene_servicio(self, codigo_servicio):
        """Verifica si el cliente tiene contratado un servicio específico."""
        return self.servicios_contratados.filter(
            servicio__codigo=codigo_servicio,
            activo=True
        ).exists()
