"""
Modelos de Concepto para el Validador de Nómina.
Maneja la clasificación de headers del Libro de Remuneraciones.
"""

from django.db import models
from django.conf import settings
from apps.core.models import Cliente


class CategoriaConcepto(models.Model):
    """
    Categorías predefinidas para clasificar conceptos.
    Son fijas del sistema.
    """
    
    CODIGO_CHOICES = [
        ('haberes_imponibles', 'Haberes Imponibles'),
        ('haberes_no_imponibles', 'Haberes No Imponibles'),
        ('descuentos_legales', 'Descuentos Legales'),
        ('otros_descuentos', 'Otros Descuentos'),
        ('aportes_patronales', 'Aportes Patronales'),
        ('informativos', 'Informativos'),
    ]
    
    codigo = models.CharField(
        max_length=30,
        choices=CODIGO_CHOICES,
        unique=True,
        primary_key=True
    )
    nombre = models.CharField(max_length=50)
    descripcion = models.TextField(blank=True)
    
    # Configuración de comparación
    se_compara = models.BooleanField(
        default=True,
        help_text='¿Los items de esta categoría se comparan con Novedades?'
    )
    se_incluye_en_incidencias = models.BooleanField(
        default=True,
        help_text='¿Los items de esta categoría se incluyen en detección de incidencias?'
    )
    
    orden = models.PositiveIntegerField(default=0)
    
    class Meta:
        verbose_name = 'Categoría de Concepto'
        verbose_name_plural = 'Categorías de Conceptos'
        ordering = ['orden']
    
    def __str__(self):
        return self.nombre


class ConceptoCliente(models.Model):
    """
    Concepto/Header del Libro de Remuneraciones clasificado.
    Es específico por cliente (cada cliente tiene sus propios nombres de conceptos).
    """
    
    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.CASCADE,
        related_name='conceptos'
    )
    
    # Nombre exacto como aparece en el Excel
    nombre_erp = models.CharField(
        max_length=200,
        help_text='Nombre del concepto como aparece en el ERP'
    )
    
    # Clasificación
    categoria = models.ForeignKey(
        CategoriaConcepto,
        on_delete=models.PROTECT,
        related_name='conceptos',
        null=True,
        blank=True
    )
    
    # Estado de clasificación
    clasificado = models.BooleanField(default=False)
    clasificado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='conceptos_clasificados'
    )
    fecha_clasificacion = models.DateTimeField(null=True, blank=True)
    
    # Configuración especial
    ignorar_en_comparacion = models.BooleanField(
        default=False,
        help_text='Ignorar este concepto específico en comparaciones'
    )
    multiplicador = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        default=1,
        help_text='Factor multiplicador (si el ERP aplica algún cálculo)'
    )
    
    # Timestamps
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Concepto de Cliente'
        verbose_name_plural = 'Conceptos de Clientes'
        unique_together = ['cliente', 'nombre_erp']
        ordering = ['cliente', 'categoria', 'nombre_erp']
    
    def __str__(self):
        cat = self.categoria.nombre if self.categoria else 'Sin clasificar'
        return f"{self.nombre_erp} ({cat})"
    
    @property
    def se_compara(self):
        """Determina si este concepto se debe comparar."""
        if self.ignorar_en_comparacion:
            return False
        if not self.categoria:
            return False
        return self.categoria.se_compara


class MapeoItemNovedades(models.Model):
    """
    Mapeo 1:1 entre items de Novedades (cliente) y Conceptos del Libro (ERP).
    Se guarda por cliente para reutilizar en futuros cierres.
    """
    
    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.CASCADE,
        related_name='mapeos_items'
    )
    
    # Nombre del item en el archivo de Novedades (del cliente)
    nombre_novedades = models.CharField(
        max_length=200,
        help_text='Nombre del item como aparece en Novedades'
    )
    
    # Concepto del ERP al que mapea
    concepto_erp = models.ForeignKey(
        ConceptoCliente,
        on_delete=models.CASCADE,
        related_name='mapeos_novedades'
    )
    
    # Quién hizo el mapeo
    mapeado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True
    )
    fecha_mapeo = models.DateTimeField(auto_now_add=True)
    
    # Notas sobre el mapeo
    notas = models.TextField(blank=True)
    
    class Meta:
        verbose_name = 'Mapeo Item Novedades'
        verbose_name_plural = 'Mapeos Items Novedades'
        unique_together = ['cliente', 'nombre_novedades']
        ordering = ['cliente', 'nombre_novedades']
    
    def __str__(self):
        return f"{self.nombre_novedades} → {self.concepto_erp.nombre_erp}"
