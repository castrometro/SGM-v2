"""
ERP Factory - Factory pattern para obtener estrategias de parseo de archivos.

Las estrategias se registran automáticamente mediante decorador @ERPFactory.register.

Uso:
    from apps.validador.services.erp import ERPFactory
    
    # Obtener estrategia para un ERP
    strategy = ERPFactory.get_strategy('talana')
    df = strategy.parse_archivo(file, 'libro_remuneraciones')
    
    # Con configuración del modelo ERP
    strategy = ERPFactory.get_strategy('talana', erp.configuracion_parseo)
    
    # Listar ERPs registrados
    slugs = ERPFactory.get_registered_slugs()
    
    # Verificar si un ERP está registrado
    if ERPFactory.is_registered('talana'):
        ...
"""

from typing import Type, Optional
import logging

from .base import ERPStrategy

logger = logging.getLogger(__name__)


class ERPFactory:
    """
    Factory para obtener la estrategia de parseo correcta según el ERP.
    
    Las estrategias se registran automáticamente mediante el decorador @register.
    Si un ERP no tiene estrategia registrada, se usa GenericStrategy como fallback.
    """
    
    _strategies: dict[str, Type[ERPStrategy]] = {}
    
    @classmethod
    def register(cls, slug: str):
        """
        Decorador para registrar una estrategia.
        
        Args:
            slug: Slug único del ERP
        
        Uso:
            @ERPFactory.register('talana')
            class TalanaStrategy(ERPStrategy):
                ...
        """
        def decorator(strategy_class: Type[ERPStrategy]):
            if slug in cls._strategies:
                logger.warning(f"Sobrescribiendo estrategia existente para '{slug}'")
            
            cls._strategies[slug] = strategy_class
            strategy_class.erp_slug = slug
            logger.debug(f"Registrada estrategia para ERP '{slug}': {strategy_class.__name__}")
            return strategy_class
        return decorator
    
    @classmethod
    def get_strategy(cls, erp_slug: str, config: dict = None) -> ERPStrategy:
        """
        Obtiene la estrategia para un ERP específico.
        
        Args:
            erp_slug: Slug del ERP (ej: 'talana', 'buk', 'sap')
            config: Configuración de parseo opcional (de ERP.configuracion_parseo)
        
        Returns:
            Instancia de ERPStrategy
        
        Raises:
            ValueError: Si el ERP no está registrado y no hay fallback genérico
        
        Examples:
            >>> strategy = ERPFactory.get_strategy('talana')
            >>> strategy = ERPFactory.get_strategy('buk', {'delimiter': ';'})
        """
        if erp_slug in cls._strategies:
            return cls._strategies[erp_slug](config)
        
        # Fallback a estrategia genérica si existe
        if 'generic' in cls._strategies:
            logger.info(f"ERP '{erp_slug}' no tiene estrategia específica, usando GenericStrategy")
            return cls._strategies['generic'](config)
        
        # No hay estrategia ni fallback
        raise ValueError(
            f"ERP '{erp_slug}' no tiene estrategia registrada. "
            f"Disponibles: {list(cls._strategies.keys())}"
        )
    
    @classmethod
    def get_strategy_for_cliente(cls, cliente) -> Optional[ERPStrategy]:
        """
        Obtiene la estrategia para el ERP activo de un cliente.
        
        Args:
            cliente: Instancia de Cliente
        
        Returns:
            ERPStrategy o None si el cliente no tiene ERP configurado
        """
        config_erp = cliente.configuraciones_erp.filter(
            activo=True
        ).select_related('erp').first()
        
        if not config_erp or not config_erp.esta_vigente:
            return None
        
        return cls.get_strategy(
            config_erp.erp.slug,
            config_erp.erp.configuracion_parseo
        )
    
    @classmethod
    def get_registered_slugs(cls) -> list[str]:
        """
        Retorna lista de slugs de ERPs registrados.
        
        Returns:
            Lista de slugs: ['talana', 'buk', 'generic', ...]
        """
        return list(cls._strategies.keys())
    
    @classmethod
    def is_registered(cls, erp_slug: str) -> bool:
        """
        Verifica si un ERP tiene estrategia registrada.
        
        Args:
            erp_slug: Slug del ERP
        
        Returns:
            True si está registrado
        """
        return erp_slug in cls._strategies
    
    @classmethod
    def get_strategy_class(cls, erp_slug: str) -> Optional[Type[ERPStrategy]]:
        """
        Obtiene la clase de estrategia (no instanciada).
        
        Args:
            erp_slug: Slug del ERP
        
        Returns:
            Clase de estrategia o None
        """
        return cls._strategies.get(erp_slug)
    
    @classmethod
    def get_all_strategies_info(cls) -> list[dict]:
        """
        Obtiene información de todas las estrategias registradas.
        
        Returns:
            Lista de dicts con info de cada estrategia
        """
        info = []
        for slug, strategy_class in cls._strategies.items():
            instance = strategy_class()
            info.append({
                'slug': slug,
                'nombre': instance.nombre_display or slug,
                'tipos_archivo': instance.get_tipos_archivo_soportados(),
            })
        return info
