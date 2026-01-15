"""
Celery Tasks para procesamiento de Archivos del Analista.
"""

from celery import shared_task
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def extraer_headers_novedades(self, archivo_id, usuario_id=None):
    """
    Extrae los headers (items) del archivo de Novedades.
    
    Similar a extraer_headers_libro, pero para el archivo del cliente.
    Crea ConceptoNovedades por cada columna que no sea RUT/identificación.
    Busca ConceptoLibro existentes para auto-mapear por coincidencia de nombre.
    
    Flujo:
        1. Lee primera fila del archivo
        2. Identifica columnas de items (no RUT, nombre, etc.)
        3. Crea ConceptoNovedades por cada columna (o reutiliza existente)
        4. Busca coincidencias con ConceptoLibro por nombre normalizado
        5. Actualiza estado: pendiente_mapeo o listo
    
    Args:
        archivo_id: ID del ArchivoAnalista tipo='novedades'
        usuario_id: ID del usuario que inició la tarea
    """
    from apps.validador.models import ArchivoAnalista, ConceptoNovedades, ConceptoLibro
    from apps.validador.constants import EstadoArchivoNovedades
    import pandas as pd
    import unicodedata
    import re
    
    def normalizar_header(header: str) -> str:
        """Normaliza header para comparación."""
        texto = str(header).lower().strip()
        texto = unicodedata.normalize('NFD', texto)
        texto = ''.join(c for c in texto if unicodedata.category(c) != 'Mn')
        texto = re.sub(r'[^a-z0-9\s]', '', texto)
        texto = re.sub(r'\s+', '_', texto.strip())
        return texto
    
    try:
        archivo = ArchivoAnalista.objects.select_related(
            'cierre__cliente'
        ).get(id=archivo_id)
        
        if archivo.tipo != 'novedades':
            raise ValueError(f"Archivo no es de tipo novedades: {archivo.tipo}")
        
        archivo.estado = EstadoArchivoNovedades.EXTRAYENDO_HEADERS
        archivo.save()
        
        logger.info(f"Extrayendo headers de novedades: {archivo.nombre_original}")
        
        cierre = archivo.cierre
        cliente = cierre.cliente
        
        # Obtener ERP activo del cliente (desde configuraciones_erp)
        config_erp = cliente.configuraciones_erp.filter(activo=True).select_related('erp').first()
        if not config_erp:
            raise ValueError(f"Cliente {cliente.rut} no tiene ERP activo configurado")
        erp = config_erp.erp
        
        # Leer archivo
        if archivo.extension == '.csv':
            df = pd.read_csv(archivo.archivo.path, nrows=1)
        else:
            df = pd.read_excel(archivo.archivo.path, nrows=1)
        
        # Columnas que NO son items (identificación)
        columnas_ignoradas = ['rut', 'nombre', 'fecha', 'periodo', 'observacion', 'observaciones']
        
        # Filtrar columnas de items
        headers = []
        for col in df.columns:
            col_lower = col.lower().strip()
            if col_lower not in columnas_ignoradas:
                headers.append(col.strip())
        
        if not headers:
            raise ValueError("No se encontraron columnas de items en el archivo")
        
        # Obtener ConceptoLibro existentes para auto-mapeo
        conceptos_libro_dict = {}
        for cl in ConceptoLibro.objects.filter(cliente=cliente, erp=erp, activo=True):
            key = normalizar_header(cl.header_original)
            conceptos_libro_dict[key] = cl
        
        # Crear o reutilizar ConceptoNovedades por cada header
        conceptos_creados = 0
        conceptos_mapeados = 0
        
        for orden, header_original in enumerate(headers, start=1):
            header_normalizado = normalizar_header(header_original)
            
            # Buscar concepto existente para este cliente+ERP+header
            concepto, created = ConceptoNovedades.objects.get_or_create(
                cliente=cliente,
                erp=erp,
                header_normalizado=header_normalizado,
                defaults={
                    'header_original': header_original,
                    'orden': orden,
                    'activo': True,
                }
            )
            
            if created:
                conceptos_creados += 1
                # Intentar auto-mapear por coincidencia de nombre normalizado
                if header_normalizado in conceptos_libro_dict:
                    concepto.concepto_libro = conceptos_libro_dict[header_normalizado]
                    concepto.save()
                    conceptos_mapeados += 1
            else:
                # Actualizar orden si cambió
                if concepto.orden != orden:
                    concepto.orden = orden
                    concepto.save()
                
                if concepto.concepto_libro:
                    conceptos_mapeados += 1
        
        # Contar total de conceptos activos para este cliente+ERP
        total_conceptos = ConceptoNovedades.objects.filter(
            cliente=cliente, erp=erp, activo=True
        ).count()
        
        total_sin_mapear = ConceptoNovedades.objects.filter(
            cliente=cliente, erp=erp, activo=True, concepto_libro__isnull=True
        ).count()
        
        # Determinar estado: si todos mapeados → listo, sino → pendiente_mapeo
        if total_sin_mapear == 0:
            archivo.estado = EstadoArchivoNovedades.LISTO
        else:
            archivo.estado = EstadoArchivoNovedades.PENDIENTE_MAPEO
        
        archivo.save()
        
        logger.info(
            f"Headers novedades extraídos: {len(headers)} en archivo, "
            f"{conceptos_creados} nuevos, {conceptos_mapeados} auto-mapeados"
        )
        
        return {
            'headers_archivo': len(headers),
            'conceptos_nuevos': conceptos_creados,
            'conceptos_mapeados': conceptos_mapeados,
            'total_conceptos': total_conceptos,
            'sin_mapear': total_sin_mapear,
            'estado': archivo.estado,
        }
        
    except Exception as e:
        logger.error(f"Error extrayendo headers novedades {archivo_id}: {str(e)}")
        
        try:
            archivo = ArchivoAnalista.objects.get(id=archivo_id)
            archivo.estado = EstadoArchivoNovedades.ERROR
            archivo.errores_procesamiento = [str(e)]
            archivo.save()
        except:
            pass
        
        raise self.retry(exc=e, countdown=60)


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
    import unicodedata
    import re
    from apps.validador.models import RegistroNovedades, ConceptoNovedades
    
    def normalizar_header(header: str) -> str:
        """Normaliza header para comparación."""
        texto = str(header).lower().strip()
        texto = unicodedata.normalize('NFD', texto)
        texto = ''.join(c for c in texto if unicodedata.category(c) != 'Mn')
        texto = re.sub(r'[^a-z0-9\s]', '', texto)
        texto = re.sub(r'\s+', '_', texto.strip())
        return texto
    
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
            
            # Buscar ConceptoNovedades por header normalizado
            header_normalizado = normalizar_header(nombre_item)
            concepto = ConceptoNovedades.objects.filter(
                cliente=cliente,
                header_normalizado=header_normalizado,
                activo=True
            ).select_related('concepto_libro').first()
            
            if not concepto or not concepto.concepto_libro:
                items_nuevos.add(nombre_item.strip())
            
            RegistroNovedades.objects.create(
                cierre=cierre,
                rut_empleado=rut,
                nombre_empleado=nombre,
                nombre_item=nombre_item.strip(),
                concepto_novedades=concepto,
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
