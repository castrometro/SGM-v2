"""
Modelos de Movimientos del Mes para el Validador de Nómina.
Maneja altas, bajas, licencias, vacaciones, etc.
"""

from django.db import models


class MovimientoMes(models.Model):
    """
    Registro de movimiento del mes (del archivo ERP).
    Puede ser: Alta, Baja, Licencia, Vacaciones, etc.
    """
    
    TIPO_CHOICES = [
        ('alta', 'Alta/Ingreso'),
        ('baja', 'Baja/Finiquito'),
        ('licencia', 'Licencia Médica'),
        ('vacaciones', 'Vacaciones'),
        ('permiso', 'Permiso'),
        ('ausencia', 'Ausencia'),
        ('otro', 'Otro'),
    ]
    
    cierre = models.ForeignKey(
        'Cierre',
        on_delete=models.CASCADE,
        related_name='movimientos_erp'
    )
    
    tipo = models.CharField(
        max_length=20,
        choices=TIPO_CHOICES
    )
    
    # Datos del empleado
    rut = models.CharField(max_length=12)
    nombre = models.CharField(max_length=200, blank=True)
    
    # Fechas del movimiento
    fecha_inicio = models.DateField(null=True, blank=True)
    fecha_fin = models.DateField(null=True, blank=True)
    
    # Días (para licencias/vacaciones)
    dias = models.PositiveIntegerField(null=True, blank=True)
    
    # Información adicional según tipo
    # Para bajas: causal
    causal = models.CharField(max_length=200, blank=True)
    # Para licencias: tipo de licencia
    tipo_licencia = models.CharField(max_length=100, blank=True)
    
    # Datos crudos del Excel
    datos_raw = models.JSONField(default=dict, blank=True)
    
    # De qué hoja del Excel vino
    hoja_origen = models.CharField(max_length=100, blank=True)
    
    class Meta:
        verbose_name = 'Movimiento del Mes (ERP)'
        verbose_name_plural = 'Movimientos del Mes (ERP)'
        ordering = ['tipo', 'rut']
        indexes = [
            models.Index(fields=['cierre', 'tipo']),
            models.Index(fields=['cierre', 'rut']),
        ]
    
    def __str__(self):
        return f"{self.get_tipo_display()} - {self.rut} ({self.nombre})"


class MovimientoAnalista(models.Model):
    """
    Registro de movimiento informado por el cliente (archivos del analista).
    Se compara contra MovimientoMes para detectar discrepancias.
    """
    
    TIPO_CHOICES = MovimientoMes.TIPO_CHOICES
    
    ORIGEN_CHOICES = [
        ('asistencias', 'Archivo Asistencias'),
        ('finiquitos', 'Archivo Finiquitos'),
        ('ingresos', 'Archivo Ingresos'),
    ]
    
    cierre = models.ForeignKey(
        'Cierre',
        on_delete=models.CASCADE,
        related_name='movimientos_analista'
    )
    
    tipo = models.CharField(
        max_length=20,
        choices=TIPO_CHOICES
    )
    
    # De qué archivo viene
    origen = models.CharField(
        max_length=20,
        choices=ORIGEN_CHOICES
    )
    
    # Datos del empleado
    rut = models.CharField(max_length=12)
    nombre = models.CharField(max_length=200, blank=True)
    
    # Fechas
    fecha_inicio = models.DateField(null=True, blank=True)
    fecha_fin = models.DateField(null=True, blank=True)
    dias = models.PositiveIntegerField(null=True, blank=True)
    
    # Información adicional
    causal = models.CharField(max_length=200, blank=True)
    
    # Datos crudos
    datos_raw = models.JSONField(default=dict, blank=True)
    
    class Meta:
        verbose_name = 'Movimiento Analista'
        verbose_name_plural = 'Movimientos Analista'
        ordering = ['tipo', 'rut']
        indexes = [
            models.Index(fields=['cierre', 'tipo']),
            models.Index(fields=['cierre', 'rut']),
        ]
    
    def __str__(self):
        return f"{self.get_tipo_display()} - {self.rut} ({self.origen})"
