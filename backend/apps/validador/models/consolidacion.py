"""
Modelo de Consolidación para el Validador de Nómina.
Datos finales consolidados después de validar.
"""

from django.db import models


class ResumenConsolidado(models.Model):
    """
    Resumen consolidado por concepto/categoría para un cierre.
    Se genera después de que discrepancias = 0.
    """
    
    cierre = models.ForeignKey(
        'Cierre',
        on_delete=models.CASCADE,
        related_name='resumenes'
    )
    
    categoria = models.ForeignKey(
        'CategoriaConcepto',
        on_delete=models.CASCADE,
        related_name='resumenes'
    )
    
    concepto = models.ForeignKey(
        'ConceptoCliente',
        on_delete=models.CASCADE,
        related_name='resumenes'
    )
    
    # Totales
    total_monto = models.DecimalField(
        max_digits=18,
        decimal_places=2,
        default=0
    )
    cantidad_empleados = models.PositiveIntegerField(
        default=0,
        help_text='Cantidad de empleados con este concepto'
    )
    monto_promedio = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0
    )
    monto_minimo = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0
    )
    monto_maximo = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0
    )
    
    class Meta:
        verbose_name = 'Resumen Consolidado'
        verbose_name_plural = 'Resúmenes Consolidados'
        unique_together = ['cierre', 'concepto']
        ordering = ['categoria', 'concepto']
    
    def __str__(self):
        return f"{self.cierre.periodo} - {self.concepto.nombre_erp}: ${self.total_monto:,.0f}"


class ResumenCategoria(models.Model):
    """
    Resumen por categoría (haberes, descuentos, etc).
    Para dashboards rápidos.
    """
    
    cierre = models.ForeignKey(
        'Cierre',
        on_delete=models.CASCADE,
        related_name='resumenes_categoria'
    )
    
    categoria = models.ForeignKey(
        'CategoriaConcepto',
        on_delete=models.CASCADE,
        related_name='resumenes_totales'
    )
    
    total_monto = models.DecimalField(
        max_digits=18,
        decimal_places=2,
        default=0
    )
    cantidad_conceptos = models.PositiveIntegerField(default=0)
    cantidad_empleados_afectados = models.PositiveIntegerField(default=0)
    
    class Meta:
        verbose_name = 'Resumen por Categoría'
        verbose_name_plural = 'Resúmenes por Categoría'
        unique_together = ['cierre', 'categoria']
    
    def __str__(self):
        return f"{self.cierre.periodo} - {self.categoria.nombre}: ${self.total_monto:,.0f}"


class ResumenMovimientos(models.Model):
    """
    Resumen de movimientos del mes por tipo.
    Para dashboard de movimientos.
    """
    
    cierre = models.ForeignKey(
        'Cierre',
        on_delete=models.CASCADE,
        related_name='resumenes_movimientos'
    )
    
    TIPO_CHOICES = [
        ('alta', 'Altas/Ingresos'),
        ('baja', 'Bajas/Finiquitos'),
        ('licencia', 'Licencias Médicas'),
        ('vacaciones', 'Vacaciones'),
        ('permiso', 'Permisos'),
        ('ausencia', 'Ausencias'),
    ]
    
    tipo = models.CharField(
        max_length=20,
        choices=TIPO_CHOICES
    )
    
    cantidad = models.PositiveIntegerField(default=0)
    total_dias = models.PositiveIntegerField(
        default=0,
        help_text='Total de días (para licencias/vacaciones)'
    )
    
    # Lista de RUTs afectados (para drill-down)
    empleados = models.JSONField(
        default=list,
        help_text='Lista de {rut, nombre} afectados'
    )
    
    class Meta:
        verbose_name = 'Resumen de Movimientos'
        verbose_name_plural = 'Resúmenes de Movimientos'
        unique_together = ['cierre', 'tipo']
    
    def __str__(self):
        return f"{self.cierre.periodo} - {self.get_tipo_display()}: {self.cantidad}"
