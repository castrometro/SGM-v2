"""
Celery Tasks para procesamiento del Libro de Remuneraciones.

Tareas:
- extraer_headers_libro: Extracción rápida de headers (2-5s)
- procesar_libro_remuneraciones: Procesamiento completo con progreso (30s-5min)
"""

import logging
from celery import shared_task
from celery.exceptions import SoftTimeLimitExceeded
from django.core.cache import cache

from shared.audit import audit_action_celery
from apps.core.constants import AccionAudit

logger = logging.getLogger(__name__)


@shared_task(bind=True, name='validador.extraer_headers_libro', soft_time_limit=60, time_limit=90)
def extraer_headers_libro(self, archivo_erp_id: int, usuario_id: int = None):
    """
    Tarea Celery para extraer headers del Libro de Remuneraciones.
    
    Esta es una tarea rápida (2-5 segundos) que lee solo la fila de headers
    del Excel y crea/actualiza los ConceptoLibro correspondientes.
    
    Args:
        archivo_erp_id: ID del ArchivoERP
        usuario_id: ID del usuario que inició la tarea (para auditoría)
    
    Timeouts:
        soft_time_limit: 1 min (warning)
        time_limit: 1.5 min (kill)
    
    Returns:
        dict con:
            - success: bool
            - headers: lista de headers
            - headers_total: cantidad de headers
            - headers_clasificados: cantidad clasificados
            - error: mensaje si hubo error
    """
    from apps.validador.models import ArchivoERP
    from apps.validador.services import LibroService
    
    try:
        logger.info(f"[Task {self.request.id}] Iniciando extracción de headers para archivo {archivo_erp_id}")
        
        # Obtener archivo
        try:
            archivo_erp = ArchivoERP.objects.get(id=archivo_erp_id)
        except ArchivoERP.DoesNotExist:
            error_msg = f"ArchivoERP {archivo_erp_id} no encontrado"
            logger.error(f"[Task {self.request.id}] {error_msg}")
            return {'success': False, 'error': error_msg}
        
        # Guardar task_id
        archivo_erp.task_id = self.request.id
        archivo_erp.save(update_fields=['task_id'])
        
        # Extraer headers
        result = LibroService.extraer_headers(archivo_erp)
        
        if result.success:
            logger.info(
                f"[Task {self.request.id}] Headers extraídos exitosamente: "
                f"{len(result.data)} headers, {archivo_erp.headers_clasificados} clasificados"
            )
            
            return {
                'success': True,
                'headers': result.data,
                'headers_total': archivo_erp.headers_total,
                'headers_clasificados': archivo_erp.headers_clasificados,
                'progreso': archivo_erp.progreso_clasificacion,
            }
        else:
            logger.error(f"[Task {self.request.id}] Error extrayendo headers: {result.error}")
            return {
                'success': False,
                'error': result.error
            }
    
    except Exception as e:
        logger.error(f"[Task {self.request.id}] Error inesperado: {e}", exc_info=True)
        return {
            'success': False,
            'error': f"Error inesperado: {str(e)}"
        }


