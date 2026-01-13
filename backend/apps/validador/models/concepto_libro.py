"""
Modelo de ConceptoLibro para clasificación de headers del Libro de Remuneraciones.

Este modelo permite clasificar los headers/columnas que vienen en el Excel del 
Libro de Remuneraciones según categorías predefinidas (haberes, descuentos, etc.).
"""

from django.db import models
from django.conf import settings
from django.utils.text import slugify


class ConceptoLibro(models.Model):
    """
    Concepto/Header del Libro de Remuneraciones clasificado.
    
    Cada header del Excel se clasifica en una categoría para poder
    procesar correctamente los montos de cada empleado.
    
    La clasificación es por cliente y ERP (el mismo header puede tener
    diferentes significados según el ERP usado).
    """
    
    CATEGORIA_CHOICES = [
        ('haberes_imponibles', 'Haberes Imponibles'),
        ('haberes_no_imponibles', 'Haberes No Imponibles'),
        ('descuentos_legales', 'Descuentos Legales'),
        ('otros_descuentos', 'Otros Descuentos'),
        ('aportes_patronales', 'Aportes Patronales'),
        ('info_adicional', 'Información Adicional'),
        ('ignorar', 'Ignorar'),
    ]
    
    cliente = models.ForeignKey(
        'core.Cliente',
        on_delete=models.CASCADE,
        related_name='conceptos_libro',
        help_text='Cliente al que pertenece esta clasificación'
    )
    
    erp = models.ForeignKey(
        'core.ERP',
        on_delete=models.CASCADE,
        related_name='conceptos_libro',
        help_text='ERP del cliente (mismo header puede variar por ERP)'
    )
    
    # Header original del Excel
    header_original = models.CharField(
        max_length=200,
        help_text='Nombre exacto como aparece en el Excel (ej: "SUELDO BASE", "AFP")'
    )
    
    # Header como lo lee pandas (puede tener .1, .2 para duplicados)
    header_pandas = models.CharField(
        max_length=200,
        blank=True,
        help_text='Nombre como pandas lo lee (ej: "BONO.1" para el segundo BONO)'
    )
    
    # Número de ocurrencia si es duplicado
    ocurrencia = models.PositiveIntegerField(
        default=1,
        help_text='Número de ocurrencia si el header está duplicado (1, 2, 3...)'
    )
    
    # Si este header está duplicado
    es_duplicado = models.BooleanField(
        default=False,
        help_text='True si este header aparece múltiples veces en el Excel'
    )
    
    # Header normalizado para matching
    header_normalizado = models.SlugField(
        max_length=200,
        help_text='Versión normalizada del header para búsqueda/matching'
    )
    
    # Clasificación
    categoria = models.CharField(
        max_length=30,
        choices=CATEGORIA_CHOICES,
        blank=True,
        null=True,
        help_text='Categoría asignada al concepto'
    )
    
    orden = models.PositiveIntegerField(
        default=0,
        help_text='Orden en que aparece la columna en el Excel'
    )
    
    activo = models.BooleanField(
        default=True,
        help_text='False = soft delete'
    )
    
    # Auditoría
    creado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='conceptos_libro_creados'
    )
    
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Concepto Libro'
        verbose_name_plural = 'Conceptos Libro'
        unique_together = [
            ['cliente', 'erp', 'header_original', 'ocurrencia'],
        ]
        ordering = ['cliente', 'erp', 'orden', 'header_original', 'ocurrencia']
        indexes = [
            models.Index(fields=['cliente', 'erp']),
            models.Index(fields=['cliente', 'erp', 'header_normalizado']),
            models.Index(fields=['categoria']),
            models.Index(fields=['cliente', 'erp', 'header_pandas']),
        ]
    
    def __str__(self):
        cat_display = self.get_categoria_display() if self.categoria else 'Sin clasificar'
        suffix = f" (#{self.ocurrencia})" if self.es_duplicado else ""
        return f"{self.header_original}{suffix} ({cat_display})"
    
    def save(self, *args, **kwargs):
        """Auto-generar header normalizado al guardar."""
        if not self.header_normalizado:
            self.header_normalizado = slugify(self.header_original)
        super().save(*args, **kwargs)
    
    @property
    def clasificado(self):
        """Retorna True si el concepto ya está clasificado."""
        return bool(self.categoria)
