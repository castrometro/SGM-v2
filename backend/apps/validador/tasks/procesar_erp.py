"""
Celery Tasks para procesamiento de Archivos ERP.
"""

from celery import shared_task
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def procesar_archivo_erp(self, archivo_id):
    """
    Procesa un archivo ERP (Libro de Remuneraciones o Movimientos).
    
    1. Lee el archivo Excel
    2. Extrae headers/conceptos
    3. Crea ConceptoCliente si son nuevos
    4. Extrae datos de empleados
    5. Actualiza estado del archivo y cierre
    """
    from apps.validador.models import ArchivoERP
    
    try:
        archivo = ArchivoERP.objects.select_related('cierre').get(id=archivo_id)
        archivo.estado = 'procesando'
        archivo.save()
        
        logger.info(f"Procesando archivo ERP: {archivo.nombre_original}")
        
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
        
        logger.info(f"Archivo ERP procesado: {archivo.nombre_original} - {resultado}")
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
    """Procesa el archivo de Movimientos del Mes."""
    import pandas as pd
    from apps.validador.models import MovimientoMes
    
    # El archivo tiene múltiples hojas
    excel_file = pd.ExcelFile(archivo.archivo.path)
    hojas = excel_file.sheet_names
    
    archivo.hojas_encontradas = hojas
    archivo.save()
    
    cierre = archivo.cierre
    movimientos_creados = 0
    
    # Mapeo de nombres de hoja a tipos de movimiento
    mapeo_hojas = {
        'ingresos': 'alta',
        'altas': 'alta',
        'finiquitos': 'baja',
        'bajas': 'baja',
        'licencias': 'licencia',
        'vacaciones': 'vacaciones',
        'permisos': 'permiso',
        'ausencias': 'ausencia',
    }
    
    for hoja in hojas:
        nombre_hoja_lower = hoja.lower().strip()
        tipo = mapeo_hojas.get(nombre_hoja_lower, 'otro')
        
        try:
            df = pd.read_excel(excel_file, sheet_name=hoja)
        except Exception:
            continue
        
        # Buscar columna RUT
        rut_col = next((col for col in df.columns if 'rut' in col.lower()), None)
        nombre_col = next((col for col in df.columns if 'nombre' in col.lower()), None)
        
        if not rut_col:
            continue
        
        for _, row in df.iterrows():
            rut = str(row[rut_col]).strip()
            if not rut or rut == 'nan':
                continue
            
            nombre = str(row[nombre_col]).strip() if nombre_col else ''
            
            MovimientoMes.objects.create(
                cierre=cierre,
                tipo=tipo,
                rut=rut,
                nombre=nombre,
                hoja_origen=hoja,
                datos_raw=row.to_dict(),
            )
            movimientos_creados += 1
    
    return {
        'filas': movimientos_creados,
        'hojas': hojas,
    }


def _verificar_clasificacion_pendiente(cierre):
    """Verifica si hay conceptos pendientes de clasificar."""
    from apps.validador.models import ConceptoCliente
    
    sin_clasificar = ConceptoCliente.objects.filter(
        cliente=cierre.cliente,
        clasificado=False
    ).count()
    
    cierre.requiere_clasificacion = sin_clasificar > 0
    cierre.save()