@shared_task(bind=True, name='validador.procesar_libro_remuneraciones', soft_time_limit=600, time_limit=720)
def procesar_libro_remuneraciones(self, archivo_erp_id: int, usuario_id: int = None, ip_address: str = None):
    """
    Tarea Celery para procesar el Libro de Remuneraciones completo.
    
    Esta es una tarea pesada (30s - 5min) que lee todo el Excel, parsea
    cada empleado y crea los registros EmpleadoLibro en la BD.
    
    Actualiza el progreso en cache para polling desde el frontend.
    
    Args:
        archivo_erp_id: ID del ArchivoERP
        usuario_id: ID del usuario que inició la tarea (para auditoría)
        ip_address: IP del cliente que inició la tarea (para auditoría)
    
    Timeouts:
        soft_time_limit: 10 min (warning)
        time_limit: 12 min (kill)
    
    Returns:
        dict con:
            - success: bool
            - empleados_procesados: cantidad de empleados
            - total_filas: filas totales leídas
            - errores: cantidad de errores
            - warnings: lista de advertencias
            - error: mensaje si hubo error
    """
    from apps.validador.models import ArchivoERP
    from apps.validador.services import LibroService
    
    cache_key = f'libro_progreso_{archivo_erp_id}'
    
    def progress_callback(progreso: int, mensaje: str, empleados: int = 0):
        """Callback para actualizar progreso en cache."""
        _actualizar_progreso(cache_key, {
            'estado': 'procesando',
            'progreso': progreso,
            'empleados_procesados': empleados,
            'mensaje': mensaje
        })
    
    try:
        logger.info(f"[Task {self.request.id}] Iniciando procesamiento de libro para archivo {archivo_erp_id}")
        
        # Obtener archivo
        try:
            archivo_erp = ArchivoERP.objects.get(id=archivo_erp_id)
        except ArchivoERP.DoesNotExist:
            error_msg = f"ArchivoERP {archivo_erp_id} no encontrado"
            logger.error(f"[Task {self.request.id}] {error_msg}")
            return {'success': False, 'error': error_msg}
        
        # Guardar task_id
        archivo_erp.task_id = self.request.id
        archivo_erp.save(update_fields=['task_id'])
        
        # Inicializar progreso en cache
        _actualizar_progreso(cache_key, {
            'estado': 'procesando',
            'progreso': 0,
            'empleados_procesados': 0,
            'mensaje': 'Iniciando procesamiento...'
        })
        
        # Procesar libro con callback de progreso
        result = LibroService.procesar_libro(archivo_erp, progress_callback=progress_callback)
        
        if result.success:
            # Actualizar progreso: completado
            _actualizar_progreso(cache_key, {
                'estado': 'completado',
                'progreso': 100,
                'empleados_procesados': result.data['empleados_procesados'],
                'mensaje': 'Procesamiento completado exitosamente'
            })
            
            # Registrar auditoría del procesamiento exitoso
            audit_action_celery(
                usuario_id=usuario_id,
                accion=AccionAudit.PROCESAR,
                instancia=archivo_erp,
                datos_anteriores={'estado': 'listo'},
                extra={
                    'estado': 'procesado',
                    'empleados_procesados': result.data['empleados_procesados'],
                    'total_filas': result.data['total_filas'],
                    'errores': result.data['errores'],
                },
                ip_address=ip_address,
            )
            
            logger.info(
                f"[Task {self.request.id}] Libro procesado exitosamente: "
                f"{result.data['empleados_procesados']} empleados de {result.data['total_filas']} filas"
            )
            
            return {
                'success': True,
                'empleados_procesados': result.data['empleados_procesados'],
                'total_filas': result.data['total_filas'],
                'errores': result.data['errores'],
                'warnings': result.data['warnings'],
            }
        else:
            # Actualizar progreso: error
            _actualizar_progreso(cache_key, {
                'estado': 'error',
                'progreso': 0,
                'mensaje': result.error
            })
            
            logger.error(f"[Task {self.request.id}] Error procesando libro: {result.error}")
            return {
                'success': False,
                'error': result.error
            }
    
    except Exception as e:
        logger.error(f"[Task {self.request.id}] Error inesperado: {e}", exc_info=True)
        
        # Actualizar progreso: error
        _actualizar_progreso(cache_key, {
            'estado': 'error',
            'progreso': 0,
            'mensaje': f"Error inesperado: {str(e)}"
        })
        
        return {
            'success': False,
            'error': f"Error inesperado: {str(e)}"
        }
    
    finally:
        # Limpiar cache después de 1 hora
        cache.expire(cache_key, 3600)


def _actualizar_progreso(cache_key: str, data: dict):
    """
    Actualiza el progreso de procesamiento en cache.
    
    Args:
        cache_key: Clave de cache
        data: Datos de progreso a guardar
    """
    try:
        cache.set(cache_key, data, timeout=3600)  # 1 hora
    except Exception as e:
        logger.error(f"Error actualizando progreso en cache: {e}")


def obtener_progreso_libro(archivo_erp_id: int) -> dict:
    """
    Obtiene el progreso actual del procesamiento del libro desde cache.
    
    Args:
        archivo_erp_id: ID del ArchivoERP
    
    Returns:
        dict con información de progreso o None si no hay progreso en cache
    """
    cache_key = f'libro_progreso_{archivo_erp_id}'
    return cache.get(cache_key)
