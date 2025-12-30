"""
Modelos de Servicio para SGM v2.
"""

from django.db import models


class Servicio(models.Model):
    """
    Catálogo de servicios disponibles.
    Ejemplo: Validación de Nómina, Reportería Mensual, etc.
    """
    
    codigo = models.CharField(
        'Código',
        max_length=20,
        unique=True,
        help_text='Código único del servicio (ej: VAL_NOMINA)'
    )
    nombre = models.CharField(
        'Nombre',
        max_length=100
    )
    descripcion = models.TextField(
        'Descripción',
        blank=True
    )
    activo = models.BooleanField(
        'Activo',
        default=True
    )
    
    class Meta:
        verbose_name = 'Servicio'
        verbose_name_plural = 'Servicios'
        ordering = ['nombre']
    
    def __str__(self):
        return self.nombre


class ServicioCliente(models.Model):
    """
    Relación entre Cliente y Servicio contratado.
    Permite configuración específica por cliente.
    """
    
    cliente = models.ForeignKey(
        'Cliente',
        on_delete=models.CASCADE,
        related_name='servicios_contratados',
        verbose_name='Cliente'
    )
    servicio = models.ForeignKey(
        Servicio,
        on_delete=models.CASCADE,
        related_name='clientes_contratantes',
        verbose_name='Servicio'
    )
    
    # Configuración del servicio para este cliente
    activo = models.BooleanField(
        'Activo',
        default=True
    )
    fecha_inicio = models.DateField(
        'Fecha de Inicio',
        null=True,
        blank=True
    )
    fecha_fin = models.DateField(
        'Fecha de Fin',
        null=True,
        blank=True,
        help_text='Dejar vacío si es indefinido'
    )
    
    # Configuración específica (JSON flexible)
    configuracion = models.JSONField(
        'Configuración',
        default=dict,
        blank=True,
        help_text='Configuración específica del servicio para este cliente'
    )
    
    # Notas
    notas = models.TextField(
        'Notas',
        blank=True
    )
    
    # Timestamps
    fecha_registro = models.DateTimeField(
        'Fecha de Registro',
        auto_now_add=True
    )
    
    class Meta:
        verbose_name = 'Servicio Contratado'
        verbose_name_plural = 'Servicios Contratados'
        unique_together = ['cliente', 'servicio']
        ordering = ['cliente', 'servicio']
    
    def __str__(self):
        return f"{self.cliente.nombre_display} - {self.servicio.nombre}"
    
    @property
    def esta_vigente(self):
        """Verifica si el servicio está vigente (activo y dentro del rango de fechas)."""
        from django.utils import timezone
        
        if not self.activo:
            return False
        
        hoy = timezone.now().date()
        
        if self.fecha_inicio and hoy < self.fecha_inicio:
            return False
        
        if self.fecha_fin and hoy > self.fecha_fin:
            return False
        
        return True
