"""
Celery Tasks para detección de incidencias.
"""

from celery import shared_task
from django.utils import timezone
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)

# Umbral de variación para detectar incidencias (30%)
UMBRAL_VARIACION = Decimal('30')


@shared_task(bind=True, max_retries=3)
def detectar_incidencias(self, cierre_id):
    """
    Detecta incidencias comparando totales con el mes anterior.
    
    Una incidencia se genera cuando la variación de un concepto
    supera el 30% respecto al mes anterior.
    
    Se excluyen:
    - Categoría "Informativos"
    - Categoría "Descuentos Legales"
    """
    from apps.validador.models import Cierre, Incidencia
    
    try:
        cierre = Cierre.objects.get(id=cierre_id)
        cierre.estado = 'deteccion_incidencias'
        cierre.save()
        
        logger.info(f"Detectando incidencias para cierre: {cierre}")
        
        # Verificar si es primer cierre
        if cierre.es_primer_cierre:
            cierre.estado = 'finalizado'
            cierre.fecha_finalizacion = timezone.now()
            cierre.save()
            logger.info("Primer cierre del cliente - sin incidencias que detectar")
            return {'incidencias': 0, 'mensaje': 'Primer cierre - sin mes anterior'}
        
        # Obtener cierre anterior
        cierre_anterior = cierre.get_cierre_anterior()
        if not cierre_anterior:
            cierre.estado = 'finalizado'
            cierre.fecha_finalizacion = timezone.now()
            cierre.save()
            logger.info("No hay cierre anterior finalizado")
            return {'incidencias': 0, 'mensaje': 'Sin cierre anterior finalizado'}
        
        # Ejecutar detección
        resultado = _detectar_incidencias_por_concepto(cierre, cierre_anterior)
        
        # Actualizar contadores y estado
        cierre.actualizar_contadores()
        
        if cierre.total_incidencias > 0:
            cierre.estado = 'revision_incidencias'
        else:
            cierre.estado = 'finalizado'
            cierre.fecha_finalizacion = timezone.now()
        
        cierre.save()
        
        logger.info(f"Detección completada: {resultado}")
        return resultado
        
    except Exception as e:
        logger.error(f"Error detectando incidencias en cierre {cierre_id}: {str(e)}")
        
        try:
            cierre = Cierre.objects.get(id=cierre_id)
            cierre.estado = 'error'
            cierre.save()
        except:
            pass
        
        raise self.retry(exc=e, countdown=60)


def _detectar_incidencias_por_concepto(cierre, cierre_anterior):
    """Detecta incidencias comparando totales por concepto."""
    from apps.validador.models import (
        Incidencia,
        ResumenConsolidado,
        ConceptoCliente,
        CategoriaConcepto,
        RegistroConcepto,
    )
    from django.db.models import Sum
    
    # Limpiar incidencias anteriores
    Incidencia.objects.filter(cierre=cierre).delete()
    
    # Categorías excluidas
    categorias_excluidas = ['informativos', 'descuentos_legales']
    
    # Obtener totales del mes actual por concepto
    totales_actual = RegistroConcepto.objects.filter(
        empleado__cierre=cierre
    ).exclude(
        concepto__categoria__codigo__in=categorias_excluidas
    ).values(
        'concepto_id',
        'concepto__nombre_erp',
        'concepto__categoria_id'
    ).annotate(
        total=Sum('monto')
    )
    
    # Crear dict de totales actuales
    dict_actual = {
        item['concepto_id']: {
            'total': item['total'] or Decimal('0'),
            'nombre': item['concepto__nombre_erp'],
            'categoria': item['concepto__categoria_id'],
        }
        for item in totales_actual
    }
    
    # Obtener totales del mes anterior
    totales_anterior = RegistroConcepto.objects.filter(
        empleado__cierre=cierre_anterior
    ).exclude(
        concepto__categoria__codigo__in=categorias_excluidas
    ).values('concepto_id').annotate(
        total=Sum('monto')
    )
    
    dict_anterior = {
        item['concepto_id']: item['total'] or Decimal('0')
        for item in totales_anterior
    }
    
    incidencias_creadas = 0
    
    # Comparar conceptos
    todos_conceptos = set(dict_actual.keys()) | set(dict_anterior.keys())
    
    for concepto_id in todos_conceptos:
        monto_actual = dict_actual.get(concepto_id, {}).get('total', Decimal('0'))
        monto_anterior = dict_anterior.get(concepto_id, Decimal('0'))
        
        # Calcular variación
        if monto_anterior != 0:
            variacion = ((monto_actual - monto_anterior) / abs(monto_anterior)) * 100
        elif monto_actual > 0:
            variacion = Decimal('100')  # Nuevo concepto
        else:
            continue  # Ambos son 0
        
        # Si la variación supera el umbral, crear incidencia
        if abs(variacion) > UMBRAL_VARIACION:
            try:
                concepto = ConceptoCliente.objects.get(id=concepto_id)
            except ConceptoCliente.DoesNotExist:
                continue
            
            if not concepto.categoria:
                continue
            
            Incidencia.objects.create(
                cierre=cierre,
                concepto=concepto,
                categoria=concepto.categoria,
                monto_mes_anterior=monto_anterior,
                monto_mes_actual=monto_actual,
                diferencia_absoluta=monto_actual - monto_anterior,
                variacion_porcentual=variacion,
            )
            incidencias_creadas += 1
    
    return {
        'incidencias': incidencias_creadas,
        'umbral': float(UMBRAL_VARIACION),
    }


