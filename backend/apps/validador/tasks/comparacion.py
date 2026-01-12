"""
Celery Tasks para comparación y detección de discrepancias.
"""

from celery import shared_task
from django.utils import timezone
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def ejecutar_comparacion(self, cierre_id, usuario_id=None):
    """
    Ejecuta la comparación entre datos ERP y datos del Analista.
    
    1. Compara Libro vs Novedades
    2. Compara Movimientos ERP vs Movimientos Analista
    3. Genera Discrepancias
    4. Actualiza estado del cierre
    
    Args:
        cierre_id: ID del Cierre a procesar
        usuario_id: ID del usuario que inició la tarea (para auditoría)
    """
    from apps.validador.models import Cierre
    
    try:
        cierre = Cierre.objects.get(id=cierre_id)
        cierre.estado = 'comparacion'
        cierre.save()
        
        logger.info(f"Ejecutando comparación para cierre: {cierre}")
        
        # 1. Comparar Libro vs Novedades
        resultado_libro = _comparar_libro_novedades(cierre)
        
        # 2. Comparar Movimientos
        resultado_movimientos = _comparar_movimientos(cierre)
        
        # Actualizar contadores
        cierre.actualizar_contadores()
        
        # Determinar siguiente estado
        if cierre.total_discrepancias > 0:
            cierre.estado = 'con_discrepancias'
        else:
            cierre.estado = 'consolidado'
            cierre.fecha_consolidacion = timezone.now()
        
        cierre.save()
        
        logger.info(f"Comparación completada: {resultado_libro}, {resultado_movimientos}")
        return {
            'libro': resultado_libro,
            'movimientos': resultado_movimientos,
            'total_discrepancias': cierre.total_discrepancias,
        }
        
    except Exception as e:
        logger.error(f"Error en comparación del cierre {cierre_id}: {str(e)}")
        
        try:
            cierre = Cierre.objects.get(id=cierre_id)
            cierre.estado = 'error'
            cierre.save()
        except:
            pass
        
        raise self.retry(exc=e, countdown=60)


def _comparar_libro_novedades(cierre):
    """Compara el Libro de Remuneraciones con Novedades."""
    from apps.validador.models import (
        EmpleadoCierre,
        RegistroConcepto,
        RegistroNovedades,
        Discrepancia,
        ConceptoCliente,
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
    
    # Agrupar novedades por (rut, concepto_erp)
    novedades_por_empleado_concepto = {}
    for novedad in novedades_mapeadas:
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
    
    # Comparar
    tolerancia = Decimal('1')  # Tolerancia de $1 por redondeos
    
    # Items en novedades que no coinciden con libro
    for key, datos_novedad in novedades_por_empleado_concepto.items():
        rut, concepto_id = key
        datos_libro = libro_por_empleado_concepto.get(key)
        
        if not datos_libro:
            # El item está en novedades pero no en libro
            Discrepancia.objects.create(
                cierre=cierre,
                tipo='falta_en_erp',
                origen='libro_vs_novedades',
                rut_empleado=rut,
                nombre_empleado=datos_novedad['nombre_empleado'],
                concepto=datos_novedad['concepto'],
                monto_cliente=datos_novedad['monto'],
                descripcion=f"El item '{datos_novedad['concepto'].nombre_erp}' está en Novedades pero no en el Libro"
            )
            discrepancias_creadas += 1
            continue
        
        # Comparar montos
        diferencia = datos_libro['monto'] - datos_novedad['monto']
        if abs(diferencia) > tolerancia:
            discrepancia = Discrepancia.objects.create(
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
            discrepancia.save()
            discrepancias_creadas += 1
    
    # Items en libro que no están en novedades (que deberían estar)
    for key, datos_libro in libro_por_empleado_concepto.items():
        if key not in novedades_por_empleado_concepto:
            rut, concepto_id = key
            
            # Solo reportar si el concepto debería estar en novedades
            # (es decir, si el cliente normalmente informa este tipo de concepto)
            Discrepancia.objects.create(
                cierre=cierre,
                tipo='falta_en_cliente',
                origen='libro_vs_novedades',
                rut_empleado=rut,
                nombre_empleado=datos_libro['nombre_empleado'],
                concepto=datos_libro['concepto'],
                monto_erp=datos_libro['monto'],
                descripcion=f"El item '{datos_libro['concepto'].nombre_erp}' está en el Libro pero no en Novedades"
            )
            discrepancias_creadas += 1
    
    # Items sin mapear (generar discrepancia informativa)
    items_sin_mapear = RegistroNovedades.objects.filter(
        cierre=cierre,
        mapeo__isnull=True
    ).values('nombre_item').distinct()
    
    for item in items_sin_mapear:
        Discrepancia.objects.create(
            cierre=cierre,
            tipo='item_no_mapeado',
            origen='libro_vs_novedades',
            rut_empleado='N/A',
            nombre_item=item['nombre_item'],
            descripcion=f"El item '{item['nombre_item']}' de Novedades no tiene mapeo a ningún concepto del ERP"
        )
        discrepancias_creadas += 1
    
    return {'discrepancias': discrepancias_creadas}


def _comparar_movimientos(cierre):
    """Compara los movimientos del ERP con los del Analista."""
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
    
    # Obtener movimientos
    movimientos_erp = MovimientoMes.objects.filter(cierre=cierre)
    movimientos_analista = MovimientoAnalista.objects.filter(cierre=cierre)
    
    # Crear sets de (rut, tipo) para comparación rápida
    erp_set = {(m.rut, m.tipo) for m in movimientos_erp}
    analista_set = {(m.rut, m.tipo) for m in movimientos_analista}
    
    # Movimientos en ERP pero no en Analista
    for rut, tipo in erp_set - analista_set:
        mov = movimientos_erp.filter(rut=rut, tipo=tipo).first()
        Discrepancia.objects.create(
            cierre=cierre,
            tipo='falta_en_cliente',
            origen='movimientos_vs_analista',
            rut_empleado=rut,
            nombre_empleado=mov.nombre if mov else '',
            tipo_movimiento=tipo,
            descripcion=f"El movimiento '{tipo}' para {rut} está en ERP pero no en archivos del Analista"
        )
        discrepancias_creadas += 1
    
    # Movimientos en Analista pero no en ERP
    for rut, tipo in analista_set - erp_set:
        mov = movimientos_analista.filter(rut=rut, tipo=tipo).first()
        Discrepancia.objects.create(
            cierre=cierre,
            tipo='falta_en_erp',
            origen='movimientos_vs_analista',
            rut_empleado=rut,
            nombre_empleado=mov.nombre if mov else '',
            tipo_movimiento=tipo,
            descripcion=f"El movimiento '{tipo}' para {rut} está en archivos del Analista pero no en ERP"
        )
        discrepancias_creadas += 1
    
    return {'discrepancias': discrepancias_creadas}
