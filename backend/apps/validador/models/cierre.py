"""
Modelo de Cierre para el Validador de Nómina.
Representa un proceso de validación mensual para un cliente.
"""

from django.db import models
from django.contrib.auth import get_user_model
from apps.core.models import Cliente

User = get_user_model()


class Cierre(models.Model):
    """
    Cierre de Validación - Contenedor principal del proceso mensual.
    
    Flujo de estados:
    1. carga_archivos → Subiendo archivos ERP y Analista
    2. clasificacion_conceptos → Clasificando headers del libro (solo si hay nuevos)
    3. mapeo_items → Mapeando items Novedades → Libro (solo si hay nuevos)
    4. comparacion → Detectando discrepancias
    5. correccion_discrepancias → Usuario corrigiendo (re-subiendo archivos)
    6. consolidado → Discrepancias = 0, datos consolidados
    7. deteccion_incidencias → Comparando con mes anterior
    8. revision_incidencias → Foro analista-supervisor
    9. finalizado → Proceso completado
    """
    
    ESTADO_CHOICES = [
        ('carga_archivos', 'Carga de Archivos'),
        ('clasificacion_conceptos', 'Clasificación de Conceptos'),
        ('mapeo_items', 'Mapeo de Items'),
        ('comparacion', 'Comparación en Proceso'),
        ('con_discrepancias', 'Con Discrepancias'),
        ('consolidado', 'Consolidado'),
        ('deteccion_incidencias', 'Detectando Incidencias'),
        ('revision_incidencias', 'Revisión de Incidencias'),
        ('finalizado', 'Finalizado'),
        ('error', 'Error en Proceso'),
    ]
    
    # Relaciones principales
    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.CASCADE,
        related_name='cierres'
    )
    
    # Período (formato: YYYY-MM)
    periodo = models.CharField(
        max_length=7,
        help_text='Formato: YYYY-MM (ej: 2025-01)'
    )
    
    # Estado del proceso
    estado = models.CharField(
        max_length=30,
        choices=ESTADO_CHOICES,
        default='carga_archivos'
    )
    
    # Usuario analista asignado
    analista = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='cierres_asignados'
    )
    
    # Contadores para UI
    total_discrepancias = models.PositiveIntegerField(default=0)
    discrepancias_resueltas = models.PositiveIntegerField(default=0)
    total_incidencias = models.PositiveIntegerField(default=0)
    incidencias_aprobadas = models.PositiveIntegerField(default=0)
    
    # Flags de proceso
    es_primer_cierre = models.BooleanField(
        default=False,
        help_text='True si es el primer cierre del cliente (sin mes anterior)'
    )
    requiere_clasificacion = models.BooleanField(
        default=False,
        help_text='True si hay conceptos nuevos por clasificar'
    )
    requiere_mapeo = models.BooleanField(
        default=False,
        help_text='True si hay items nuevos por mapear'
    )
    
    # Timestamps
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    fecha_consolidacion = models.DateTimeField(null=True, blank=True)
    fecha_finalizacion = models.DateTimeField(null=True, blank=True)
    
    # Usuario que finalizó
    finalizado_por = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='cierres_finalizados'
    )
    
    # Notas/observaciones
    observaciones = models.TextField(blank=True)
    
    class Meta:
        verbose_name = 'Cierre'
        verbose_name_plural = 'Cierres'
        unique_together = ['cliente', 'periodo']
        ordering = ['-periodo', '-fecha_creacion']
        indexes = [
            models.Index(fields=['cliente', '-periodo']),
            models.Index(fields=['estado']),
            models.Index(fields=['analista', 'estado']),
        ]
    
    def __str__(self):
        return f"{self.cliente.nombre_display} - {self.periodo}"
    
    def get_cierre_anterior(self):
        """Obtiene el cierre del mes anterior si existe."""
        from datetime import datetime
        from dateutil.relativedelta import relativedelta
        
        try:
            fecha_actual = datetime.strptime(self.periodo, '%Y-%m')
            fecha_anterior = fecha_actual - relativedelta(months=1)
            periodo_anterior = fecha_anterior.strftime('%Y-%m')
            
            return Cierre.objects.filter(
                cliente=self.cliente,
                periodo=periodo_anterior,
                estado='finalizado'
            ).first()
        except:
            return None
    
    def actualizar_contadores(self):
        """Recalcula los contadores de discrepancias e incidencias."""
        self.total_discrepancias = self.discrepancias.count()
        self.discrepancias_resueltas = self.discrepancias.filter(resuelta=True).count()
        self.total_incidencias = self.incidencias.count()
        self.incidencias_aprobadas = self.incidencias.filter(estado='aprobada').count()
        self.save(update_fields=[
            'total_discrepancias', 
            'discrepancias_resueltas',
            'total_incidencias',
            'incidencias_aprobadas'
        ])
    
    @property
    def puede_consolidar(self):
        """Verifica si puede pasar a estado consolidado."""
        return (
            self.total_discrepancias == 0 or 
            self.total_discrepancias == self.discrepancias_resueltas
        )
    
    @property
    def puede_finalizar(self):
        """Verifica si puede finalizar el cierre."""
        if self.es_primer_cierre:
            # Sin mes anterior, no hay incidencias que revisar
            return self.estado == 'consolidado'
        
        return (
            self.total_incidencias == 0 or
            self.total_incidencias == self.incidencias_aprobadas
        )
