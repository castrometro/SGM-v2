"""
Celery Tasks para procesamiento de Archivos del Analista.

Procesa archivos del cliente (no dependen del ERP):
- Novedades: Items/conceptos con montos
- Ingresos: Altas de personal  
- Finiquitos: Bajas de personal
- Ausentismos: Licencias, permisos, vacaciones

Seguridad:
- Validación de rutas (CWE-22 path traversal)
- Enmascaramiento de PII en logs (Ley 21.719)
- Sanitización de datos JSON
"""

from celery import shared_task
from celery.exceptions import SoftTimeLimitExceeded
from django.utils import timezone
import logging

from apps.validador.utils import (
    normalizar_rut,
    mask_rut,
    parse_fecha,
    sanitizar_datos_raw,
    validar_ruta_archivo,
)

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, soft_time_limit=300, time_limit=360)
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
    
    Timeouts:
        soft_time_limit: 5 min (warning)
        time_limit: 6 min (kill)
    """
    from apps.validador.models import ArchivoAnalista, ConceptoNovedades, ConceptoLibro
    from apps.validador.constants import EstadoArchivoNovedades
    import pandas as pd
    import unicodedata
    import re
    import html
    
    def sanitizar_header(header: str) -> str:
        """
        Sanitiza un header de Excel para prevenir inyecciones.
        
        Seguridad:
        - Remueve caracteres no imprimibles
        - Limita longitud
        - Remueve caracteres de inyección SQL/XSS
        - Escapa HTML
        """
        if not header:
            return ""
        
        header = str(header)
        
        # Remover caracteres no imprimibles
        header = ''.join(c for c in header if c.isprintable())
        
        # Limitar longitud
        MAX_HEADER_LENGTH = 200
        header = header[:MAX_HEADER_LENGTH]
        
        # Remover caracteres peligrosos para SQL/script injection
        header = re.sub(r'[;<>\'\"\\]', '', header)
        
        # Escapar HTML para prevenir XSS
        header = html.escape(header)
        
        # Remover espacios excesivos
        header = ' '.join(header.split())
        
        return header.strip()
    
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
        
        # Validar ruta del archivo (seguridad: path traversal)
        if not validar_ruta_archivo(archivo.archivo.path):
            raise ValueError("Ruta de archivo no permitida")
        
        archivo.estado = EstadoArchivoNovedades.EXTRAYENDO_HEADERS
        archivo.save()
        
        logger.info(f"Extrayendo headers de novedades: {archivo.nombre_original}")
        
        cierre = archivo.cierre
        cliente = cierre.cliente
        
        # Obtener ERP activo del cliente (desde configuraciones_erp)
        config_erp = cliente.configuraciones_erp.filter(activo=True).select_related('erp').first()
        if not config_erp:
            raise ValueError(f"Cliente {mask_rut(cliente.rut)} no tiene ERP activo configurado")
        erp = config_erp.erp
        
        # Leer archivo
        if archivo.extension == '.csv':
            df = pd.read_csv(archivo.archivo.path, nrows=1)
        else:
            df = pd.read_excel(archivo.archivo.path, nrows=1)
        
        # Columnas que NO son items (identificación)
        columnas_ignoradas = ['rut', 'nombre', 'fecha', 'periodo', 'observacion', 'observaciones']
        
        # Filtrar columnas de items y sanitizar
        headers = []
        for col in df.columns:
            col_sanitizado = sanitizar_header(col)
            if not col_sanitizado:
                continue
            col_lower = col_sanitizado.lower().strip()
            if col_lower not in columnas_ignoradas:
                headers.append(col_sanitizado)
        
        if not headers:
            raise ValueError("No se encontraron columnas de items en el archivo")
        
        # Crear o reutilizar ConceptoNovedades por cada header
        conceptos_creados = 0
        
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
            else:
                # Actualizar orden si cambió
                if concepto.orden != orden:
                    concepto.orden = orden
                    concepto.save()
        
        # Contar total de conceptos activos para este cliente+ERP
        total_conceptos = ConceptoNovedades.objects.filter(
            cliente=cliente, erp=erp, activo=True
        ).count()
        
        # Sin mapear = no tiene concepto_libro NI está marcado sin_asignacion
        total_sin_mapear = ConceptoNovedades.objects.filter(
            cliente=cliente, erp=erp, activo=True,
            concepto_libro__isnull=True,
            sin_asignacion=False
        ).count()
        
        # Determinar estado: si todos mapeados/sin_asignacion → listo, sino → pendiente_mapeo
        if total_sin_mapear == 0:
            archivo.estado = EstadoArchivoNovedades.LISTO
        else:
            archivo.estado = EstadoArchivoNovedades.PENDIENTE_MAPEO
        
        archivo.save()
        
        logger.info(
            f"Headers novedades extraídos: {len(headers)} en archivo, "
            f"{conceptos_creados} nuevos"
        )
        
        return {
            'headers_archivo': len(headers),
            'conceptos_nuevos': conceptos_creados,
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


@shared_task(bind=True, max_retries=3, soft_time_limit=600, time_limit=720)
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
    
    Timeouts:
        soft_time_limit: 10 min (warning)
        time_limit: 12 min (kill)
    """
    from apps.validador.models import ArchivoAnalista
    from apps.validador.constants import EstadoArchivoNovedades
    
    try:
        archivo = ArchivoAnalista.objects.select_related('cierre').get(id=archivo_id)
        
        # Validar ruta del archivo (seguridad: path traversal)
        if not validar_ruta_archivo(archivo.archivo.path):
            raise ValueError("Ruta de archivo no permitida")
        
        # Validar estado para novedades: debe estar LISTO
        if archivo.tipo == 'novedades':
            if archivo.estado != EstadoArchivoNovedades.LISTO:
                raise ValueError(
                    f"Archivo de novedades debe estar en estado LISTO para procesar "
                    f"(estado actual: {archivo.estado})"
                )
            archivo.estado = EstadoArchivoNovedades.PROCESANDO
        else:
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
        
        # Actualizar estado según tipo
        if archivo.tipo == 'novedades':
            archivo.estado = EstadoArchivoNovedades.PROCESADO
        else:
            archivo.estado = 'procesado'
        archivo.filas_procesadas = resultado.get('filas', 0)
        archivo.fecha_procesamiento = timezone.now()
        archivo.save()
        
        # Verificar si hay items nuevos por mapear (solo para otros tipos, no novedades)
        if archivo.tipo != 'novedades':
            _verificar_mapeo_pendiente(archivo.cierre)
        
        logger.info(f"Archivo Analista procesado: {archivo.nombre_original} - {resultado}")
        return resultado
        
    except Exception as e:
        logger.error(f"Error procesando archivo Analista {archivo_id}: {str(e)}")
        
        try:
            archivo = ArchivoAnalista.objects.get(id=archivo_id)
            if archivo.tipo == 'novedades':
                archivo.estado = EstadoArchivoNovedades.ERROR
            else:
                archivo.estado = 'error'
            archivo.errores_procesamiento = [str(e)]
            archivo.save()
        except:
            pass
        
        raise self.retry(exc=e, countdown=60)


