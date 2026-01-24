"""
Celery Tasks para procesamiento de Archivos ERP.
"""

from celery import shared_task
from celery.exceptions import SoftTimeLimitExceeded
from django.conf import settings
from django.utils import timezone
from pathlib import Path
import logging
import os

logger = logging.getLogger(__name__)


def _validar_ruta_archivo(file_path: str) -> bool:
    """
    Valida que la ruta del archivo esté dentro de MEDIA_ROOT.
    Previene ataques de path traversal (CWE-22).
    
    Args:
        file_path: Ruta del archivo a validar
        
    Returns:
        True si la ruta es segura, False si es sospechosa
    """
    try:
        # Resolver rutas a absolutas y canonicalizadas
        media_root = Path(settings.MEDIA_ROOT).resolve()
        archivo_path = Path(file_path).resolve()
        
        # Verificar que el archivo está dentro de MEDIA_ROOT
        return str(archivo_path).startswith(str(media_root))
    except Exception:
        return False


def _mask_rut(rut: str) -> str:
    """
    Enmascara RUT para logs, mostrando solo últimos 4 caracteres.
    Protege PII según Ley 21.719.
    
    Args:
        rut: RUT completo (ej: "12345678-9")
        
    Returns:
        RUT enmascarado (ej: "****78-9")
    """
    if not rut or len(rut) < 5:
        return "****"
    return f"****{rut[-4:]}"


@shared_task(bind=True, max_retries=3, soft_time_limit=600, time_limit=720)
def procesar_archivo_erp(self, archivo_id, usuario_id=None):
    """
    Procesa un archivo ERP (Libro de Remuneraciones o Movimientos).
    
    1. Lee el archivo Excel
    2. Extrae headers/conceptos
    3. Crea ConceptoCliente si son nuevos
    4. Extrae datos de empleados
    5. Actualiza estado del archivo y cierre
    
    Args:
        archivo_id: ID del ArchivoERP a procesar
        usuario_id: ID del usuario que inició la tarea (para auditoría)
    
    Timeouts:
        soft_time_limit: 10 min (warning)
        time_limit: 12 min (kill)
    """
    from apps.validador.models import ArchivoERP
    
    try:
        archivo = ArchivoERP.objects.select_related('cierre').get(id=archivo_id)
        archivo.estado = 'procesando'
        archivo.save()
        
        # Validar que la ruta del archivo sea segura (prevenir path traversal)
        if not _validar_ruta_archivo(archivo.archivo.path):
            raise ValueError("Ruta de archivo no válida o fuera del directorio permitido")
        
        logger.info(f"Procesando archivo ERP ID={archivo_id}, tipo={archivo.tipo}")
        
        if archivo.tipo == 'libro_remuneraciones':
            resultado = _procesar_libro_remuneraciones(archivo)
        elif archivo.tipo == 'movimientos_mes':
            resultado = _procesar_movimientos_mes(archivo)
        else:
            raise ValueError(f"Tipo de archivo desconocido: {archivo.tipo}")
        
        archivo.estado = 'procesado'
        archivo.filas_procesadas = resultado.get('filas', 0)
        archivo.fecha_procesamiento = timezone.now()
        archivo.save()
        
        # Verificar si hay conceptos nuevos por clasificar
        _verificar_clasificacion_pendiente(archivo.cierre)
        
        logger.info(f"Archivo ERP procesado ID={archivo_id}: {resultado.get('filas', 0)} filas")
        return resultado
        
    except Exception as e:
        logger.error(f"Error procesando archivo ERP {archivo_id}: {str(e)}")
        
        try:
            archivo = ArchivoERP.objects.get(id=archivo_id)
            archivo.estado = 'error'
            archivo.errores_procesamiento = [str(e)]
            archivo.save()
        except:
            pass
        
        raise self.retry(exc=e, countdown=60)


