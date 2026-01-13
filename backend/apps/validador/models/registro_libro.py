"""
Modelo RegistroLibro para almacenar datos individuales de conceptos del Libro de Remuneraciones.

Este modelo almacena un registro por cada concepto-valor de cada empleado,
permitiendo comparación directa con RegistroNovedades mediante JOINs SQL.

Arquitectura Medallion - Capa Bronce (datos crudos).
"""

from django.db import models
from decimal import Decimal


class RegistroLibro(models.Model):
    """
    Registro individual de concepto del Libro de Remuneraciones.
    
    Un registro por cada concepto con monto > 0 de cada empleado.
    Estructura espejo de RegistroNovedades para facilitar comparación.
    
    Categorías que se guardan:
    - haberes_imponibles
    - haberes_no_imponibles
    - descuentos_legales
    - otros_descuentos
    - aportes_patronales
    
    NO se guardan:
    - info_adicional (datos del empleado, no montos)
    - ignorar (excluidos de validación)
    """
    
    cierre = models.ForeignKey(
        'Cierre',
        on_delete=models.CASCADE,
        related_name='registros_libro',
        help_text='Cierre al que pertenece este registro'
    )
    
    empleado = models.ForeignKey(
        'EmpleadoLibro',
        on_delete=models.CASCADE,
        related_name='registros',
        help_text='Empleado al que pertenece este registro'
    )
    
    concepto = models.ForeignKey(
        'ConceptoLibro',
        on_delete=models.PROTECT,
        related_name='registros',
        help_text='Concepto clasificado del libro'
    )
    
    monto = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text='Monto del concepto para este empleado'
    )
    
    class Meta:
        verbose_name = 'Registro Libro'
        verbose_name_plural = 'Registros Libro'
        ordering = ['cierre', 'empleado', 'concepto']
        indexes = [
            models.Index(fields=['cierre', 'empleado']),
            models.Index(fields=['cierre', 'concepto']),
            models.Index(fields=['empleado', 'concepto']),
        ]
        # Un empleado solo puede tener un registro por concepto
        unique_together = [
            ['empleado', 'concepto'],
        ]
    
    def __str__(self):
        return f"{self.empleado.rut} - {self.concepto.header_original}: ${self.monto:,.0f}"