def _procesar_novedades(archivo):
    """
    Procesa el archivo de Novedades del cliente.
    
    - Lee archivo Excel/CSV
    - Crea RegistroNovedades por cada (RUT, item, monto)
    - Ignora items marcados como sin_asignacion
    """
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
    
    # Pre-cargar ConceptoNovedades del cliente para evitar N+1 queries
    conceptos_dict = {}
    for concepto in ConceptoNovedades.objects.filter(cliente=cliente, activo=True).select_related('concepto_libro'):
        conceptos_dict[concepto.header_normalizado] = concepto
    
    # Limpiar registros anteriores del cierre
    RegistroNovedades.objects.filter(cierre=cierre).delete()
    
    registros_creados = 0
    registros_ignorados = 0  # Items sin_asignacion
    registros_batch = []
    
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
            concepto = conceptos_dict.get(header_normalizado)
            
            # Ignorar items marcados como sin_asignacion
            if concepto and concepto.sin_asignacion:
                registros_ignorados += 1
                continue
            
            registros_batch.append(RegistroNovedades(
                cierre=cierre,
                rut_empleado=rut,
                nombre_empleado=nombre,
                nombre_item=nombre_item.strip(),
                concepto_novedades=concepto,
                monto=monto,
            ))
            registros_creados += 1
            
            # Bulk insert cada 1000 registros
            if len(registros_batch) >= 1000:
                RegistroNovedades.objects.bulk_create(registros_batch)
                registros_batch = []
    
    # Insertar registros restantes
    if registros_batch:
        RegistroNovedades.objects.bulk_create(registros_batch)
    
    return {
        'filas': registros_creados,
        'ignorados_sin_asignacion': registros_ignorados,
    }


