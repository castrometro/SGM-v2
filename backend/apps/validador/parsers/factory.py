"""
Factory para obtener el parser correcto según el ERP.

Usa patrón Factory para instanciar dinámicamente el parser adecuado.
"""

from typing import Type, Optional
import logging

from .base import BaseLibroParser

logger = logging.getLogger(__name__)


class ParserFactory:
    """
    Factory para obtener la instancia correcta de parser según el ERP.
    
    Los parsers se registran automáticamente mediante decorador @register.
    
    Uso:
        parser = ParserFactory.get_parser('talana')
        headers = parser.extraer_headers(archivo)
        result = parser.procesar_libro(archivo, conceptos)
    """
    
    _parsers: dict[str, Type[BaseLibroParser]] = {}
    
    @classmethod
    def register(cls, erp_codigo: str):
        """
        Decorador para registrar un parser.
        
        Args:
            erp_codigo: Código del ERP ('talana', 'buk', etc.)
        
        Uso:
            @ParserFactory.register('talana')
            class TalanaLibroParser(BaseLibroParser):
                ...
        """
        def decorator(parser_class: Type[BaseLibroParser]):
            if erp_codigo in cls._parsers:
                logger.warning(f"Sobrescribiendo parser existente para '{erp_codigo}'")
            
            cls._parsers[erp_codigo] = parser_class
            logger.debug(f"Registrado parser para ERP '{erp_codigo}': {parser_class.__name__}")
            return parser_class
        return decorator
    
    @classmethod
    def get_parser(cls, erp_codigo: str) -> BaseLibroParser:
        """
        Obtiene la instancia del parser para un ERP específico.
        
        Args:
            erp_codigo: Código del ERP (ej: 'talana', 'buk')
        
        Returns:
            Instancia de BaseLibroParser
        
        Raises:
            ValueError: Si el ERP no tiene parser registrado
        
        Examples:
            >>> parser = ParserFactory.get_parser('talana')
            >>> headers = parser.extraer_headers(archivo)
        """
        if erp_codigo not in cls._parsers:
            raise ValueError(
                f"No hay parser registrado para ERP '{erp_codigo}'. "
                f"Disponibles: {list(cls._parsers.keys())}"
            )
        
        parser_class = cls._parsers[erp_codigo]
        return parser_class()
    
    @classmethod
    def get_parser_for_cliente(cls, cliente) -> Optional[BaseLibroParser]:
        """
        Obtiene el parser según el ERP activo del cliente.
        
        Args:
            cliente: Instancia de Cliente
        
        Returns:
            BaseLibroParser o None si el cliente no tiene ERP configurado
        """
        # Obtener ERP activo del cliente
        config_erp = cliente.configuraciones_erp.filter(
            activo=True
        ).select_related('erp').first()
        
        if not config_erp or not config_erp.esta_vigente:
            logger.warning(f"Cliente {cliente} no tiene ERP configurado y vigente")
            return None
        
        erp_codigo = config_erp.erp.slug
        
        try:
            return cls.get_parser(erp_codigo)
        except ValueError as e:
            logger.error(f"Error obteniendo parser para cliente {cliente}: {e}")
            return None
    
    @classmethod
    def is_registered(cls, erp_codigo: str) -> bool:
        """
        Verifica si un ERP tiene parser registrado.
        
        Args:
            erp_codigo: Código del ERP
        
        Returns:
            True si está registrado
        """
        return erp_codigo in cls._parsers
    
    @classmethod
    def get_registered_erps(cls) -> list[str]:
        """
        Retorna lista de ERPs con parser registrado.
        
        Returns:
            Lista de códigos de ERP: ['talana', 'buk', ...]
        """
        return list(cls._parsers.keys())
    
    @classmethod
    def get_parser_class(cls, erp_codigo: str) -> Optional[Type[BaseLibroParser]]:
        """
        Obtiene la clase del parser (no instanciada).
        
        Args:
            erp_codigo: Código del ERP
        
        Returns:
            Clase del parser o None
        """
        return cls._parsers.get(erp_codigo)
