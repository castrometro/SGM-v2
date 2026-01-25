"""
Celery Tasks para comparación y detección de discrepancias.

Compara datos ERP vs datos del Analista:
1. Libro de Remuneraciones vs Novedades (montos)
2. Movimientos del Mes vs Archivos Analista (ingresos, finiquitos, etc.)

Reporta progreso a cache para polling desde frontend.
"""

from celery import shared_task
from celery.exceptions import SoftTimeLimitExceeded
from django.core.cache import cache
from django.utils import timezone
from decimal import Decimal
import logging

from apps.validador.constants import EstadoCierre

logger = logging.getLogger(__name__)

# Prefijo para keys de cache de progreso
CACHE_PREFIX_COMPARACION = 'comparacion_progreso_'
CACHE_TIMEOUT = 600  # 10 minutos


def _set_progreso(cierre_id: int, data: dict):
    """Guarda progreso de comparación en cache."""
    cache.set(f'{CACHE_PREFIX_COMPARACION}{cierre_id}', data, CACHE_TIMEOUT)


def get_progreso_comparacion(cierre_id: int) -> dict:
    """Obtiene progreso de comparación desde cache."""
    return cache.get(f'{CACHE_PREFIX_COMPARACION}{cierre_id}', {
        'estado': 'pendiente',
        'progreso': 0,
        'mensaje': 'Esperando...',
    })


@shared_task(bind=True, max_retries=2, soft_time_limit=600, time_limit=720)
def ejecutar_comparacion(self, cierre_id, usuario_id=None):
    """
    Ejecuta la comparación entre datos ERP y datos del Analista.
    
    Fases:
    1. Preparación (10%)
    2. Comparar Libro vs Novedades (10-60%)
    3. Comparar Movimientos (60-90%)
    4. Finalización (90-100%)
    
    Args:
        cierre_id: ID del Cierre a procesar
        usuario_id: ID del usuario que inició la tarea (para auditoría)
    
    Timeouts:
        soft_time_limit: 10 min (warning)
        time_limit: 12 min (kill)
    """
    from apps.validador.models import Cierre
    
    try:
        cierre = Cierre.objects.get(id=cierre_id)
        
        # Cambiar a estado COMPARANDO
        cierre.estado = EstadoCierre.COMPARANDO
        cierre.save(update_fields=['estado'])
        
        logger.info(f"Iniciando comparación para cierre ID={cierre_id}")
        
        # Fase 1: Preparación
        _set_progreso(cierre_id, {
            'estado': 'comparando',
            'progreso': 5,
            'fase': 'preparacion',
            'mensaje': 'Preparando datos para comparación...',
        })
        
        # Fase 2: Comparar Libro vs Novedades (10-60%)
        _set_progreso(cierre_id, {
            'estado': 'comparando',
            'progreso': 10,
            'fase': 'libro_vs_novedades',
            'mensaje': 'Comparando Libro vs Novedades...',
        })
        
        resultado_libro = _comparar_libro_novedades(cierre, cierre_id)
        
        _set_progreso(cierre_id, {
            'estado': 'comparando',
            'progreso': 60,
            'fase': 'libro_vs_novedades',
            'mensaje': f'Libro vs Novedades: {resultado_libro["discrepancias"]} discrepancias',
        })
        
        # Fase 3: Comparar Movimientos (60-90%)
        _set_progreso(cierre_id, {
            'estado': 'comparando',
            'progreso': 65,
            'fase': 'movimientos',
            'mensaje': 'Comparando Movimientos ERP vs Analista...',
        })
        
        resultado_movimientos = _comparar_movimientos(cierre, cierre_id)
        
        _set_progreso(cierre_id, {
            'estado': 'comparando',
            'progreso': 90,
            'fase': 'movimientos',
            'mensaje': f'Movimientos: {resultado_movimientos["discrepancias"]} discrepancias',
        })
        
        # Fase 4: Finalización
        _set_progreso(cierre_id, {
            'estado': 'comparando',
            'progreso': 95,
            'fase': 'finalizando',
            'mensaje': 'Actualizando contadores...',
        })
        
        # Actualizar contadores
        cierre.actualizar_contadores()
        
        # Determinar siguiente estado
        total_discrepancias = resultado_libro['discrepancias'] + resultado_movimientos['discrepancias']
        
        if total_discrepancias > 0:
            nuevo_estado = EstadoCierre.CON_DISCREPANCIAS
        else:
            nuevo_estado = EstadoCierre.SIN_DISCREPANCIAS
        
        cierre.estado = nuevo_estado
        cierre.save(update_fields=['estado'])
        
        # Progreso final
        _set_progreso(cierre_id, {
            'estado': 'completado',
            'progreso': 100,
            'fase': 'completado',
            'mensaje': f'Comparación completada: {total_discrepancias} discrepancias encontradas',
            'resultado': {
                'total_discrepancias': total_discrepancias,
                'libro_vs_novedades': resultado_libro['discrepancias'],
                'movimientos': resultado_movimientos['discrepancias'],
                'nuevo_estado': nuevo_estado,
            }
        })
        
        logger.info(
            f"Comparación completada cierre ID={cierre_id}: "
            f"libro={resultado_libro['discrepancias']}, mov={resultado_movimientos['discrepancias']}"
        )
        
        return {
            'libro': resultado_libro,
            'movimientos': resultado_movimientos,
            'total_discrepancias': total_discrepancias,
            'nuevo_estado': nuevo_estado,
        }
        
    except SoftTimeLimitExceeded:
        logger.warning(f"Timeout suave en comparación del cierre {cierre_id}")
        _set_progreso(cierre_id, {
            'estado': 'error',
            'progreso': 0,
            'mensaje': 'La comparación está tomando más tiempo del esperado. Reintentando...',
        })
        raise
        
    except Exception as e:
        logger.error(f"Error en comparación del cierre {cierre_id}: {str(e)}")
        
        _set_progreso(cierre_id, {
            'estado': 'error',
            'progreso': 0,
            'mensaje': f'Error: {str(e)}',
        })
        
        try:
            cierre = Cierre.objects.get(id=cierre_id)
            cierre.estado = EstadoCierre.ERROR
            cierre.save(update_fields=['estado'])
        except Exception:
            logger.exception(f"No se pudo actualizar estado de error del cierre {cierre_id}")
        
        raise self.retry(exc=e, countdown=60)


