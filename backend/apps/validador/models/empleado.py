"""
Modelos de Empleado y sus registros para el Validador de Nómina.
Datos extraídos del Libro de Remuneraciones.
"""

from django.db import models


class EmpleadoCierre(models.Model):
    """
    Empleado dentro de un cierre específico.
    Representa a una persona en el Libro de Remuneraciones de ese período.
    """
    
    cierre = models.ForeignKey(
        'Cierre',
        on_delete=models.CASCADE,
        related_name='empleados'
    )
    
    # Identificación
    rut = models.CharField(max_length=12)
    nombre = models.CharField(max_length=200)
    
    # Información adicional del libro
    cargo = models.CharField(max_length=200, blank=True)
    centro_costo = models.CharField(max_length=100, blank=True)
    fecha_ingreso = models.DateField(null=True, blank=True)
    
    # Totales calculados
    total_haberes = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0
    )
    total_descuentos = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0
    )
    liquido = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0
    )
    
    class Meta:
        verbose_name = 'Empleado de Cierre'
        verbose_name_plural = 'Empleados de Cierre'
        unique_together = ['cierre', 'rut']
        ordering = ['nombre']
        indexes = [
            models.Index(fields=['cierre', 'rut']),
        ]
    
    def __str__(self):
        return f"{self.rut} - {self.nombre}"


class RegistroConcepto(models.Model):
    """
    Registro individual de un concepto para un empleado.
    Representa una celda del Libro de Remuneraciones (empleado x concepto = monto).
    """
    
    empleado = models.ForeignKey(
        EmpleadoCierre,
        on_delete=models.CASCADE,
        related_name='registros'
    )
    
    concepto = models.ForeignKey(
        'ConceptoCliente',
        on_delete=models.CASCADE,
        related_name='registros'
    )
    
    # Monto del ERP
    monto = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0
    )
    
    # Monto original (antes de aplicar multiplicador si existe)
    monto_original = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0
    )
    
    class Meta:
        verbose_name = 'Registro de Concepto'
        verbose_name_plural = 'Registros de Conceptos'
        unique_together = ['empleado', 'concepto']
        indexes = [
            models.Index(fields=['empleado', 'concepto']),
        ]
    
    def __str__(self):
        return f"{self.empleado.rut} - {self.concepto.nombre_erp}: ${self.monto}"


class RegistroNovedades(models.Model):
    """
    Registro de novedades del cliente para un empleado.
    Se usa para comparar contra RegistroConcepto.
    """
    
    cierre = models.ForeignKey(
        'Cierre',
        on_delete=models.CASCADE,
        related_name='registros_novedades'
    )
    
    # RUT del empleado (puede no existir en el libro)
    rut_empleado = models.CharField(max_length=12)
    nombre_empleado = models.CharField(max_length=200, blank=True)
    
    # Item de novedades (nombre original del cliente)
    nombre_item = models.CharField(max_length=200)
    
    # Mapeo al concepto del ERP (puede ser null si no está mapeado)
    mapeo = models.ForeignKey(
        'MapeoItemNovedades',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='registros'
    )
    
    # Monto informado por el cliente
    monto = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0
    )
    
    class Meta:
        verbose_name = 'Registro de Novedades'
        verbose_name_plural = 'Registros de Novedades'
        indexes = [
            models.Index(fields=['cierre', 'rut_empleado']),
            models.Index(fields=['cierre', 'nombre_item']),
        ]
    
    def __str__(self):
        return f"{self.rut_empleado} - {self.nombre_item}: ${self.monto}"
