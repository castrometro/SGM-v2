"""
Modelo AuditLog para registro de acciones CRUD.

Implementa auditoría según ISO 27001/27701 y Ley 21.719.
Registra CREATE, UPDATE, DELETE sobre modelos sensibles.
"""

from django.conf import settings
from django.db import models


class AuditLog(models.Model):
    """
    Registro de auditoría para acciones CRUD.
    
    Captura quién hizo qué, cuándo y sobre qué objeto.
    No usa FK a objetos auditados para mantener integridad histórica.
    
    Compliance:
        - ISO 27001:2022 (A.8.15, A.8.16) - Logging y monitoreo
        - ISO 27701:2019 (7.3.6) - Log de acceso a recursos
        - Ley 21.719 Chile - Datos personales sensibles
    """
    
    # Quién realizó la acción
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_logs',
        help_text='Usuario que realizó la acción'
    )
    usuario_email = models.EmailField(
        blank=True,
        help_text='Email del usuario al momento de la acción (inmutable)'
    )
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text='Dirección IP del cliente'
    )
    user_agent = models.TextField(
        blank=True,
        help_text='User-Agent del navegador/cliente'
    )
    
    # Qué acción se realizó
    accion = models.CharField(
        max_length=20,
        db_index=True,
        help_text='Tipo de acción: create, update, delete, login, logout, export'
    )
    
    # Sobre qué objeto
    modelo = models.CharField(
        max_length=100,
        db_index=True,
        help_text='Modelo afectado (ej: validador.Cierre)'
    )
    objeto_id = models.PositiveIntegerField(
        null=True,
        blank=True,
        db_index=True,
        help_text='ID del objeto afectado'
    )
    objeto_repr = models.CharField(
        max_length=255,
        blank=True,
        help_text='Representación string del objeto'
    )
    
    # Contexto adicional para filtrado
    cliente_id = models.PositiveIntegerField(
        null=True,
        blank=True,
        db_index=True,
        help_text='ID del cliente asociado (para filtros de acceso)'
    )
    
    # Datos del cambio
    datos_anteriores = models.JSONField(
        null=True,
        blank=True,
        help_text='Estado anterior del objeto (para UPDATE/DELETE)'
    )
    datos_nuevos = models.JSONField(
        null=True,
        blank=True,
        help_text='Nuevo estado del objeto (para CREATE/UPDATE)'
    )
    
    # Información adicional
    endpoint = models.CharField(
        max_length=255,
        blank=True,
        help_text='Endpoint de la API que procesó la acción'
    )
    metodo_http = models.CharField(
        max_length=10,
        blank=True,
        help_text='Método HTTP usado (POST, PUT, PATCH, DELETE)'
    )
    
    # Cuándo
    timestamp = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        help_text='Momento de la acción'
    )
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Log de Auditoría'
        verbose_name_plural = 'Logs de Auditoría'
        indexes = [
            models.Index(fields=['usuario', 'timestamp']),
            models.Index(fields=['modelo', 'objeto_id']),
            models.Index(fields=['cliente_id', 'timestamp']),
            models.Index(fields=['accion', 'timestamp']),
        ]
    
    def __str__(self):
        return f"{self.timestamp:%Y-%m-%d %H:%M} | {self.usuario_email} | {self.accion} | {self.modelo}"
    
    @classmethod
    def registrar(
        cls,
        request,
        accion,
        instancia=None,
        modelo=None,
        objeto_id=None,
        datos_anteriores=None,
        datos_nuevos=None,
        cliente_id=None,
        usuario=None,
        ip_address=None,
    ):
        """
        Registra una acción en el log de auditoría.
        
        Args:
            request: HttpRequest con usuario e info de cliente (puede ser None para Celery)
            accion: Tipo de acción (usar AccionAudit constants)
            instancia: Objeto afectado (opcional, extrae modelo/id/repr)
            modelo: Nombre del modelo (si no hay instancia)
            objeto_id: ID del objeto (si no hay instancia)
            datos_anteriores: Dict con estado previo
            datos_nuevos: Dict con nuevo estado
            cliente_id: ID del cliente (si no se puede extraer de instancia)
            usuario: Usuario directo (para llamadas desde Celery sin request)
            ip_address: IP del cliente (para llamadas desde Celery sin request)
        
        Returns:
            AuditLog creado
        """
        # Extraer info del request (puede ser None para Celery)
        if usuario is None and request:
            usuario = getattr(request, 'user', None)
            if usuario and not usuario.is_authenticated:
                usuario = None
        
        # ip_address puede venir como parámetro (desde Celery) o extraerse del request
        _ip_address = ip_address
        user_agent = ''
        endpoint = ''
        metodo_http = ''
        
        if request:
            if not _ip_address:
                _ip_address = cls._get_client_ip(request)
            user_agent = request.META.get('HTTP_USER_AGENT', '')[:500]
            endpoint = request.path
            metodo_http = request.method
        else:
            # Desde Celery, usar valores especiales
            endpoint = 'celery_task'
            metodo_http = 'ASYNC'
        
        # Extraer info de la instancia si existe
        objeto_repr = ''
        if instancia:
            modelo = f"{instancia._meta.app_label}.{instancia._meta.model_name}"
            objeto_id = instancia.pk
            objeto_repr = str(instancia)[:255]
            
            # Intentar extraer cliente_id
            if cliente_id is None:
                cliente_id = cls._extraer_cliente_id(instancia)
        
        return cls.objects.create(
            usuario=usuario,
            usuario_email=usuario.email if usuario else '',
            ip_address=_ip_address,
            user_agent=user_agent,
            accion=accion,
            modelo=modelo or '',
            objeto_id=objeto_id,
            objeto_repr=objeto_repr,
            cliente_id=cliente_id,
            datos_anteriores=datos_anteriores,
            datos_nuevos=datos_nuevos,
            endpoint=endpoint,
            metodo_http=metodo_http,
        )
    
    @staticmethod
    def _get_client_ip(request):
        """Extrae la IP del cliente considerando proxies."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR')
    
    @staticmethod
    def _extraer_cliente_id(instancia):
        """Intenta extraer el cliente_id de una instancia."""
        # Orden de búsqueda: cliente_id, cliente.id, cierre.cliente_id
        if hasattr(instancia, 'cliente_id') and instancia.cliente_id:
            return instancia.cliente_id
        if hasattr(instancia, 'cliente') and instancia.cliente:
            return instancia.cliente.id
        if hasattr(instancia, 'cierre') and instancia.cierre:
            return instancia.cierre.cliente_id
        return None
