"""
Modelos de Incidencia para el Validador de Nómina.
Detectadas al comparar con el mes anterior.
"""

from django.db import models
from django.conf import settings


class Incidencia(models.Model):
    """
    Incidencia detectada al comparar totales con el mes anterior.
    Se genera cuando la variación de un concepto supera el 30%.
    """
    
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente de Revisión'),
        ('en_revision', 'En Revisión'),
        ('aprobada', 'Aprobada'),
        ('rechazada', 'Rechazada'),
    ]
    
    cierre = models.ForeignKey(
        'Cierre',
        on_delete=models.CASCADE,
        related_name='incidencias'
    )
    
    # Concepto afectado
    concepto = models.ForeignKey(
        'ConceptoCliente',
        on_delete=models.CASCADE,
        related_name='incidencias'
    )
    
    # Categoría (para agrupar en UI)
    categoria = models.ForeignKey(
        'CategoriaConcepto',
        on_delete=models.CASCADE,
        related_name='incidencias'
    )
    
    # Montos comparados
    monto_mes_anterior = models.DecimalField(
        max_digits=15,
        decimal_places=2
    )
    monto_mes_actual = models.DecimalField(
        max_digits=15,
        decimal_places=2
    )
    diferencia_absoluta = models.DecimalField(
        max_digits=15,
        decimal_places=2
    )
    variacion_porcentual = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        help_text='Variación en porcentaje'
    )
    
    # Estado de revisión
    estado = models.CharField(
        max_length=20,
        choices=ESTADO_CHOICES,
        default='pendiente'
    )
    
    # Resolución
    resuelto_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='incidencias_resueltas'
    )
    fecha_resolucion = models.DateTimeField(null=True, blank=True)
    motivo_resolucion = models.TextField(
        blank=True,
        help_text='Justificación de la aprobación/rechazo'
    )
    
    # Timestamps
    fecha_deteccion = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Incidencia'
        verbose_name_plural = 'Incidencias'
        ordering = ['-variacion_porcentual']
        indexes = [
            models.Index(fields=['cierre', 'estado']),
            models.Index(fields=['cierre', 'categoria']),
        ]
    
    def __str__(self):
        return f"{self.concepto.nombre_erp} - {self.variacion_porcentual:+.1f}%"
    
    @property
    def es_variacion_positiva(self):
        return self.diferencia_absoluta > 0
    
    def calcular_variacion(self):
        """Calcula la variación porcentual."""
        if self.monto_mes_anterior and self.monto_mes_anterior != 0:
            self.diferencia_absoluta = self.monto_mes_actual - self.monto_mes_anterior
            self.variacion_porcentual = (
                (self.diferencia_absoluta / abs(self.monto_mes_anterior)) * 100
            )
        else:
            self.diferencia_absoluta = self.monto_mes_actual
            self.variacion_porcentual = 100  # 100% si no había monto anterior


class ComentarioIncidencia(models.Model):
    """
    Comentario en el foro de una incidencia.
    Permite la conversación entre analista y supervisor.
    """
    
    incidencia = models.ForeignKey(
        Incidencia,
        on_delete=models.CASCADE,
        related_name='comentarios'
    )
    
    autor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='comentarios_incidencias'
    )
    
    contenido = models.TextField()
    
    # Archivos adjuntos (opcional)
    archivo_adjunto = models.FileField(
        upload_to='incidencias/adjuntos/',
        null=True,
        blank=True
    )
    nombre_adjunto = models.CharField(max_length=255, blank=True)
    
    # Timestamps
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_edicion = models.DateTimeField(auto_now=True)
    editado = models.BooleanField(default=False)
    
    class Meta:
        verbose_name = 'Comentario de Incidencia'
        verbose_name_plural = 'Comentarios de Incidencias'
        ordering = ['fecha_creacion']
    
    def __str__(self):
        return f"{self.autor.get_full_name()} - {self.fecha_creacion}"