def _procesar_libro_remuneraciones(archivo):
    """Procesa el Libro de Remuneraciones."""
    import pandas as pd
    from apps.validador.models import (
        ConceptoCliente,
        EmpleadoCierre,
        RegistroConcepto,
    )
    
    # Leer Excel
    df = pd.read_excel(archivo.archivo.path)
    
    cierre = archivo.cierre
    cliente = cierre.cliente
    
    # Identificar columnas de identificación (RUT, Nombre) vs conceptos
    columnas_id = ['rut', 'nombre', 'cargo', 'centro_costo', 'fecha_ingreso']
    columnas_id_encontradas = [col for col in df.columns if col.lower().strip() in columnas_id]
    columnas_concepto = [col for col in df.columns if col.lower().strip() not in columnas_id]
    
    # Crear/obtener conceptos
    conceptos_creados = 0
    for nombre_concepto in columnas_concepto:
        concepto, created = ConceptoCliente.objects.get_or_create(
            cliente=cliente,
            nombre_erp=nombre_concepto.strip(),
            defaults={'clasificado': False}
        )
        if created:
            conceptos_creados += 1
    
    # Procesar empleados
    empleados_procesados = 0
    for _, row in df.iterrows():
        # Buscar columna RUT
        rut_col = next((col for col in df.columns if col.lower().strip() == 'rut'), None)
        nombre_col = next((col for col in df.columns if col.lower().strip() == 'nombre'), None)
        
        if not rut_col:
            continue
        
        rut = str(row[rut_col]).strip()
        nombre = str(row[nombre_col]).strip() if nombre_col else ''
        
        if not rut or rut == 'nan':
            continue
        
        # Crear/actualizar empleado
        empleado, _ = EmpleadoCierre.objects.update_or_create(
            cierre=cierre,
            rut=rut,
            defaults={'nombre': nombre}
        )
        
        # Crear registros por concepto
        total_haberes = 0
        total_descuentos = 0
        
        for nombre_concepto in columnas_concepto:
            try:
                monto = float(row[nombre_concepto]) if pd.notna(row[nombre_concepto]) else 0
            except (ValueError, TypeError):
                monto = 0
            
            if monto == 0:
                continue
            
            concepto = ConceptoCliente.objects.get(
                cliente=cliente,
                nombre_erp=nombre_concepto.strip()
            )
            
            RegistroConcepto.objects.update_or_create(
                empleado=empleado,
                concepto=concepto,
                defaults={
                    'monto': monto * concepto.multiplicador,
                    'monto_original': monto,
                }
            )
            
            # Sumar a totales según categoría (si está clasificado)
            if concepto.categoria:
                if concepto.categoria.codigo in ['haberes_imponibles', 'haberes_no_imponibles']:
                    total_haberes += monto
                elif concepto.categoria.codigo in ['descuentos_legales', 'otros_descuentos']:
                    total_descuentos += monto
        
        empleado.total_haberes = total_haberes
        empleado.total_descuentos = total_descuentos
        empleado.liquido = total_haberes - total_descuentos
        empleado.save()
        
        empleados_procesados += 1
    
    return {
        'filas': empleados_procesados,
        'conceptos_nuevos': conceptos_creados,
    }