def _procesar_asistencias(archivo):
    """
    Procesa el archivo de Ausentismos del analista.
    
    Formato esperado (headers en fila 1):
    - Rut
    - Nombre
    - Fecha Inicio Ausencia
    - Fecha Fin Ausencia
    - Tipo Ausentismo
    """
    import pandas as pd
    from apps.validador.models import MovimientoAnalista
    
    if archivo.extension == '.csv':
        df = pd.read_csv(archivo.archivo.path)
    else:
        df = pd.read_excel(archivo.archivo.path)
    
    cierre = archivo.cierre
    
    # Mapeo de columnas (case-insensitive)
    col_map = {}
    for col in df.columns:
        col_lower = col.lower().strip()
        if 'rut' in col_lower:
            col_map['rut'] = col
        elif 'nombre' in col_lower:
            col_map['nombre'] = col
        elif 'inicio' in col_lower and ('fecha' in col_lower or 'ausencia' in col_lower):
            col_map['fecha_inicio'] = col
        elif 'fin' in col_lower and ('fecha' in col_lower or 'ausencia' in col_lower):
            col_map['fecha_fin'] = col
        elif 'tipo' in col_lower and 'ausentismo' in col_lower:
            col_map['tipo_ausentismo'] = col
    
    if 'rut' not in col_map:
        raise ValueError("No se encontró columna de RUT")
    
    # Eliminar movimientos anteriores de este archivo (para re-procesamiento)
    MovimientoAnalista.objects.filter(archivo_analista=archivo).delete()
    
    # Mapeo de tipo ausentismo -> tipo movimiento
    MAPEO_TIPO = {
        'licencia': 'licencia',
        'licencia medica': 'licencia',
        'licencia médica': 'licencia',
        'licencia maternal': 'licencia',
        'vacacion': 'vacaciones',
        'vacaciones': 'vacaciones',
        'permiso': 'permiso',
        'permiso con goce': 'permiso',
        'permiso sin goce': 'permiso',
        'ausencia': 'ausencia',
        'ausencia no justificada': 'ausencia',
        'ausencia injustificada': 'ausencia',
        'falta': 'ausencia',
    }
    
    movimientos = []
    filas_procesadas = 0
    filas_omitidas = 0
    
    for idx, row in df.iterrows():
        rut_raw = row.get(col_map['rut'], '')
        rut = normalizar_rut(rut_raw)
        if not rut:
            filas_omitidas += 1
            continue
        
        nombre = str(row.get(col_map.get('nombre', ''), '')).strip()
        if nombre == 'nan':
            nombre = ''
        
        # Parsear fechas
        fecha_inicio = parse_fecha(row.get(col_map.get('fecha_inicio')))
        fecha_fin = parse_fecha(row.get(col_map.get('fecha_fin')))
        
        # Tipo ausentismo
        tipo_ausentismo_raw = str(row.get(col_map.get('tipo_ausentismo', ''), '')).strip()
        tipo_ausentismo_lower = tipo_ausentismo_raw.lower()
        
        # Determinar tipo de movimiento
        tipo = 'otro'
        for key, value in MAPEO_TIPO.items():
            if key in tipo_ausentismo_lower:
                tipo = value
                break
        
        # Calcular días si hay fechas
        dias = None
        if fecha_inicio and fecha_fin:
            dias = (fecha_fin - fecha_inicio).days + 1
        
        # Sanitizar datos_raw
        datos_raw = sanitizar_datos_raw(row.to_dict())
        
        movimientos.append(MovimientoAnalista(
            cierre=cierre,
            archivo_analista=archivo,
            tipo=tipo,
            origen='asistencias',
            rut=rut,
            nombre=nombre,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            dias=dias,
            tipo_ausentismo=tipo_ausentismo_raw,
            datos_raw=datos_raw,
        ))
        filas_procesadas += 1
    
    # Bulk create
    if movimientos:
        MovimientoAnalista.objects.bulk_create(movimientos)
    
    logger.info(f"Ausentismos procesados: {filas_procesadas}, omitidas: {filas_omitidas}")
    return {'filas': filas_procesadas, 'omitidas': filas_omitidas}


