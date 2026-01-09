"""
Modelo EmpleadoLibro para almacenar datos procesados del Libro de Remuneraciones.

Este modelo almacena los datos de cada empleado extraídos del Libro de Remuneraciones
antes de la consolidación final. Sirve como capa intermedia para verificación y validación.
"""

from django.db import models
from decimal import Decimal


class EmpleadoLibro(models.Model):
    """
    Empleado extraído del Libro de Remuneraciones.
    
    Almacena los datos procesados de cada empleado del libro,
    con el detalle de conceptos agrupados por categoría en formato JSON.
    
    Este modelo es intermedio: se carga al procesar el libro y luego
    se usa para generar los registros finales en EmpleadoCierre.
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
    
    # Identificación
    rut = models.CharField(
        max_length=12,
        help_text='RUT del empleado (formato: 12345678-9)'
    )
    
    nombre = models.CharField(
        max_length=200,
        blank=True,
        help_text='Nombre completo del empleado (si viene en el libro)'
    )
    
    # Datos adicionales (si vienen en el libro)
    cargo = models.CharField(max_length=200, blank=True)
    centro_costo = models.CharField(max_length=100, blank=True)
    area = models.CharField(max_length=100, blank=True)
    fecha_ingreso = models.DateField(null=True, blank=True)
    
    # Datos JSON con detalle por categoría
    datos_json = models.JSONField(
        default=dict,
        help_text="""
        Estructura: {
            "haberes_imponibles": {
                "SUELDO BASE": 1500000,
                "BONO PRODUCCION": 200000,
                "total": 1700000
            },
            "haberes_no_imponibles": {...},
            "descuentos_legales": {...},
            ...
        }
        """
    )
    
    # Totales calculados (para queries rápidas sin procesar JSON)
    total_haberes_imponibles = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text='Suma de todos los haberes imponibles'
    )
    
    total_haberes_no_imponibles = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text='Suma de todos los haberes no imponibles'
    )
    
    total_descuentos_legales = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text='Suma de descuentos legales (AFP, Salud, etc.)'
    )
    
    total_otros_descuentos = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text='Suma de otros descuentos'
    )
    
    total_aportes_patronales = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text='Suma de aportes patronales'
    )
    
    total_liquido = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text='Líquido a pagar (haberes - descuentos)'
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
    
    def calcular_totales(self):
        """
        Calcula los totales desde datos_json y actualiza los campos de totales.
        
        Returns:
            dict con los totales calculados
        """
        from decimal import Decimal
        
        totales = {
            'total_haberes_imponibles': Decimal('0.00'),
            'total_haberes_no_imponibles': Decimal('0.00'),
            'total_descuentos_legales': Decimal('0.00'),
            'total_otros_descuentos': Decimal('0.00'),
            'total_aportes_patronales': Decimal('0.00'),
        }
        
        # Mapeo de categorías a campos de totales
        mapeo_categorias = {
            'haberes_imponibles': 'total_haberes_imponibles',
            'haberes_no_imponibles': 'total_haberes_no_imponibles',
            'descuentos_legales': 'total_descuentos_legales',
            'otros_descuentos': 'total_otros_descuentos',
            'aportes_patronales': 'total_aportes_patronales',
        }
        
        # Calcular totales desde datos_json
        for categoria, campo_total in mapeo_categorias.items():
            if categoria in self.datos_json:
                total = self.datos_json[categoria].get('total', 0)
                totales[campo_total] = Decimal(str(total))
        
        # Calcular líquido: (haberes imponibles + no imponibles) - (descuentos legales + otros)
        totales['total_liquido'] = (
            totales['total_haberes_imponibles'] +
            totales['total_haberes_no_imponibles'] -
            totales['total_descuentos_legales'] -
            totales['total_otros_descuentos']
        )
        
        # Actualizar campos del modelo
        for campo, valor in totales.items():
            setattr(self, campo, valor)
        
        return totales
    
    def get_concepto_monto(self, categoria: str, concepto: str) -> Decimal:
        """
        Obtiene el monto de un concepto específico.
        
        Args:
            categoria: Categoría del concepto (ej: 'haberes_imponibles')
            concepto: Nombre del concepto (ej: 'SUELDO BASE')
        
        Returns:
            Monto del concepto o 0 si no existe
        """
        if categoria not in self.datos_json:
            return Decimal('0.00')
        
        monto = self.datos_json[categoria].get(concepto, 0)
        return Decimal(str(monto))
