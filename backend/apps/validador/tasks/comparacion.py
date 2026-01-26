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
from django.db import models
from django.utils import timezone
from decimal import Decimal
from datetime import date
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
    
    Solo compara montos por empleado para elementos que están mapeados
    entre ambas tablas (ConceptoNovedades → ConceptoLibro).
    
    Detecta:
    - monto_diferente: El monto en Libro != monto en Novedades para mismo RUT+concepto
    """
    from apps.validador.models import (
        RegistroNovedades,
        RegistroLibro,
        Discrepancia,
    )
    
    # Limpiar discrepancias anteriores de este tipo
    Discrepancia.objects.filter(
        cierre=cierre,
        origen='libro_vs_novedades'
    ).delete()
    
    discrepancias_creadas = 0
    
    # Obtener registros de novedades CON mapeo completo
    # Solo los que tienen: concepto_novedades → concepto_libro
    novedades_mapeadas = RegistroNovedades.objects.filter(
        cierre=cierre,
        concepto_novedades__isnull=False,
        concepto_novedades__concepto_libro__isnull=False,
    ).select_related('concepto_novedades', 'concepto_novedades__concepto_libro')
    
    total_novedades = novedades_mapeadas.count()
    
    # Agrupar novedades por (rut, concepto_libro_id) - sumar si hay múltiples
    novedades_dict = {}
    for idx, nov in enumerate(novedades_mapeadas):
        if idx % 500 == 0 and total_novedades > 0:
            progreso = 10 + int((idx / total_novedades) * 20)
            _set_progreso(cierre_id, {
                'estado': 'comparando',
                'progreso': progreso,
                'fase': 'libro_vs_novedades',
                'mensaje': f'Procesando novedades: {idx}/{total_novedades}',
            })
        
        concepto_libro = nov.concepto_novedades.concepto_libro
        key = (nov.rut_empleado, concepto_libro.id)
        
        if key not in novedades_dict:
            novedades_dict[key] = {
                'monto': Decimal('0'),
                'nombre_empleado': nov.nombre_empleado,
                'concepto_nombre_libro': concepto_libro.header_original,
                'concepto_nombre_novedades': nov.concepto_novedades.header_original,
            }
        novedades_dict[key]['monto'] += Decimal(str(nov.monto))
    
    _set_progreso(cierre_id, {
        'estado': 'comparando',
        'progreso': 35,
        'fase': 'libro_vs_novedades',
        'mensaje': 'Cargando datos del libro...',
    })
    
    # Obtener registros del libro
    registros_libro = RegistroLibro.objects.filter(
        cierre=cierre
    ).select_related('empleado', 'concepto')
    
    # Crear diccionario del libro por (rut, concepto_libro_id)
    # Solo categorías comparables (no info_adicional ni ignorar)
    libro_dict = {}
    for reg in registros_libro:
        if reg.concepto.categoria in ('info_adicional', 'ignorar'):
            continue
        
        key = (reg.empleado.rut, reg.concepto_id)
        libro_dict[key] = {
            'monto': Decimal(str(reg.monto)),
            'nombre_empleado': reg.empleado.nombre,
            'concepto_nombre': reg.concepto.header_original,
        }
    
    _set_progreso(cierre_id, {
        'estado': 'comparando',
        'progreso': 45,
        'fase': 'libro_vs_novedades',
        'mensaje': 'Comparando montos...',
    })
    
    # Comparar solo los elementos que existen en AMBOS lados
    tolerancia = Decimal('1')  # Tolerancia de $1 por redondeos
    discrepancias_batch = []
    
    # Buscar keys que existen en ambos diccionarios
    keys_comunes = set(novedades_dict.keys()) & set(libro_dict.keys())
    
    for key in keys_comunes:
        rut, concepto_id = key
        datos_nov = novedades_dict[key]
        datos_libro = libro_dict[key]
        
        diferencia = datos_libro['monto'] - datos_nov['monto']
        
        if abs(diferencia) > tolerancia:
            discrepancia = Discrepancia(
                cierre=cierre,
                tipo='monto_diferente',
                origen='libro_vs_novedades',
                rut_empleado=rut,
                nombre_empleado=datos_libro['nombre_empleado'] or datos_nov['nombre_empleado'],
                nombre_item=datos_libro['concepto_nombre'],
                nombre_item_novedades=datos_nov['concepto_nombre_novedades'],
                monto_erp=datos_libro['monto'],
                monto_cliente=datos_nov['monto'],
                diferencia=diferencia,
            )
            discrepancia.generar_descripcion()
            discrepancias_batch.append(discrepancia)
            discrepancias_creadas += 1
    
    # Bulk create
    if discrepancias_batch:
        Discrepancia.objects.bulk_create(discrepancias_batch)
    
    logger.info(
        f"Comparación libro vs novedades cierre {cierre.id}: "
        f"{len(keys_comunes)} pares comparados, {discrepancias_creadas} discrepancias"
    )
    
    return {'discrepancias': discrepancias_creadas, 'pares_comparados': len(keys_comunes)}


def _comparar_movimientos(cierre, cierre_id):
    """
    Compara los movimientos del ERP con los del Analista.
    
    Conexiones:
    - ERP alta (Altas y Bajas) ↔ Analista alta (ingresos)
    - ERP baja (Altas y Bajas) ↔ Analista baja (finiquitos)
    - ERP licencia/permiso/ausencia/vacaciones (Ausentismos/Vacaciones) ↔ Analista (asistencias)
    
    Compara por RUT + tipo de movimiento.
    
    Detecta:
    - falta_en_cliente: Movimiento en ERP pero no en archivos Analista
    - falta_en_erp: Movimiento en archivos Analista pero no en ERP
    """
    from apps.validador.models import (
        MovimientoMes,
        MovimientoAnalista,
        Discrepancia,
    )
    
    # Limpiar discrepancias anteriores
    Discrepancia.objects.filter(
        cierre=cierre,
        origen='movimientos_vs_analista'
    ).delete()
    
    discrepancias_creadas = 0
    discrepancias_batch = []
    
    _set_progreso(cierre_id, {
        'estado': 'comparando',
        'progreso': 65,
        'fase': 'movimientos',
        'mensaje': 'Cargando movimientos ERP...',
    })
    
    # Obtener rango de fechas del mes del cierre
    año, mes = map(int, cierre.periodo.split('-'))
    from calendar import monthrange
    primer_dia = date(año, mes, 1)
    ultimo_dia = date(año, mes, monthrange(año, mes)[1])
    
    # Obtener movimientos del ERP
    movimientos_erp = MovimientoMes.objects.filter(cierre=cierre)
    
    # Crear dict de ERP: {(rut, tipo): movimiento}
    # Solo incluir movimientos cuya fecha_inicio esté en el mes del cierre
    # (para vacaciones/asistencia que pueden cruzar meses)
    erp_dict = {}
    movimientos_ignorados = 0
    for mov in movimientos_erp:
        # Para vacaciones y asistencia, filtrar por fecha_inicio en el mes
        if mov.tipo in ('vacaciones', 'asistencia') and mov.fecha_inicio:
            if mov.fecha_inicio < primer_dia or mov.fecha_inicio > ultimo_dia:
                movimientos_ignorados += 1
                continue
        
        key = (mov.rut, mov.tipo)
        # Si hay múltiples del mismo tipo para el mismo RUT, guardar el primero
        if key not in erp_dict:
            erp_dict[key] = mov
    
    if movimientos_ignorados:
        logger.info(
            f"Cierre {cierre.id}: Ignorados {movimientos_ignorados} movimientos ERP "
            f"con fecha_inicio fuera del mes {cierre.periodo}"
        )
    
    _set_progreso(cierre_id, {
        'estado': 'comparando',
        'progreso': 72,
        'fase': 'movimientos',
        'mensaje': 'Cargando movimientos Analista...',
    })
    
    # Obtener movimientos del Analista
    movimientos_analista = MovimientoAnalista.objects.filter(cierre=cierre)
    
    # Si no hay movimientos del analista, no hay nada que comparar
    if not movimientos_analista.exists():
        logger.info(f"Cierre {cierre.id}: Sin movimientos del analista para comparar")
        return {'discrepancias': 0, 'mensaje': 'Sin archivos de movimientos del analista'}
    
    # Crear dict de Analista: {(rut, tipo): movimiento}
    analista_dict = {}
    for mov in movimientos_analista:
        key = (mov.rut, mov.tipo)
        if key not in analista_dict:
            analista_dict[key] = mov
    
    _set_progreso(cierre_id, {
        'estado': 'comparando',
        'progreso': 80,
        'fase': 'movimientos',
        'mensaje': 'Comparando movimientos...',
    })
    
    erp_keys = set(erp_dict.keys())
    analista_keys = set(analista_dict.keys())
    
    # Movimientos en ERP que NO están en Analista
    solo_en_erp = erp_keys - analista_keys
    for key in solo_en_erp:
        rut, tipo = key
        mov = erp_dict[key]
        
        discrepancias_batch.append(Discrepancia(
            cierre=cierre,
            tipo='falta_en_cliente',
            origen='movimientos_vs_analista',
            rut_empleado=rut,
            nombre_empleado=mov.nombre,
            tipo_movimiento=tipo,
            descripcion=(
                f"El movimiento '{mov.get_tipo_display()}' para {rut} ({mov.nombre}) "
                f"está en ERP pero no fue reportado por el cliente"
            ),
            detalle_movimiento={
                'fecha_inicio': str(mov.fecha_inicio) if mov.fecha_inicio else None,
                'fecha_fin': str(mov.fecha_fin) if mov.fecha_fin else None,
                'dias': mov.dias,
                'hoja_origen': mov.hoja_origen,
            }
        ))
        discrepancias_creadas += 1
    
    # Movimientos en Analista que NO están en ERP
    solo_en_analista = analista_keys - erp_keys
    for key in solo_en_analista:
        rut, tipo = key
        mov = analista_dict[key]
        
        discrepancias_batch.append(Discrepancia(
            cierre=cierre,
            tipo='falta_en_erp',
            origen='movimientos_vs_analista',
            rut_empleado=rut,
            nombre_empleado=mov.nombre,
            tipo_movimiento=tipo,
            descripcion=(
                f"El movimiento '{mov.get_tipo_display()}' para {rut} ({mov.nombre}) "
                f"fue reportado por el cliente pero no está en ERP"
            ),
            detalle_movimiento={
                'fecha_inicio': str(mov.fecha_inicio) if mov.fecha_inicio else None,
                'fecha_fin': str(mov.fecha_fin) if mov.fecha_fin else None,
                'dias': mov.dias,
                'origen': mov.origen,
            }
        ))
        discrepancias_creadas += 1
    
    # Bulk create
    if discrepancias_batch:
        Discrepancia.objects.bulk_create(discrepancias_batch)
    
    logger.info(
        f"Comparación movimientos cierre {cierre.id}: "
        f"ERP={len(erp_keys)}, Analista={len(analista_keys)}, "
        f"solo_erp={len(solo_en_erp)}, solo_analista={len(solo_en_analista)}"
    )
    
    return {
        'discrepancias': discrepancias_creadas,
        'movimientos_erp': len(erp_keys),
        'movimientos_analista': len(analista_keys),
    }