def _procesar_finiquitos(archivo):
    """
    Procesa el archivo de Finiquitos del analista.
    
    Formato esperado (headers en fila 1):
    - Rut
    - Nombre
    - Fecha Retiro
    - Motivo
    """
    import pandas as pd
    from apps.validador.models import MovimientoAnalista
    
    if archivo.extension == '.csv':
        df = pd.read_csv(archivo.archivo.path)
    else:
        df = pd.read_excel(archivo.archivo.path)
    
    cierre = archivo.cierre
    
    # Mapeo de columnas (case-insensitive)
    col_map = {}
    for col in df.columns:
        col_lower = col.lower().strip()
        if 'rut' in col_lower:
            col_map['rut'] = col
        elif 'nombre' in col_lower:
            col_map['nombre'] = col
        elif 'fecha' in col_lower and 'retiro' in col_lower:
            col_map['fecha_retiro'] = col
        elif 'motivo' in col_lower or 'causal' in col_lower:
            col_map['motivo'] = col
    
    if 'rut' not in col_map:
        raise ValueError("No se encontró columna de RUT")
    
    # Eliminar movimientos anteriores de este archivo
    MovimientoAnalista.objects.filter(archivo_analista=archivo).delete()
    
    movimientos = []
    filas_procesadas = 0
    filas_omitidas = 0
    
    for idx, row in df.iterrows():
        rut_raw = row.get(col_map['rut'], '')
        rut = normalizar_rut(rut_raw)
        if not rut:
            filas_omitidas += 1
            continue
        
        nombre = str(row.get(col_map.get('nombre', ''), '')).strip()
        if nombre == 'nan':
            nombre = ''
        
        fecha_retiro = parse_fecha(row.get(col_map.get('fecha_retiro')))
        
        causal = str(row.get(col_map.get('motivo', ''), '')).strip()
        if causal == 'nan':
            causal = ''
        
        datos_raw = sanitizar_datos_raw(row.to_dict())
        
        movimientos.append(MovimientoAnalista(
            cierre=cierre,
            archivo_analista=archivo,
            tipo='baja',
            origen='finiquitos',
            rut=rut,
            nombre=nombre,
            fecha_fin=fecha_retiro,  # fecha_fin = fecha de retiro
            causal=causal,
            datos_raw=datos_raw,
        ))
        filas_procesadas += 1
    
    if movimientos:
        MovimientoAnalista.objects.bulk_create(movimientos)
    
    logger.info(f"Finiquitos procesados: {filas_procesadas}, omitidas: {filas_omitidas}")
    return {'filas': filas_procesadas, 'omitidas': filas_omitidas}


def _procesar_ingresos(archivo):
    """
    Procesa el archivo de Ingresos del analista.
    
    Formato esperado (headers en fila 1):
    - Rut
    - Nombre
    - Fecha Ingreso
    """
    import pandas as pd
    from apps.validador.models import MovimientoAnalista
    
    if archivo.extension == '.csv':
        df = pd.read_csv(archivo.archivo.path)
    else:
        df = pd.read_excel(archivo.archivo.path)
    
    cierre = archivo.cierre
    
    # Mapeo de columnas (case-insensitive)
    col_map = {}
    for col in df.columns:
        col_lower = col.lower().strip()
        if 'rut' in col_lower:
            col_map['rut'] = col
        elif 'nombre' in col_lower:
            col_map['nombre'] = col
        elif 'fecha' in col_lower and 'ingreso' in col_lower:
            col_map['fecha_ingreso'] = col
    
    if 'rut' not in col_map:
        raise ValueError("No se encontró columna de RUT")
    
    # Eliminar movimientos anteriores de este archivo
    MovimientoAnalista.objects.filter(archivo_analista=archivo).delete()
    
    movimientos = []
    filas_procesadas = 0
    filas_omitidas = 0
    
    for idx, row in df.iterrows():
        rut_raw = row.get(col_map['rut'], '')
        rut = normalizar_rut(rut_raw)
        if not rut:
            filas_omitidas += 1
            continue
        
        nombre = str(row.get(col_map.get('nombre', ''), '')).strip()
        if nombre == 'nan':
            nombre = ''
        
        fecha_ingreso = parse_fecha(row.get(col_map.get('fecha_ingreso')))
        
        datos_raw = sanitizar_datos_raw(row.to_dict())
        
        movimientos.append(MovimientoAnalista(
            cierre=cierre,
            archivo_analista=archivo,
            tipo='alta',
            origen='ingresos',
            rut=rut,
            nombre=nombre,
            fecha_inicio=fecha_ingreso,  # fecha_inicio = fecha de ingreso
            datos_raw=datos_raw,
        ))
        filas_procesadas += 1
    
    if movimientos:
        MovimientoAnalista.objects.bulk_create(movimientos)
    
    logger.info(f"Ingresos procesados: {filas_procesadas}, omitidas: {filas_omitidas}")
    return {'filas': filas_procesadas, 'omitidas': filas_omitidas}


def _verificar_mapeo_pendiente(cierre):
    """Verifica si hay items de novedades pendientes de mapear."""
    from apps.validador.models import RegistroNovedades
    
    sin_mapear = RegistroNovedades.objects.filter(
        cierre=cierre,
        mapeo__isnull=True
    ).values('nombre_item').distinct().count()
    
    cierre.requiere_mapeo = sin_mapear > 0
    cierre.save()
