"""
ERP Services Package - Factory y Strategies para procesamiento de archivos ERP.

Este paquete implementa los patrones Factory y Strategy para manejar
diferentes formatos de archivos según el sistema ERP del cliente.

Uso básico:
    from apps.validador.services.erp import ERPFactory
    
    # Obtener estrategia para un ERP
    strategy = ERPFactory.get_strategy('talana')
    result = strategy.parse_archivo(file, 'libro_remuneraciones')
    
    if result.success:
        df = result.data  # DataFrame normalizado
    else:
        error = result.error

    # Obtener estrategia para el cliente
    strategy = ERPFactory.get_strategy_for_cliente(cliente)

    # Listar ERPs disponibles
    erps = ERPFactory.get_registered_slugs()  # ['talana', 'buk', 'sap', 'generic']

Estrategias disponibles:
    - TalanaStrategy: Archivos de Talana
    - BukStrategy: Archivos de BUK
    - SAPStrategy: Archivos de SAP HCM
    - GenericStrategy: Fallback para ERPs sin implementación específica

Agregar nuevo ERP:
    1. Crear archivo {erp_slug}.py en este directorio
    2. Heredar de ERPStrategy
    3. Decorar la clase con @ERPFactory.register('{erp_slug}')
    4. Implementar métodos abstractos
    5. Importar en este __init__.py
"""

from .base import ERPStrategy, ParseResult, FormatoEsperado
from .factory import ERPFactory

# Importar estrategias para que se registren automáticamente
from .talana import TalanaStrategy
from .buk import BukStrategy
from .sap import SAPStrategy
from .generic import GenericStrategy

__all__ = [
    # Base
    'ERPStrategy',
    'ParseResult',
    'FormatoEsperado',
    
    # Factory
    'ERPFactory',
    
    # Strategies
    'TalanaStrategy',
    'BukStrategy',
    'SAPStrategy',
    'GenericStrategy',
]