def _comparar_libro_novedades(cierre, cierre_id):
    """
    Compara el Libro de Remuneraciones con Novedades.
    
    Detecta:
    - monto_diferente: El monto en Libro != monto en Novedades
    - falta_en_erp: Item en Novedades pero no en Libro
    - falta_en_cliente: Item en Libro pero no en Novedades
    - item_no_mapeado: Item en Novedades sin mapeo a concepto ERP
    """
    from apps.validador.models import (
        RegistroConcepto,
        RegistroNovedades,
        Discrepancia,
    )
    
    # Limpiar discrepancias anteriores de este tipo
    Discrepancia.objects.filter(
        cierre=cierre,
        origen='libro_vs_novedades'
    ).delete()
    
    discrepancias_creadas = 0
    
    # Obtener todos los registros de novedades con mapeo
    novedades_mapeadas = RegistroNovedades.objects.filter(
        cierre=cierre,
        mapeo__isnull=False
    ).select_related('mapeo', 'mapeo__concepto_erp')
    
    total_novedades = novedades_mapeadas.count()
    
    # Agrupar novedades por (rut, concepto_erp)
    novedades_por_empleado_concepto = {}
    for idx, novedad in enumerate(novedades_mapeadas):
        # Actualizar progreso cada 100 registros
        if idx % 100 == 0 and total_novedades > 0:
            progreso = 10 + int((idx / total_novedades) * 20)  # 10-30%
            _set_progreso(cierre_id, {
                'estado': 'comparando',
                'progreso': progreso,
                'fase': 'libro_vs_novedades',
                'mensaje': f'Procesando novedades: {idx}/{total_novedades}',
            })
        
        key = (novedad.rut_empleado, novedad.mapeo.concepto_erp_id)
        if key not in novedades_por_empleado_concepto:
            novedades_por_empleado_concepto[key] = {
                'monto': Decimal('0'),
                'nombre_empleado': novedad.nombre_empleado,
                'concepto': novedad.mapeo.concepto_erp,
            }
        novedades_por_empleado_concepto[key]['monto'] += Decimal(str(novedad.monto))
    
    # Obtener registros del libro (solo conceptos que se comparan)
    registros_libro = RegistroConcepto.objects.filter(
        empleado__cierre=cierre
    ).select_related('empleado', 'concepto', 'concepto__categoria')
    
    # Crear diccionario de libro por (rut, concepto)
    libro_por_empleado_concepto = {}
    for registro in registros_libro:
        # Verificar si el concepto se compara
        if not registro.concepto.se_compara:
            continue
        
        key = (registro.empleado.rut, registro.concepto_id)
        libro_por_empleado_concepto[key] = {
            'monto': Decimal(str(registro.monto)),
            'nombre_empleado': registro.empleado.nombre,
            'concepto': registro.concepto,
        }
    
    _set_progreso(cierre_id, {
        'estado': 'comparando',
        'progreso': 35,
        'fase': 'libro_vs_novedades',
        'mensaje': 'Comparando montos...',
    })
    
    # Comparar
    tolerancia = Decimal('1')  # Tolerancia de $1 por redondeos
    discrepancias_batch = []
    
    # Items en novedades que no coinciden con libro
    for key, datos_novedad in novedades_por_empleado_concepto.items():
        rut, concepto_id = key
        datos_libro = libro_por_empleado_concepto.get(key)
        
        if not datos_libro:
            # El item está en novedades pero no en libro
            discrepancias_batch.append(Discrepancia(
                cierre=cierre,
                tipo='falta_en_erp',
                origen='libro_vs_novedades',
                rut_empleado=rut,
                nombre_empleado=datos_novedad['nombre_empleado'],
                concepto=datos_novedad['concepto'],
                monto_cliente=datos_novedad['monto'],
                descripcion=f"El item '{datos_novedad['concepto'].nombre_erp}' está en Novedades pero no en el Libro"
            ))
            discrepancias_creadas += 1
            continue
        
        # Comparar montos
        diferencia = datos_libro['monto'] - datos_novedad['monto']
        if abs(diferencia) > tolerancia:
            discrepancia = Discrepancia(
                cierre=cierre,
                tipo='monto_diferente',
                origen='libro_vs_novedades',
                rut_empleado=rut,
                nombre_empleado=datos_libro['nombre_empleado'],
                concepto=datos_libro['concepto'],
                monto_erp=datos_libro['monto'],
                monto_cliente=datos_novedad['monto'],
                diferencia=diferencia,
            )
            discrepancia.generar_descripcion()
            discrepancias_batch.append(discrepancia)
            discrepancias_creadas += 1
    
    _set_progreso(cierre_id, {
        'estado': 'comparando',
        'progreso': 45,
        'fase': 'libro_vs_novedades',
        'mensaje': 'Verificando items faltantes...',
    })
    
    # Items en libro que no están en novedades (que deberían estar)
    for key, datos_libro in libro_por_empleado_concepto.items():
        if key not in novedades_por_empleado_concepto:
            rut, concepto_id = key
            
            discrepancias_batch.append(Discrepancia(
                cierre=cierre,
                tipo='falta_en_cliente',
                origen='libro_vs_novedades',
                rut_empleado=rut,
                nombre_empleado=datos_libro['nombre_empleado'],
                concepto=datos_libro['concepto'],
                monto_erp=datos_libro['monto'],
                descripcion=f"El item '{datos_libro['concepto'].nombre_erp}' está en el Libro pero no en Novedades"
            ))
            discrepancias_creadas += 1
    
    # Items sin mapear (generar discrepancia informativa)
    items_sin_mapear = RegistroNovedades.objects.filter(
        cierre=cierre,
        mapeo__isnull=True
    ).values('nombre_item').distinct()
    
    for item in items_sin_mapear:
        discrepancias_batch.append(Discrepancia(
            cierre=cierre,
            tipo='item_no_mapeado',
            origen='libro_vs_novedades',
            rut_empleado='N/A',
            nombre_item=item['nombre_item'],
            descripcion=f"El item '{item['nombre_item']}' de Novedades no tiene mapeo a ningún concepto del ERP"
        ))
        discrepancias_creadas += 1
    
    # Bulk create para mejor performance
    if discrepancias_batch:
        Discrepancia.objects.bulk_create(discrepancias_batch)
    
    return {'discrepancias': discrepancias_creadas}


