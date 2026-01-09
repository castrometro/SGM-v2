"""
Parsers para procesar archivos del Libro de Remuneraciones.

Este paquete contiene los parsers específicos para cada ERP que procesan
el Libro de Remuneraciones y extraen los datos de empleados.
"""

from .base import BaseLibroParser, ProcessResult
from .factory import ParserFactory

# Importar parsers para auto-registro
from . import talana  # noqa: F401

__all__ = [
    'BaseLibroParser',
    'ProcessResult',
    'ParserFactory',
]
