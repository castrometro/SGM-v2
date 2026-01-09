"""
Modelos de ERP y ConfiguracionERPCliente para SGM v2.

Estos modelos permiten:
- Definir catálogo de sistemas ERP soportados (Talana, BUK, SAP, etc.)
- Configurar qué ERP usa cada cliente con sus credenciales
- Determinar dinámicamente la estrategia de parseo de archivos (Factory pattern)
"""

from django.db import models
from django.core.exceptions import ValidationError


class ERP(models.Model):
    """
    Catálogo de sistemas ERP soportados por SGM.
    
    El campo `slug` se usa como clave para el Factory pattern,
    permitiendo instanciar la estrategia de parseo correcta.
    
    Ejemplos: Talana, BUK, SAP, Nubox, Softland
    
    Uso:
        erp = ERP.objects.get(slug='talana')
        strategy = ERPFactory.get_strategy(erp.slug, erp.configuracion_parseo)
    """
    
    slug = models.SlugField(
        'Slug',
        max_length=50,
        unique=True,
        help_text='Identificador único para Factory pattern (ej: talana, buk, sap)'
    )
    nombre = models.CharField(
        'Nombre',
        max_length=100,
        help_text='Nombre del sistema ERP para mostrar'
    )
    descripcion = models.TextField(
        'Descripción',
        blank=True,
        help_text='Descripción del ERP y sus características'
    )
    activo = models.BooleanField(
        'Activo',
        default=True,
        help_text='Si el ERP está disponible para asignar a clientes'
    )
    
    # Metadatos técnicos para integración
    requiere_api = models.BooleanField(
        'Requiere API',
        default=False,
        help_text='Si el ERP tiene API para integración directa (reportería)'
    )
    formatos_soportados = models.JSONField(
        'Formatos Soportados',
        default=list,
        help_text='Lista de extensiones de archivo: ["xlsx", "csv", "txt"]'
    )
    schema_credenciales = models.JSONField(
        'Schema de Credenciales',
        default=dict,
        blank=True,
        help_text='JSON Schema para validar campos de credenciales requeridas'
    )
    
    # Configuración específica de parseo (usada por Strategy)
    configuracion_parseo = models.JSONField(
        'Configuración de Parseo',
        default=dict,
        blank=True,
        help_text='Configuración específica: columnas, hojas, delimitadores, mapeos'
    )
    
    # Timestamps
    created_at = models.DateTimeField(
        'Fecha de Creación',
        auto_now_add=True
    )
    updated_at = models.DateTimeField(
        'Última Actualización',
        auto_now=True
    )
    
    class Meta:
        verbose_name = 'ERP'
        verbose_name_plural = 'ERPs'
        ordering = ['nombre']
    
    def __str__(self):
        return self.nombre
    
    def clean(self):
        """Validación del modelo."""
        super().clean()
        # Asegurar que formatos_soportados sea una lista
        if self.formatos_soportados and not isinstance(self.formatos_soportados, list):
            raise ValidationError({
                'formatos_soportados': 'Debe ser una lista de extensiones, ej: ["xlsx", "csv"]'
            })
    
    @property
    def formatos_display(self) -> str:
        """Retorna los formatos soportados como string para mostrar."""
        if self.formatos_soportados:
            return ', '.join(self.formatos_soportados)
        return 'Todos'


class ConfiguracionERPCliente(models.Model):
    """
    Configuración de un ERP específico para un Cliente.
    
    Vincula Cliente ↔ ERP con:
    - Credenciales de acceso (para APIs)
    - Fechas de vigencia
    - Estado activo/inactivo
    
    Un cliente puede tener múltiples ERPs configurados pero solo uno activo.
    
    Uso:
        config = cliente.configuraciones_erp.filter(activo=True).first()
        if config and config.esta_vigente:
            strategy = ERPFactory.get_strategy(config.erp.slug)
    """
    
    cliente = models.ForeignKey(
        'Cliente',
        on_delete=models.CASCADE,
        related_name='configuraciones_erp',
        verbose_name='Cliente'
    )
    erp = models.ForeignKey(
        ERP,
        on_delete=models.CASCADE,
        related_name='configuraciones',
        verbose_name='ERP'
    )
    
    # Credenciales y conexión
    # Nota: En producción, considerar encriptar con django-encrypted-model-fields
    credenciales = models.JSONField(
        'Credenciales',
        default=dict,
        blank=True,
        help_text='Credenciales específicas: {token, client_id, base_url, api_key, etc.}'
    )
    
    # Vigencia
    fecha_activacion = models.DateField(
        'Fecha de Activación',
        help_text='Desde cuándo está activa esta configuración'
    )
    fecha_expiracion = models.DateField(
        'Fecha de Expiración',
        null=True,
        blank=True,
        help_text='Fecha límite de vigencia (null = sin vencimiento)'
    )
    activo = models.BooleanField(
        'Activo',
        default=True,
        help_text='Si esta configuración está habilitada'
    )
    
    # Notas de configuración
    notas = models.TextField(
        'Notas',
        blank=True,
        help_text='Notas sobre esta configuración (contacto técnico, observaciones)'
    )
    
    # Auditoría
    created_at = models.DateTimeField(
        'Fecha de Creación',
        auto_now_add=True
    )
    updated_at = models.DateTimeField(
        'Última Actualización',
        auto_now=True
    )
    
    class Meta:
        verbose_name = 'Configuración ERP de Cliente'
        verbose_name_plural = 'Configuraciones ERP de Clientes'
        constraints = [
            models.UniqueConstraint(
                fields=['cliente', 'erp'],
                name='unique_cliente_erp'
            )
        ]
        ordering = ['cliente', 'erp']
    
    def __str__(self):
        return f"{self.cliente} ↔ {self.erp}"
    
    def clean(self):
        """Validación del modelo."""
        super().clean()
        
        # Validar que fecha_expiracion sea posterior a fecha_activacion
        if self.fecha_expiracion and self.fecha_activacion:
            if self.fecha_expiracion < self.fecha_activacion:
                raise ValidationError({
                    'fecha_expiracion': 'Debe ser posterior a la fecha de activación'
                })
        
        # Validar credenciales contra schema del ERP (si existe)
        if self.erp_id and self.erp.schema_credenciales and self.credenciales:
            # TODO: Implementar validación con jsonschema
            pass
    
    @property
    def esta_vigente(self) -> bool:
        """
        Verifica si la configuración está vigente.
        
        Returns:
            True si está activa y dentro del rango de fechas
        """
        from django.utils import timezone
        today = timezone.now().date()
        
        if not self.activo:
            return False
        if self.fecha_expiracion and self.fecha_expiracion < today:
            return False
        return self.fecha_activacion <= today
    
    @property
    def dias_para_expirar(self) -> int | None:
        """
        Calcula días restantes para expiración.
        
        Returns:
            Número de días o None si no tiene fecha de expiración
        """
        if not self.fecha_expiracion:
            return None
        
        from django.utils import timezone
        today = timezone.now().date()
        delta = self.fecha_expiracion - today
        return delta.days
    
    def get_credencial(self, key: str, default=None):
        """
        Obtiene una credencial específica de forma segura.
        
        Args:
            key: Nombre de la credencial (ej: 'token', 'base_url')
            default: Valor por defecto si no existe
        
        Returns:
            Valor de la credencial o default
        """
        if self.credenciales:
            return self.credenciales.get(key, default)
        return default