@shared_task
def generar_consolidacion(cierre_id):
    """
    Genera los resúmenes consolidados después de que discrepancias = 0.
    """
    from apps.validador.models import (
        Cierre,
        ResumenConsolidado,
        ResumenCategoria,
        ResumenMovimientos,
        EmpleadoCierre,
        RegistroConcepto,
        MovimientoMes,
        CategoriaConcepto,
    )
    from django.db.models import Sum, Avg, Min, Max, Count
    
    cierre = Cierre.objects.get(id=cierre_id)
    
    # Limpiar resúmenes anteriores
    ResumenConsolidado.objects.filter(cierre=cierre).delete()
    ResumenCategoria.objects.filter(cierre=cierre).delete()
    ResumenMovimientos.objects.filter(cierre=cierre).delete()
    
    # Generar resumen por concepto
    totales_concepto = RegistroConcepto.objects.filter(
        empleado__cierre=cierre
    ).values(
        'concepto_id',
        'concepto__categoria_id'
    ).annotate(
        total=Sum('monto'),
        cantidad=Count('id'),
        promedio=Avg('monto'),
        minimo=Min('monto'),
        maximo=Max('monto'),
    )
    
    for item in totales_concepto:
        ResumenConsolidado.objects.create(
            cierre=cierre,
            categoria_id=item['concepto__categoria_id'],
            concepto_id=item['concepto_id'],
            total_monto=item['total'] or 0,
            cantidad_empleados=item['cantidad'] or 0,
            monto_promedio=item['promedio'] or 0,
            monto_minimo=item['minimo'] or 0,
            monto_maximo=item['maximo'] or 0,
        )
    
    # Generar resumen por categoría
    for categoria in CategoriaConcepto.objects.all():
        totales = ResumenConsolidado.objects.filter(
            cierre=cierre,
            categoria=categoria
        ).aggregate(
            total=Sum('total_monto'),
            conceptos=Count('id'),
            empleados=Sum('cantidad_empleados')
        )
        
        if totales['total']:
            ResumenCategoria.objects.create(
                cierre=cierre,
                categoria=categoria,
                total_monto=totales['total'] or 0,
                cantidad_conceptos=totales['conceptos'] or 0,
                cantidad_empleados_afectados=totales['empleados'] or 0,
            )
    
    # Generar resumen de movimientos
    for tipo in ['alta', 'baja', 'licencia', 'vacaciones', 'permiso', 'ausencia']:
        movimientos = MovimientoMes.objects.filter(cierre=cierre, tipo=tipo)
        
        if movimientos.exists():
            empleados = [
                {'rut': m.rut, 'nombre': m.nombre}
                for m in movimientos
            ]
            total_dias = sum(m.dias or 0 for m in movimientos)
            
            ResumenMovimientos.objects.create(
                cierre=cierre,
                tipo=tipo,
                cantidad=movimientos.count(),
                total_dias=total_dias,
                empleados=empleados,
            )
    
    logger.info(f"Consolidación generada para cierre {cierre_id}")
    return {'status': 'ok'}