def _procesar_movimientos_mes(archivo):
    """
    Procesa el archivo de Movimientos del Mes usando la estrategia del ERP.
    
    Para Talana:
    - Lee hojas: "Altas y Bajas", "Ausentismos", "Vacaciones"
    - Headers en fila 3, datos desde fila 4
    - Aplica regla RN-001: baja + plazo fijo + sin motivo = ignorar
    """
    from apps.validador.models import MovimientoMes
    from apps.validador.services.erp import ERPFactory
    from datetime import datetime
    
    cierre = archivo.cierre
    
    # Obtener estrategia del ERP del cliente
    erp_codigo = 'generic'
    if cierre.cliente and hasattr(cierre.cliente, 'erp') and cierre.cliente.erp:
        erp_codigo = cierre.cliente.erp.codigo
    else:
        # Default a Talana si no hay ERP configurado
        erp_codigo = 'talana'
    
    strategy = ERPFactory.get_strategy(erp_codigo)
    
    # Parsear archivo usando la estrategia
    result = strategy.parse_archivo(archivo.archivo.path, 'movimientos_mes')
    
    if not result.success:
        raise ValueError(f"Error parseando archivo: {result.error}")
    
    data = result.data
    warnings = data.get('warnings', [])
    
    # Actualizar hojas encontradas en el archivo
    archivo.hojas_encontradas = data.get('hojas_encontradas', [])
    archivo.save()
    
    # Eliminar movimientos anteriores de este archivo (para re-procesamiento)
    MovimientoMes.objects.filter(archivo_erp=archivo).delete()
    
    # Crear registros en bulk
    movimientos_a_crear = []
    
    # Procesar altas y bajas
    for registro in data.get('altas_bajas', []):
        movimientos_a_crear.append(_crear_movimiento_desde_dict(cierre, archivo, registro))
    
    # Procesar ausentismos
    for registro in data.get('ausentismos', []):
        movimientos_a_crear.append(_crear_movimiento_desde_dict(cierre, archivo, registro))
    
    # Procesar vacaciones
    for registro in data.get('vacaciones', []):
        movimientos_a_crear.append(_crear_movimiento_desde_dict(cierre, archivo, registro))
    
    # Bulk create para mejor performance
    if movimientos_a_crear:
        MovimientoMes.objects.bulk_create(movimientos_a_crear)
    
    total_creados = len(movimientos_a_crear)
    
    logger.info(
        f"Movimientos procesados para cierre_id={cierre.id}: "
        f"altas_bajas={len(data.get('altas_bajas', []))}, "
        f"ausentismos={len(data.get('ausentismos', []))}, "
        f"vacaciones={len(data.get('vacaciones', []))}. "
        f"Total={total_creados}, warnings={len(warnings)}"
    )
    
    return {
        'filas': total_creados,
        'hojas': data.get('hojas_encontradas', []),
        'detalle': {
            'altas_bajas': len(data.get('altas_bajas', [])),
            'ausentismos': len(data.get('ausentismos', [])),
            'vacaciones': len(data.get('vacaciones', [])),
        },
        'warnings': warnings,
    }


def _crear_movimiento_desde_dict(cierre, archivo, registro: dict):
    """Crea instancia de MovimientoMes desde diccionario normalizado."""
    from apps.validador.models import MovimientoMes
    from datetime import datetime
    
    # Convertir fechas string a date objects
    fecha_inicio = None
    fecha_fin = None
    
    if registro.get('fecha_inicio'):
        try:
            fecha_inicio = datetime.strptime(registro['fecha_inicio'], '%Y-%m-%d').date()
        except (ValueError, TypeError):
            pass
    
    if registro.get('fecha_fin'):
        try:
            fecha_fin = datetime.strptime(registro['fecha_fin'], '%Y-%m-%d').date()
        except (ValueError, TypeError):
            pass
    
    # Serializar datos_raw para evitar problemas con tipos no serializables
    # NaN/Inf no son válidos en JSON, convertir a None
    datos_raw = registro.get('datos_raw', {})
    if datos_raw:
        datos_raw_clean = {}
        for k, v in datos_raw.items():
            if isinstance(v, float) and (v != v or v == float('inf') or v == float('-inf')):
                # NaN check: NaN != NaN es True
                datos_raw_clean[k] = None
            elif not isinstance(v, (str, int, float, bool, type(None))):
                datos_raw_clean[k] = str(v)
            else:
                datos_raw_clean[k] = v
        datos_raw = datos_raw_clean
    
    return MovimientoMes(
        cierre=cierre,
        archivo_erp=archivo,
        tipo=registro.get('tipo', 'otro'),
        rut=registro.get('rut', ''),
        nombre=registro.get('nombre', ''),
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        dias=registro.get('dias'),
        tipo_contrato=registro.get('tipo_contrato', ''),
        causal=registro.get('causal', ''),
        tipo_licencia=registro.get('tipo_licencia', ''),
        hoja_origen=registro.get('hoja_origen', ''),
        datos_raw=datos_raw,
    )


def _verificar_clasificacion_pendiente(cierre):
    """Verifica si hay conceptos pendientes de clasificar."""
    from apps.validador.models import ConceptoCliente
    
    sin_clasificar = ConceptoCliente.objects.filter(
        cliente=cierre.cliente,
        clasificado=False
    ).count()
    
    cierre.requiere_clasificacion = sin_clasificar > 0
    cierre.save()