def _comparar_movimientos(cierre, cierre_id):
    """
    Compara los movimientos del ERP con los del Analista.
    
    Detecta:
    - falta_en_cliente: Movimiento en ERP pero no en archivos Analista
    - falta_en_erp: Movimiento en archivos Analista pero no en ERP
    """
    from apps.validador.models import (
        MovimientoMes,
        Discrepancia,
    )
    from apps.validador.models.archivo import ArchivoAnalista
    
    # Limpiar discrepancias anteriores
    Discrepancia.objects.filter(
        cierre=cierre,
        origen='movimientos_vs_analista'
    ).delete()
    
    discrepancias_creadas = 0
    discrepancias_batch = []
    
    # Obtener movimientos del ERP
    movimientos_erp = MovimientoMes.objects.filter(cierre=cierre)
    
    _set_progreso(cierre_id, {
        'estado': 'comparando',
        'progreso': 70,
        'fase': 'movimientos',
        'mensaje': f'Procesando {movimientos_erp.count()} movimientos ERP...',
    })
    
    # Obtener archivos analista procesados (ingresos, finiquitos, asistencias)
    # Cada archivo tiene registros de movimientos que debemos comparar
    archivos_analista = ArchivoAnalista.objects.filter(
        cierre=cierre,
        estado='procesado'
    ).exclude(tipo='novedades')  # Novedades se compara aparte
    
    # Crear set de movimientos del analista: (rut, tipo_movimiento)
    analista_set = set()
    analista_data = {}  # Para guardar datos del movimiento
    
    for archivo in archivos_analista:
        # Mapear tipo de archivo a tipo de movimiento
        tipo_map = {
            'ingresos': 'alta',
            'finiquitos': 'baja',
            'asistencias': 'ausencia',  # Simplificado
        }
        tipo_mov = tipo_map.get(archivo.tipo, archivo.tipo)
        
        # Los datos procesados están en los movimientos del analista
        # Por ahora usamos los registros que ya existen
        # TODO: Implementar MovimientoAnalista si no existe
    
    _set_progreso(cierre_id, {
        'estado': 'comparando',
        'progreso': 80,
        'fase': 'movimientos',
        'mensaje': 'Comparando movimientos...',
    })
    
    # Crear sets de (rut, tipo) para comparación rápida desde ERP
    erp_set = {(m.rut, m.tipo) for m in movimientos_erp}
    erp_data = {(m.rut, m.tipo): m for m in movimientos_erp}
    
    # Por ahora, solo reportamos movimientos del ERP que podrían no tener respaldo
    # La comparación completa requiere que el analista suba archivos de ingresos/finiquitos
    
    # Si no hay archivos de analista procesados (excepto novedades), 
    # no generamos discrepancias de movimientos
    if not archivos_analista.exists():
        logger.info(f"Cierre {cierre.id}: Sin archivos de movimientos del analista para comparar")
        return {'discrepancias': 0}
    
    # Movimientos en ERP pero no en Analista
    for (rut, tipo), mov in erp_data.items():
        if (rut, tipo) not in analista_set:
            discrepancias_batch.append(Discrepancia(
                cierre=cierre,
                tipo='falta_en_cliente',
                origen='movimientos_vs_analista',
                rut_empleado=rut,
                nombre_empleado=mov.nombre if mov else '',
                tipo_movimiento=tipo,
                descripcion=f"El movimiento '{tipo}' para empleado está en ERP pero no fue reportado por el Analista"
            ))
            discrepancias_creadas += 1
    
    # Movimientos en Analista pero no en ERP
    for (rut, tipo) in analista_set - erp_set:
        data = analista_data.get((rut, tipo), {})
        discrepancias_batch.append(Discrepancia(
            cierre=cierre,
            tipo='falta_en_erp',
            origen='movimientos_vs_analista',
            rut_empleado=rut,
            nombre_empleado=data.get('nombre', ''),
            tipo_movimiento=tipo,
            descripcion=f"El movimiento '{tipo}' fue reportado por el Analista pero no está en ERP"
        ))
        discrepancias_creadas += 1
    
    # Bulk create
    if discrepancias_batch:
        Discrepancia.objects.bulk_create(discrepancias_batch)
    
    return {'discrepancias': discrepancias_creadas}
