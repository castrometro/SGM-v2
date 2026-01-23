"""
Modelo de ConceptoNovedades para clasificación de headers del archivo de Novedades.

Este modelo permite mapear los headers/columnas que vienen en el Excel del 
archivo de Novedades del cliente hacia los ConceptosLibro correspondientes.

Sigue el mismo patrón que ConceptoLibro pero en vez de clasificar por categoría,
se mapea directamente a un ConceptoLibro existente.
"""

from django.db import models
from django.conf import settings
from django.utils.text import slugify


class ConceptoNovedades(models.Model):
    """
    Concepto/Header del archivo de Novedades del cliente.
    
    Cada header del Excel de novedades se mapea a un ConceptoLibro
    para poder comparar los datos entre ambos archivos.
    
    El mapeo es por cliente y ERP, y se reutiliza entre cierres.
    """
    
    cliente = models.ForeignKey(
        'core.Cliente',
        on_delete=models.CASCADE,
        related_name='conceptos_novedades',
        help_text='Cliente al que pertenece este mapeo'
    )
    
    erp = models.ForeignKey(
        'core.ERP',
        on_delete=models.CASCADE,
        related_name='conceptos_novedades',
        help_text='ERP del cliente'
    )
    
    # Header original del Excel de novedades
    header_original = models.TextField(
        help_text='Nombre exacto como aparece en el Excel de novedades'
    )
    
    # Header normalizado para matching
    header_normalizado = models.SlugField(
        max_length=200,
        help_text='Versión normalizada del header para búsqueda/matching'
    )
    
    # Mapeo a ConceptoLibro (equivalente a "categoria" en ConceptoLibro)
    concepto_libro = models.ForeignKey(
        'validador.ConceptoLibro',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='conceptos_novedades',
        help_text='Concepto del libro al que mapea (null = sin mapear)'
    )
    
    # Flag para items que no tienen equivalente en el libro
    sin_asignacion = models.BooleanField(
        default=False,
        help_text='True = este item no tiene equivalente en el libro y se ignorará en comparación'
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
        related_name='conceptos_novedades_creados'
    )
    
    mapeado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='conceptos_novedades_mapeados'
    )
    
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_mapeo = models.DateTimeField(null=True, blank=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Concepto Novedades'
        verbose_name_plural = 'Conceptos Novedades'
        unique_together = [
            ['cliente', 'erp', 'header_original'],
        ]
        ordering = ['cliente', 'erp', 'orden', 'header_original']
        indexes = [
            models.Index(fields=['cliente', 'erp']),
            models.Index(fields=['cliente', 'erp', 'header_normalizado']),
            models.Index(fields=['concepto_libro']),
        ]
        constraints = [
            # Debe tener concepto_libro O sin_asignacion=True (o ninguno si está pendiente)
            # Esta constraint se aplica solo cuando mapeado=True
            models.CheckConstraint(
                check=models.Q(concepto_libro__isnull=True) | models.Q(sin_asignacion=False),
                name='concepto_libro_xor_sin_asignacion',
            ),
        ]
    
    def __str__(self):
        if self.concepto_libro:
            return f"{self.header_original[:50]} → {self.concepto_libro.header_original[:30]}"
        return f"{self.header_original[:50]} (sin mapear)"
    
    def save(self, *args, **kwargs):
        # Generar header_normalizado
        if not self.header_normalizado:
            # Truncar a 200 chars para el slug
            self.header_normalizado = slugify(self.header_original[:200])[:200]
        super().save(*args, **kwargs)
    
    @property
    def mapeado(self):
        """Retorna True si tiene mapeo a ConceptoLibro O está marcado sin_asignacion."""
        return self.concepto_libro is not None or self.sin_asignacion
    
    @property
    def categoria(self):
        """Retorna la categoría del ConceptoLibro mapeado, si existe."""
        if self.concepto_libro:
            return self.concepto_libro.categoria
        return None
