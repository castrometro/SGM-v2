"""
Celery Tasks para procesamiento de Archivos del Analista.
"""

from celery import shared_task
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def procesar_archivo_analista(self, archivo_id, usuario_id=None):
    """
    Procesa un archivo del Analista (Novedades, Asistencias, Finiquitos, Ingresos).
    
    1. Lee el archivo Excel/CSV
    2. Extrae datos según tipo
    3. Crea registros correspondientes
    4. Actualiza estado del archivo y cierre
    
    Args:
        archivo_id: ID del ArchivoAnalista a procesar
        usuario_id: ID del usuario que inició la tarea (para auditoría)
    """
    from apps.validador.models import ArchivoAnalista
    
    try:
        archivo = ArchivoAnalista.objects.select_related('cierre').get(id=archivo_id)
        archivo.estado = 'procesando'
        archivo.save()
        
        logger.info(f"Procesando archivo Analista: {archivo.nombre_original}")
        
        if archivo.tipo == 'novedades':
            resultado = _procesar_novedades(archivo)
        elif archivo.tipo == 'asistencias':
            resultado = _procesar_asistencias(archivo)
        elif archivo.tipo == 'finiquitos':
            resultado = _procesar_finiquitos(archivo)
        elif archivo.tipo == 'ingresos':
            resultado = _procesar_ingresos(archivo)
        else:
            raise ValueError(f"Tipo de archivo desconocido: {archivo.tipo}")
        
        archivo.estado = 'procesado'
        archivo.filas_procesadas = resultado.get('filas', 0)
        archivo.fecha_procesamiento = timezone.now()
        archivo.save()
        
        # Verificar si hay items nuevos por mapear
        _verificar_mapeo_pendiente(archivo.cierre)
        
        logger.info(f"Archivo Analista procesado: {archivo.nombre_original} - {resultado}")
        return resultado
        
    except Exception as e:
        logger.error(f"Error procesando archivo Analista {archivo_id}: {str(e)}")
        
        try:
            archivo = ArchivoAnalista.objects.get(id=archivo_id)
            archivo.estado = 'error'
            archivo.errores_procesamiento = [str(e)]
            archivo.save()
        except:
            pass
        
        raise self.retry(exc=e, countdown=60)


def _procesar_novedades(archivo):
    """Procesa el archivo de Novedades del cliente."""
    import pandas as pd
    from apps.validador.models import RegistroNovedades, MapeoItemNovedades
    
    # Leer archivo
    if archivo.extension == '.csv':
        df = pd.read_csv(archivo.archivo.path)
    else:
        df = pd.read_excel(archivo.archivo.path)
    
    cierre = archivo.cierre
    cliente = cierre.cliente
    
    # Buscar columnas clave
    rut_col = next((col for col in df.columns if 'rut' in col.lower()), None)
    nombre_col = next((col for col in df.columns if 'nombre' in col.lower()), None)
    
    if not rut_col:
        raise ValueError("No se encontró columna de RUT en el archivo de Novedades")
    
    # Columnas que son items (no son identificación)
    columnas_id = ['rut', 'nombre', 'fecha', 'periodo']
    columnas_item = [col for col in df.columns if col.lower().strip() not in columnas_id]
    
    # Limpiar registros anteriores del cierre
    RegistroNovedades.objects.filter(cierre=cierre).delete()
    
    registros_creados = 0
    items_nuevos = set()
    
    for _, row in df.iterrows():
        rut = str(row[rut_col]).strip()
        if not rut or rut == 'nan':
            continue
        
        nombre = str(row[nombre_col]).strip() if nombre_col else ''
        
        for nombre_item in columnas_item:
            try:
                monto = float(row[nombre_item]) if pd.notna(row[nombre_item]) else 0
            except (ValueError, TypeError):
                monto = 0
            
            if monto == 0:
                continue
            
            # Buscar mapeo existente
            mapeo = MapeoItemNovedades.objects.filter(
                cliente=cliente,
                nombre_novedades=nombre_item.strip()
            ).first()
            
            if not mapeo:
                items_nuevos.add(nombre_item.strip())
            
            RegistroNovedades.objects.create(
                cierre=cierre,
                rut_empleado=rut,
                nombre_empleado=nombre,
                nombre_item=nombre_item.strip(),
                mapeo=mapeo,
                monto=monto,
            )
            registros_creados += 1
    
    return {
        'filas': registros_creados,
        'items_sin_mapear': len(items_nuevos),
    }


