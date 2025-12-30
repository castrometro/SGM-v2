"""
Modelos de Archivos para el Validador de Nómina.
Representa los archivos Excel subidos al sistema.
"""

import os
from django.db import models
from django.contrib.auth import get_user_model
from datetime import datetime

User = get_user_model()


def archivo_upload_path(instance, filename):
    """Genera la ruta de almacenamiento para los archivos."""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    cliente_id = instance.cierre.cliente_id
    periodo = instance.cierre.periodo
    tipo = instance.tipo
    
    # Limpiar nombre de archivo
    nombre_limpio = filename.replace(' ', '_')
    
    return f'cierres/{cliente_id}/{periodo}/{tipo}/{timestamp}_{nombre_limpio}'


class ArchivoBase(models.Model):
    """Modelo base abstracto para archivos."""
    
    ESTADO_CHOICES = [
        ('subido', 'Subido'),
        ('procesando', 'Procesando'),
        ('procesado', 'Procesado'),
        ('error', 'Error'),
    ]
    
    archivo = models.FileField(upload_to=archivo_upload_path)
    nombre_original = models.CharField(max_length=255)
    
    estado = models.CharField(
        max_length=20,
        choices=ESTADO_CHOICES,
        default='subido'
    )
    
    # Metadatos del procesamiento
    filas_procesadas = models.PositiveIntegerField(default=0)
    errores_procesamiento = models.JSONField(default=list, blank=True)
    
    # Timestamps
    fecha_subida = models.DateTimeField(auto_now_add=True)
    fecha_procesamiento = models.DateTimeField(null=True, blank=True)
    
    # Usuario que subió
    subido_por = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True
    )
    
    class Meta:
        abstract = True
    
    def __str__(self):
        return f"{self.nombre_original} ({self.get_estado_display()})"
    
    @property
    def extension(self):
        return os.path.splitext(self.nombre_original)[1].lower()


class ArchivoERP(ArchivoBase):
    """
    Archivos provenientes del ERP (Talana/BUK/Rex+).
    - Libro de Remuneraciones
    - Movimientos del Mes
    """
    
    TIPO_CHOICES = [
        ('libro_remuneraciones', 'Libro de Remuneraciones'),
        ('movimientos_mes', 'Movimientos del Mes'),
    ]
    
    cierre = models.ForeignKey(
        'Cierre',
        on_delete=models.CASCADE,
        related_name='archivos_erp'
    )
    
    tipo = models.CharField(
        max_length=30,
        choices=TIPO_CHOICES
    )
    
    # Para Movimientos: qué hojas se encontraron
    hojas_encontradas = models.JSONField(
        default=list,
        blank=True,
        help_text='Lista de hojas encontradas en el Excel (para Movimientos)'
    )
    
    # Versión del archivo (para re-subidas)
    version = models.PositiveIntegerField(default=1)
    es_version_actual = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = 'Archivo ERP'
        verbose_name_plural = 'Archivos ERP'
        ordering = ['-fecha_subida']
    
    def save(self, *args, **kwargs):
        # Al guardar nueva versión, marcar anteriores como no actuales
        if not self.pk and self.es_version_actual:
            ArchivoERP.objects.filter(
                cierre=self.cierre,
                tipo=self.tipo,
                es_version_actual=True
            ).update(es_version_actual=False)
            
            # Calcular versión
            ultima_version = ArchivoERP.objects.filter(
                cierre=self.cierre,
                tipo=self.tipo
            ).aggregate(max_v=models.Max('version'))['max_v'] or 0
            self.version = ultima_version + 1
        
        super().save(*args, **kwargs)


class ArchivoAnalista(ArchivoBase):
    """
    Archivos proporcionados por el cliente al analista.
    - Novedades
    - Asistencias
    - Finiquitos
    - Ingresos
    """
    
    TIPO_CHOICES = [
        ('novedades', 'Novedades'),
        ('asistencias', 'Asistencias'),
        ('finiquitos', 'Finiquitos'),
        ('ingresos', 'Ingresos'),
    ]
    
    cierre = models.ForeignKey(
        'Cierre',
        on_delete=models.CASCADE,
        related_name='archivos_analista'
    )
    
    tipo = models.CharField(
        max_length=30,
        choices=TIPO_CHOICES
    )
    
    # Versión del archivo (para re-subidas)
    version = models.PositiveIntegerField(default=1)
    es_version_actual = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = 'Archivo Analista'
        verbose_name_plural = 'Archivos Analista'
        ordering = ['-fecha_subida']
    
    def save(self, *args, **kwargs):
        if not self.pk and self.es_version_actual:
            ArchivoAnalista.objects.filter(
                cierre=self.cierre,
                tipo=self.tipo,
                es_version_actual=True
            ).update(es_version_actual=False)
            
            ultima_version = ArchivoAnalista.objects.filter(
                cierre=self.cierre,
                tipo=self.tipo
            ).aggregate(max_v=models.Max('version'))['max_v'] or 0
            self.version = ultima_version + 1
        
        super().save(*args, **kwargs)
