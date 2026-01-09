"""
Services Layer - Lógica de negocio centralizada.

Este módulo contiene todos los servicios de negocio de la aplicación.
Los servicios encapsulan la lógica de negocio separándola de las views
y los modelos.

Uso:
    from apps.validador.services import CierreService, ArchivoService
    from apps.validador.constants import EstadoCierre
    
    # Cambiar estado de un cierre
    result = CierreService.cambiar_estado(cierre, EstadoCierre.CONSOLIDADO, user)
    if result.success:
        cierre_actualizado = result.data
    else:
        error_message = result.error
    
    # Subir archivo
    result = ArchivoService.subir_archivo_erp(cierre, archivo, 'libro_remuneraciones', user)
    
    # Resolver incidencia
    result = IncidenciaService.resolver(incidencia, 'aprobar', user, 'Justificación válida')

Patrón ServiceResult:
    Todos los servicios retornan ServiceResult que contiene:
    - success: bool indicando éxito/fallo
    - data: datos retornados (si success=True)
    - error: mensaje de error (si success=False)
    - errors: dict con múltiples errores de validación

ERP Factory/Strategy:
    from apps.validador.services.erp import ERPFactory
    
    strategy = ERPFactory.get_strategy('talana')
    result = strategy.parse_archivo(file, 'libro_remuneraciones')
"""

from .base import BaseService, ServiceResult
from .cierre_service import CierreService
from .archivo_service import ArchivoService
from .incidencia_service import IncidenciaService
from .equipo_service import EquipoService
from .libro_service import LibroService

# ERP Factory/Strategy
from .erp import ERPFactory, ERPStrategy, ParseResult, FormatoEsperado


__all__ = [
    # Base
    'BaseService',
    'ServiceResult',
    
    # Servicios
    'CierreService',
    'ArchivoService',
    'IncidenciaService',
    'EquipoService',
    'LibroService',
    
    # ERP Factory/Strategy
    'ERPFactory',
    'ERPStrategy',
    'ParseResult',
    'FormatoEsperado',
]
