"""
Modelos de Discrepancia para el Validador de Nómina.
Resultado de comparar ERP vs Archivos del Analista.
"""

from django.db import models


class Discrepancia(models.Model):
    """
    Discrepancia detectada entre datos del ERP y datos del cliente.
    """
    
    TIPO_CHOICES = [
        ('monto_diferente', 'Monto Diferente'),
        ('falta_en_erp', 'Falta en ERP'),
        ('falta_en_cliente', 'Falta en Archivos Cliente'),
    ]
    
    ORIGEN_CHOICES = [
        ('libro_vs_novedades', 'Libro vs Novedades'),
        ('movimientos_vs_analista', 'Movimientos vs Archivos Analista'),
    ]
    
    cierre = models.ForeignKey(
        'Cierre',
        on_delete=models.CASCADE,
        related_name='discrepancias'
    )
    
    tipo = models.CharField(
        max_length=30,
        choices=TIPO_CHOICES
    )
    
    origen = models.CharField(
        max_length=30,
        choices=ORIGEN_CHOICES
    )
    
    # Datos del empleado afectado
    rut_empleado = models.CharField(max_length=12)
    nombre_empleado = models.CharField(max_length=200, blank=True)
    
    # Para discrepancias de montos (libro vs novedades)
    concepto = models.ForeignKey(
        'ConceptoCliente',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='discrepancias'
    )
    # Nombre del concepto en cada fuente
    nombre_item = models.CharField(
        max_length=200,
        blank=True,
        help_text='Nombre del concepto en el Libro (ERP)'
    )
    nombre_item_novedades = models.CharField(
        max_length=200,
        blank=True,
        help_text='Nombre del concepto en Novedades (cliente)'
    )
    monto_erp = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True
    )
    monto_cliente = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True
    )
    diferencia = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True
    )
    
    # Para discrepancias de movimientos
    tipo_movimiento = models.CharField(max_length=30, blank=True)
    detalle_movimiento = models.JSONField(default=dict, blank=True)
    
    # Estado
    resuelta = models.BooleanField(default=False)
    fecha_resolucion = models.DateTimeField(null=True, blank=True)
    
    # Descripción legible
    descripcion = models.TextField(blank=True)
    
    # Timestamps
    fecha_deteccion = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Discrepancia'
        verbose_name_plural = 'Discrepancias'
        ordering = ['-fecha_deteccion']
        indexes = [
            models.Index(fields=['cierre', 'tipo']),
            models.Index(fields=['cierre', 'origen']),
            models.Index(fields=['cierre', 'resuelta']),
            models.Index(fields=['cierre', 'rut_empleado']),
        ]
    
    def __str__(self):
        return f"{self.get_tipo_display()} - {self.rut_empleado}"
    
    def calcular_diferencia(self):
        """Calcula la diferencia entre montos."""
        if self.monto_erp is not None and self.monto_cliente is not None:
            self.diferencia = self.monto_erp - self.monto_cliente
    
    def generar_descripcion(self):
        """Genera una descripción legible de la discrepancia."""
        if self.tipo == 'monto_diferente':
            self.descripcion = (
                f"'{self.nombre_item}' (Libro) vs '{self.nombre_item_novedades}' (Novedades): "
                f"${self.monto_erp:,.0f} vs ${self.monto_cliente:,.0f} = ${self.diferencia:,.0f}"
            )
        elif self.tipo == 'falta_en_erp':
            self.descripcion = (
                f"El movimiento '{self.tipo_movimiento}' existe en archivos del cliente pero no en ERP."
            )
        elif self.tipo == 'falta_en_cliente':
            self.descripcion = (
                f"El movimiento '{self.tipo_movimiento}' existe en ERP pero no en archivos del cliente."
            )