def _procesar_asistencias(archivo):
    """Procesa el archivo de Asistencias."""
    import pandas as pd
    from apps.validador.models import MovimientoAnalista
    
    if archivo.extension == '.csv':
        df = pd.read_csv(archivo.archivo.path)
    else:
        df = pd.read_excel(archivo.archivo.path)
    
    cierre = archivo.cierre
    
    rut_col = next((col for col in df.columns if 'rut' in col.lower()), None)
    if not rut_col:
        raise ValueError("No se encontró columna de RUT")
    
    registros_creados = 0
    
    for _, row in df.iterrows():
        rut = str(row[rut_col]).strip()
        if not rut or rut == 'nan':
            continue
        
        # Detectar tipo de movimiento por columnas presentes
        nombre_col = next((col for col in df.columns if 'nombre' in col.lower()), None)
        tipo_col = next((col for col in df.columns if 'tipo' in col.lower()), None)
        dias_col = next((col for col in df.columns if 'dias' in col.lower() or 'día' in col.lower()), None)
        
        nombre = str(row[nombre_col]).strip() if nombre_col else ''
        tipo_str = str(row[tipo_col]).lower() if tipo_col and pd.notna(row[tipo_col]) else ''
        
        # Mapear tipo
        if 'licencia' in tipo_str:
            tipo = 'licencia'
        elif 'vacacion' in tipo_str:
            tipo = 'vacaciones'
        elif 'permiso' in tipo_str:
            tipo = 'permiso'
        elif 'ausencia' in tipo_str or 'falta' in tipo_str:
            tipo = 'ausencia'
        else:
            tipo = 'otro'
        
        dias = int(row[dias_col]) if dias_col and pd.notna(row[dias_col]) else None
        
        MovimientoAnalista.objects.create(
            cierre=cierre,
            tipo=tipo,
            origen='asistencias',
            rut=rut,
            nombre=nombre,
            dias=dias,
            datos_raw=row.to_dict(),
        )
        registros_creados += 1
    
    return {'filas': registros_creados}


def _procesar_finiquitos(archivo):
    """Procesa el archivo de Finiquitos."""
    import pandas as pd
    from apps.validador.models import MovimientoAnalista
    
    if archivo.extension == '.csv':
        df = pd.read_csv(archivo.archivo.path)
    else:
        df = pd.read_excel(archivo.archivo.path)
    
    cierre = archivo.cierre
    
    rut_col = next((col for col in df.columns if 'rut' in col.lower()), None)
    if not rut_col:
        raise ValueError("No se encontró columna de RUT")
    
    registros_creados = 0
    
    for _, row in df.iterrows():
        rut = str(row[rut_col]).strip()
        if not rut or rut == 'nan':
            continue
        
        nombre_col = next((col for col in df.columns if 'nombre' in col.lower()), None)
        causal_col = next((col for col in df.columns if 'causal' in col.lower() or 'motivo' in col.lower()), None)
        fecha_col = next((col for col in df.columns if 'fecha' in col.lower()), None)
        
        nombre = str(row[nombre_col]).strip() if nombre_col else ''
        causal = str(row[causal_col]).strip() if causal_col and pd.notna(row[causal_col]) else ''
        
        MovimientoAnalista.objects.create(
            cierre=cierre,
            tipo='baja',
            origen='finiquitos',
            rut=rut,
            nombre=nombre,
            causal=causal,
            datos_raw=row.to_dict(),
        )
        registros_creados += 1
    
    return {'filas': registros_creados}


def _procesar_ingresos(archivo):
    """Procesa el archivo de Ingresos."""
    import pandas as pd
    from apps.validador.models import MovimientoAnalista
    
    if archivo.extension == '.csv':
        df = pd.read_csv(archivo.archivo.path)
    else:
        df = pd.read_excel(archivo.archivo.path)
    
    cierre = archivo.cierre
    
    rut_col = next((col for col in df.columns if 'rut' in col.lower()), None)
    if not rut_col:
        raise ValueError("No se encontró columna de RUT")
    
    registros_creados = 0
    
    for _, row in df.iterrows():
        rut = str(row[rut_col]).strip()
        if not rut or rut == 'nan':
            continue
        
        nombre_col = next((col for col in df.columns if 'nombre' in col.lower()), None)
        fecha_col = next((col for col in df.columns if 'fecha' in col.lower()), None)
        
        nombre = str(row[nombre_col]).strip() if nombre_col else ''
        
        MovimientoAnalista.objects.create(
            cierre=cierre,
            tipo='alta',
            origen='ingresos',
            rut=rut,
            nombre=nombre,
            datos_raw=row.to_dict(),
        )
        registros_creados += 1
    
    return {'filas': registros_creados}


def _verificar_mapeo_pendiente(cierre):
    """Verifica si hay items de novedades pendientes de mapear."""
    from apps.validador.models import RegistroNovedades
    
    sin_mapear = RegistroNovedades.objects.filter(
        cierre=cierre,
        mapeo__isnull=True
    ).values('nombre_item').distinct().count()
    
    cierre.requiere_mapeo = sin_mapear > 0
    cierre.save()
