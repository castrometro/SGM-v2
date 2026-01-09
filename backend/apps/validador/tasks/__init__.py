"""
Celery Tasks del app Validador.
"""

from .procesar_erp import procesar_archivo_erp
from .procesar_analista import procesar_archivo_analista
from .comparacion import ejecutar_comparacion
from .incidencias import detectar_incidencias, generar_consolidacion
from .libro import extraer_headers_libro, procesar_libro_remuneraciones, obtener_progreso_libro

__all__ = [
    'procesar_archivo_erp',
    'procesar_archivo_analista',
    'ejecutar_comparacion',
    'detectar_incidencias',
    'generar_consolidacion',
    'extraer_headers_libro',
    'procesar_libro_remuneraciones',
    'obtener_progreso_libro',
]
