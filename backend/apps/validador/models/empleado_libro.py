"""
Modelo EmpleadoLibro para almacenar empleados del Libro de Remuneraciones.

Este modelo almacena la identificación de cada empleado extraído del Libro.
Los montos por concepto se guardan en RegistroLibro (relación 1:N).

Arquitectura Medallion - Capa Bronce (datos crudos).
"""

from django.db import models


class EmpleadoLibro(models.Model):
    """
    Empleado extraído del Libro de Remuneraciones.
    
    Solo almacena identificación básica del empleado.
    Los conceptos y montos se guardan en RegistroLibro (related_name='registros').
    
    Este modelo es parte de la capa Bronce (datos crudos) de la arquitectura medallion.
    Los totales y consolidación se calculan en la capa Oro.
    """
    
    cierre = models.ForeignKey(
        'Cierre',
        on_delete=models.CASCADE,
        related_name='empleados_libro',
        help_text='Cierre al que pertenece este empleado'
    )
    
    archivo_erp = models.ForeignKey(
        'ArchivoERP',
        on_delete=models.CASCADE,
        related_name='empleados_libro',
        help_text='Archivo del cual se extrajo este empleado'
    )
    
    # Identificación (únicos campos requeridos)
    rut = models.CharField(
        max_length=20,
        help_text='RUT del empleado (formato: 12345678-9)'
    )
    
    nombre = models.CharField(
        max_length=200,
        blank=True,
        help_text='Nombre completo del empleado (si viene en el libro)'
    )
    
    # Timestamps
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Empleado Libro'
        verbose_name_plural = 'Empleados Libro'
        unique_together = [
            ['cierre', 'archivo_erp', 'rut'],
        ]
        ordering = ['cierre', 'nombre', 'rut']
        indexes = [
            models.Index(fields=['cierre', 'rut']),
            models.Index(fields=['archivo_erp']),
            models.Index(fields=['cierre', 'archivo_erp']),
        ]
    
    def __str__(self):
        return f"{self.rut} - {self.nombre or '(sin nombre)'}"
