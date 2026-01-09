"""
Base Service - Clase base para todos los servicios.

Define patrones comunes para manejo de errores, logging y respuestas.
"""

import logging
from dataclasses import dataclass
from typing import Any, Optional, TypeVar, Generic
from django.db import transaction


T = TypeVar('T')


@dataclass
class ServiceResult(Generic[T]):
    """
    Resultado estándar de operaciones de servicio.
    
    Uso:
        from apps.validador.constants import EstadoCierre
        
        result = CierreService.cambiar_estado(cierre, EstadoCierre.CONSOLIDADO)
        if result.success:
            print(result.data)
        else:
            print(result.error)
    """
    success: bool
    data: Optional[T] = None
    error: Optional[str] = None
    errors: Optional[dict] = None  # Para múltiples errores de validación
    
    @classmethod
    def ok(cls, data: T = None) -> 'ServiceResult[T]':
        """Crear resultado exitoso."""
        return cls(success=True, data=data)
    
    @classmethod
    def fail(cls, error: str, errors: dict = None) -> 'ServiceResult[T]':
        """Crear resultado fallido."""
        return cls(success=False, error=error, errors=errors)


class BaseService:
    """
    Clase base para servicios de negocio.
    
    Proporciona:
    - Logger configurado
    - Manejo de transacciones
    - Patrones de respuesta estandarizados
    """
    
    @classmethod
    def get_logger(cls) -> logging.Logger:
        """Obtener logger para el servicio."""
        return logging.getLogger(f'services.{cls.__name__}')
    
    @classmethod
    def atomic(cls):
        """Decorador/context manager para transacciones."""
        return transaction.atomic()
    
    @classmethod
    def log_action(cls, action: str, entity_type: str, entity_id: Any, 
                   user=None, extra: dict = None):
        """
        Registrar acción para auditoría.
        
        Args:
            action: Tipo de acción (create, update, delete, etc.)
            entity_type: Tipo de entidad (cierre, archivo, etc.)
            entity_id: ID de la entidad
            user: Usuario que realiza la acción
            extra: Datos adicionales
        """
        logger = cls.get_logger()
        
        log_data = {
            'action': action,
            'entity_type': entity_type,
            'entity_id': entity_id,
            'user_id': user.id if user else None,
            'user_email': user.email if user else None,
        }
        
        if extra:
            log_data.update(extra)
        
        logger.info(f"[{action.upper()}] {entity_type}:{entity_id}", extra=log_data)
    
    @classmethod
    def validate_required(cls, data: dict, required_fields: list) -> Optional[dict]:
        """
        Validar campos requeridos.
        
        Returns:
            None si es válido, dict con errores si no.
        """
        errors = {}
        for field in required_fields:
            if field not in data or data[field] is None:
                errors[field] = 'Este campo es requerido.'
        
        return errors if errors else None
