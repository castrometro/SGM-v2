"""
Servicio para gestión del Libro de Remuneraciones.

Maneja la lógica de negocio para:
- Extracción de headers
- Clasificación de conceptos
- Procesamiento del libro completo
"""

from typing import List, Dict, Optional
from decimal import Decimal
from django.db import transaction
from django.utils import timezone

from .base import BaseService, ServiceResult
from ..models import ArchivoERP, ConceptoLibro, EmpleadoLibro, Cierre
from ..parsers import ParserFactory
from ..constants import EstadoArchivoLibro, CategoriaConceptoLibro


class LibroService(BaseService):
    """
    Servicio para procesar el Libro de Remuneraciones.
    
    Uso:
        # Extraer headers
        result = LibroService.extraer_headers(archivo_erp)
        
        # Clasificar conceptos
        result = LibroService.clasificar_conceptos(
            archivo_erp, clasificaciones, user
        )
        
        # Procesar libro completo
        result = LibroService.procesar_libro(archivo_erp)
    """
    
    @classmethod
    def extraer_headers(cls, archivo_erp: ArchivoERP) -> ServiceResult[List[str]]:
        """
        Extrae los headers del archivo de libro.
        
        Args:
            archivo_erp: Instancia de ArchivoERP con tipo='libro_remuneraciones'
        
        Returns:
            ServiceResult con lista de headers o error
        """
        logger = cls.get_logger()
        
        try:
            # Validar que es libro de remuneraciones
            if archivo_erp.tipo != 'libro_remuneraciones':
                return ServiceResult.fail(
                    "El archivo no es de tipo 'libro_remuneraciones'"
                )
            
            # Validar estado
            if not EstadoArchivoLibro.puede_extraer_headers(archivo_erp.estado):
                return ServiceResult.fail(
                    f"No se pueden extraer headers en estado '{archivo_erp.estado}'"
                )
            
            # Actualizar estado
            archivo_erp.estado = EstadoArchivoLibro.EXTRAYENDO_HEADERS
            archivo_erp.save(update_fields=['estado'])
            
            # Obtener parser según ERP del cliente
            cierre = archivo_erp.cierre
            parser = ParserFactory.get_parser_for_cliente(cierre.cliente)
            
            if not parser:
                archivo_erp.estado = EstadoArchivoLibro.ERROR
                archivo_erp.error_mensaje = "No hay parser disponible para este ERP"
                archivo_erp.save(update_fields=['estado', 'error_mensaje'])
                return ServiceResult.fail("No hay parser disponible para este ERP")
            
            # Extraer headers
            headers = parser.extraer_headers(archivo_erp.archivo.path)
            
            logger.info(f"Extraídos {len(headers)} headers de {archivo_erp}")
            
            # Filtrar headers de empleado (no se registran en ConceptoLibro)
            # Solo contamos los headers que requieren clasificación (conceptos monetarios)
            if hasattr(parser, 'es_header_empleado'):
                headers_monetarios = [
                    h for i, h in enumerate(headers) 
                    if not parser.es_header_empleado(i)
                ]
                headers_empleado_count = len(headers) - len(headers_monetarios)
                logger.info(
                    f"Omitiendo {headers_empleado_count} headers de empleado, "
                    f"{len(headers_monetarios)} headers requieren clasificación"
                )
            else:
                headers_monetarios = headers
            
            # Actualizar archivo con conteo de headers que requieren clasificación
            archivo_erp.headers_total = len(headers_monetarios)
            archivo_erp.estado = EstadoArchivoLibro.PENDIENTE_CLASIFICACION
            archivo_erp.save(update_fields=['headers_total', 'estado'])
            
            # Crear/actualizar conceptos en BD (solo monetarios)
            cls._sincronizar_conceptos(archivo_erp, headers)
            
            # Contar clasificados (de los que se registraron en BD)
            config_erp = cierre.cliente.configuraciones_erp.filter(activo=True).first()
            headers_clasificados = ConceptoLibro.objects.filter(
                cliente=cierre.cliente,
                erp=config_erp.erp,
                categoria__isnull=False
            ).count()
            
            archivo_erp.headers_clasificados = headers_clasificados
            archivo_erp.save(update_fields=['headers_clasificados'])
            
            # Si todos están clasificados, cambiar a LISTO
            if headers_clasificados >= len(headers_monetarios):
                archivo_erp.estado = EstadoArchivoLibro.LISTO
                archivo_erp.save(update_fields=['estado'])
            
            return ServiceResult.ok(headers_monetarios)
            
        except Exception as e:
            logger.error(f"Error extrayendo headers: {e}", exc_info=True)
            archivo_erp.estado = EstadoArchivoLibro.ERROR
            archivo_erp.error_mensaje = str(e)
            archivo_erp.save(update_fields=['estado', 'error_mensaje'])
            return ServiceResult.fail(f"Error extrayendo headers: {str(e)}")
    
    @classmethod
    @transaction.atomic
    def _sincronizar_conceptos(cls, archivo_erp: ArchivoERP, headers: List[str]):
        """
        Crea o actualiza ConceptoLibro para cada header encontrado.
        Maneja headers duplicados correctamente.
        
        Args:
            archivo_erp: Archivo de donde vienen los headers
            headers: Lista de headers a sincronizar (nombres como pandas los lee)
        """
        cierre = archivo_erp.cierre
        config_erp = cierre.cliente.configuraciones_erp.filter(activo=True).first()
        
        if not config_erp:
            return
        
        # Re-extraer headers con info de duplicados
        parser = ParserFactory.get_parser_for_cliente(cierre.cliente)
        if not parser:
            return
        
        try:
            # Leer archivo para analizar headers
            if archivo_erp.archivo.path.endswith('.csv'):
                import pandas as pd
                df = pd.read_csv(archivo_erp.archivo.path, nrows=0)
            else:
                df = parser.leer_excel(archivo_erp.archivo.path, sheet_name=0, header=0, nrows=0)
            
            headers_info = parser.analizar_headers_duplicados(df.columns)
        except Exception as e:
            cls.get_logger().warning(f"No se pudo analizar headers para duplicados: {e}")
            # Fallback: tratar todos como únicos
            from ..parsers.base import HeaderInfo
            headers_info = [
                HeaderInfo(original=h, pandas_name=h, occurrence=1, is_duplicate=False)
                for h in headers
            ]
        
        # Contador de headers omitidos (datos de empleado)
        headers_omitidos = 0
        
        for orden, header_info in enumerate(headers_info):
            # Si el parser indica que es un header de empleado (no monetario), omitirlo
            # Estos datos se usarán al procesar el libro para crear EmpleadoLibro
            if hasattr(parser, 'es_header_empleado') and parser.es_header_empleado(orden):
                headers_omitidos += 1
                continue
            
            # Crear o actualizar concepto (solo conceptos monetarios)
            concepto, created = ConceptoLibro.objects.get_or_create(
                cliente=cierre.cliente,
                erp=config_erp.erp,
                header_original=header_info.original,
                ocurrencia=header_info.occurrence,
                defaults={
                    'header_pandas': header_info.pandas_name,
                    'es_duplicado': header_info.is_duplicate,
                    'orden': orden,
                    'activo': True,
                }
            )
            
            if not created:
                # Actualizar campos si cambió algo
                updated = False
                if concepto.orden != orden:
                    concepto.orden = orden
                    updated = True
                if concepto.header_pandas != header_info.pandas_name:
                    concepto.header_pandas = header_info.pandas_name
                    updated = True
                if concepto.es_duplicado != header_info.is_duplicate:
                    concepto.es_duplicado = header_info.is_duplicate
                    updated = True
                
                if updated:
                    concepto.save(update_fields=['orden', 'header_pandas', 'es_duplicado'])
        
        if headers_omitidos:
            cls.get_logger().info(
                f"Omitidos {headers_omitidos} headers de empleado para {archivo_erp}"
            )

    
    @classmethod
    @transaction.atomic
    def clasificar_conceptos(
        cls,
        archivo_erp: ArchivoERP,
        clasificaciones: List[Dict],
        user
    ) -> ServiceResult:
        """
        Clasifica los conceptos del libro.
        
        Args:
            archivo_erp: Archivo del libro
            clasificaciones: Lista de dicts con estructura:
                [
                    {
                        'header': 'SUELDO BASE',
                        'categoria': 'haberes_imponibles'
                    },
                    ...
                ]
            user: Usuario que realiza la clasificación
        
        Returns:
            ServiceResult con info de clasificación o error
        """
        logger = cls.get_logger()
        
        try:
            # Validar estado
            if not EstadoArchivoLibro.puede_clasificar(archivo_erp.estado):
                return ServiceResult.fail(
                    f"No se puede clasificar en estado '{archivo_erp.estado}'"
                )
            
            cierre = archivo_erp.cierre
            config_erp = cierre.cliente.configuraciones_erp.filter(activo=True).first()
            
            if not config_erp:
                return ServiceResult.fail("Cliente no tiene ERP configurado")
            
            # Clasificar cada concepto
            clasificados = 0
            for clas in clasificaciones:
                # Puede venir header (pandas_name) o header_pandas
                header = clas.get('header') or clas.get('header_pandas')
                ocurrencia = clas.get('ocurrencia', 1)
                categoria = clas.get('categoria')
                
                # Validar categoría
                if not CategoriaConceptoLibro.es_valido(categoria):
                    logger.warning(f"Categoría inválida '{categoria}' para header '{header}'")
                    continue
                
                # Actualizar concepto
                # Intentar por header_pandas primero, luego por header_original + ocurrencia
                try:
                    # Buscar por header_pandas (más específico)
                    concepto = ConceptoLibro.objects.filter(
                        cliente=cierre.cliente,
                        erp=config_erp.erp,
                        header_pandas=header
                    ).first()
                    
                    # Si no se encuentra, buscar por header_original + ocurrencia
                    if not concepto:
                        # Extraer original de header (remover .1, .2, etc)
                        import re
                        match = re.match(r'^(.+)\.(\d+)$', header)
                        if match:
                            original = match.group(1)
                            ocurrencia = int(match.group(2)) + 1
                        else:
                            original = header
                        
                        concepto = ConceptoLibro.objects.get(
                            cliente=cierre.cliente,
                            erp=config_erp.erp,
                            header_original=original,
                            ocurrencia=ocurrencia
                        )
                    
                    concepto.categoria = categoria
                    concepto.creado_por = user
                    concepto.fecha_actualizacion = timezone.now()
                    concepto.save()
                    
                    clasificados += 1
                    
                except ConceptoLibro.DoesNotExist:
                    logger.warning(f"Concepto no encontrado para header '{header}'")
                    continue
            
            logger.info(f"Clasificados {clasificados} conceptos para {archivo_erp}")
            
            # Actualizar contador en archivo
            archivo_erp.headers_clasificados = ConceptoLibro.objects.filter(
                cliente=cierre.cliente,
                erp=config_erp.erp,
                categoria__isnull=False
            ).count()
            
            # Si todos están clasificados, cambiar estado a LISTO
            if archivo_erp.todos_headers_clasificados:
                archivo_erp.estado = EstadoArchivoLibro.LISTO
            
            archivo_erp.save(update_fields=['headers_clasificados', 'estado'])
            
            cls.log_action(
                'clasificar_conceptos',
                'archivo_erp',
                archivo_erp.id,
                user,
                {'clasificados': clasificados}
            )
            
            return ServiceResult.ok({
                'clasificados': clasificados,
                'total': archivo_erp.headers_total,
                'progreso': archivo_erp.progreso_clasificacion,
                'listo_para_procesar': archivo_erp.todos_headers_clasificados
            })
            
        except Exception as e:
            logger.error(f"Error clasificando conceptos: {e}", exc_info=True)
            return ServiceResult.fail(f"Error clasificando conceptos: {str(e)}")
    
    @classmethod
    @transaction.atomic
    def procesar_libro(
        cls, 
        archivo_erp: ArchivoERP,
        progress_callback: callable = None
    ) -> ServiceResult:
        """
        Procesa el libro completo y crea EmpleadoLibro + RegistroLibro.
        
        Arquitectura Medallion - Capa Bronce:
        - EmpleadoLibro: identificación del empleado (rut, nombre)
        - RegistroLibro: un registro por cada concepto con monto > 0
        
        Args:
            archivo_erp: Archivo del libro a procesar
            progress_callback: Función opcional para reportar progreso.
                Signature: callback(progreso: int, mensaje: str, empleados: int = 0)
                - progreso: 0-100
                - mensaje: descripción del estado actual
                - empleados: cantidad de empleados procesados (opcional)
        
        Returns:
            ServiceResult con estadísticas o error
        """
        from apps.validador.models import RegistroLibro
        
        logger = cls.get_logger()
        
        def report_progress(progreso: int, mensaje: str, empleados: int = 0):
            """Helper para reportar progreso si hay callback."""
            if progress_callback:
                try:
                    progress_callback(progreso, mensaje, empleados)
                except Exception as e:
                    logger.warning(f"Error en progress_callback: {e}")
        
        try:
            # Validar estado
            if not EstadoArchivoLibro.puede_procesar(archivo_erp.estado):
                return ServiceResult.fail(
                    f"No se puede procesar en estado '{archivo_erp.estado}'"
                )
            
            # Validar que todos los headers están clasificados
            if not archivo_erp.todos_headers_clasificados:
                return ServiceResult.fail(
                    f"Faltan {archivo_erp.headers_total - archivo_erp.headers_clasificados} "
                    "headers por clasificar"
                )
            
            report_progress(5, "Preparando procesamiento...")
            
            # Actualizar estado
            archivo_erp.estado = EstadoArchivoLibro.PROCESANDO
            archivo_erp.save(update_fields=['estado'])
            
            # Obtener parser
            cierre = archivo_erp.cierre
            parser = ParserFactory.get_parser_for_cliente(cierre.cliente)
            
            if not parser:
                archivo_erp.estado = EstadoArchivoLibro.ERROR
                archivo_erp.error_mensaje = "No hay parser disponible"
                archivo_erp.save(update_fields=['estado', 'error_mensaje'])
                return ServiceResult.fail("No hay parser disponible")
            
            report_progress(10, "Leyendo archivo Excel...")
            
            # Obtener conceptos clasificados
            config_erp = cierre.cliente.configuraciones_erp.filter(activo=True).first()
            conceptos_qs = ConceptoLibro.objects.filter(
                cliente=cierre.cliente,
                erp=config_erp.erp,
                activo=True
            )
            
            # Crear dict {header_pandas: ConceptoLibro} para mapeo correcto con duplicados
            conceptos_clasificados = {
                c.header_pandas if c.header_pandas else c.header_original: c 
                for c in conceptos_qs
            }
            
            report_progress(15, "Parseando empleados del libro...")
            
            # Procesar libro
            result = parser.procesar_libro(
                archivo_erp.archivo.path,
                conceptos_clasificados
            )
            
            if not result.success:
                archivo_erp.estado = EstadoArchivoLibro.ERROR
                archivo_erp.error_mensaje = result.error
                archivo_erp.save(update_fields=['estado', 'error_mensaje'])
                return ServiceResult.fail(result.error)
            
            total_empleados = len(result.data)
            report_progress(30, f"Procesando {total_empleados} empleados...", 0)
            
            # Limpiar empleados y registros previos de este archivo
            EmpleadoLibro.objects.filter(
                cierre=cierre,
                archivo_erp=archivo_erp
            ).delete()
            
            report_progress(35, "Creando registros de empleados...")
            
            # 1. Crear EmpleadoLibro para cada empleado (solo rut, nombre)
            empleados_a_crear = []
            for emp_data in result.data:
                empleado = EmpleadoLibro(
                    cierre=cierre,
                    archivo_erp=archivo_erp,
                    rut=emp_data['rut'],
                    nombre=emp_data.get('nombre', ''),
                )
                empleados_a_crear.append(empleado)
            
            # Bulk create empleados (PostgreSQL retorna IDs)
            empleados_creados = EmpleadoLibro.objects.bulk_create(
                empleados_a_crear, 
                batch_size=500
            )
            
            report_progress(50, f"{len(empleados_creados)} empleados creados, procesando conceptos...", len(empleados_creados))
            
            # 2. Mapear RUT → EmpleadoLibro para asignar FK a registros
            empleados_por_rut = {e.rut: e for e in empleados_creados}
            
            # 3. Crear RegistroLibro para cada concepto con monto > 0
            registros_a_crear = []
            total_registros = 0
            empleados_procesados = 0
            
            for idx, emp_data in enumerate(result.data):
                empleado = empleados_por_rut.get(emp_data['rut'])
                if not empleado:
                    continue
                
                for reg in emp_data.get('registros', []):
                    registro = RegistroLibro(
                        cierre=cierre,
                        empleado=empleado,
                        concepto=reg['concepto'],
                        monto=reg['monto'],
                    )
                    registros_a_crear.append(registro)
                    total_registros += 1
                
                empleados_procesados += 1
                
                # Reportar progreso cada 50 empleados o al final
                if empleados_procesados % 50 == 0 or empleados_procesados == total_empleados:
                    # Progreso de 50% a 90% proporcional a empleados procesados
                    progreso = 50 + int((empleados_procesados / total_empleados) * 40)
                    report_progress(
                        progreso, 
                        f"Procesando conceptos: {empleados_procesados}/{total_empleados} empleados...",
                        empleados_procesados
                    )
            
            report_progress(90, f"Guardando {total_registros} registros en base de datos...")
            
            # Bulk create registros
            if registros_a_crear:
                RegistroLibro.objects.bulk_create(
                    registros_a_crear, 
                    batch_size=1000
                )
            
            report_progress(95, "Finalizando procesamiento...")
            
            # Actualizar archivo
            archivo_erp.empleados_procesados = len(empleados_creados)
            archivo_erp.estado = EstadoArchivoLibro.PROCESADO
            archivo_erp.fecha_procesamiento = timezone.now()
            archivo_erp.save(update_fields=[
                'empleados_procesados', 'estado', 'fecha_procesamiento'
            ])
            
            logger.info(
                f"Libro procesado: {len(empleados_creados)} empleados, "
                f"{total_registros} registros creados"
            )
            
            cls.log_action(
                'procesar_libro',
                'archivo_erp',
                archivo_erp.id,
                None,
                {
                    'empleados_procesados': len(empleados_creados),
                    'registros_creados': total_registros,
                    'warnings': len(result.warnings)
                }
            )
            
            report_progress(100, "Procesamiento completado", len(empleados_creados))
            
            return ServiceResult.ok({
                'empleados_procesados': len(empleados_creados),
                'registros_creados': total_registros,
                'total_filas': result.metadata.get('total_filas', 0),
                'errores': result.metadata.get('errores', 0),
                'warnings': result.warnings,
            })
            
        except Exception as e:
            logger.error(f"Error procesando libro: {e}", exc_info=True)
            archivo_erp.estado = EstadoArchivoLibro.ERROR
            archivo_erp.error_mensaje = str(e)
            archivo_erp.save(update_fields=['estado', 'error_mensaje'])
            return ServiceResult.fail(f"Error procesando libro: {str(e)}")
    
    @classmethod
    def obtener_conceptos_pendientes(cls, archivo_erp: ArchivoERP) -> ServiceResult[List[Dict]]:
        """
        Obtiene la lista de conceptos pendientes de clasificación con sugerencias.
        
        Args:
            archivo_erp: Archivo del libro
        
        Returns:
            ServiceResult con lista de conceptos pendientes, incluyendo sugerencias
        """
        try:
            cierre = archivo_erp.cierre
            config_erp = cierre.cliente.configuraciones_erp.filter(activo=True).first()
            
            if not config_erp:
                return ServiceResult.fail("Cliente no tiene ERP configurado")
            
            # Obtener conceptos sin clasificar
            conceptos_pendientes = ConceptoLibro.objects.filter(
                cliente=cierre.cliente,
                erp=config_erp.erp,
                categoria__isnull=True,
                activo=True
            ).order_by('orden')
            
            # Obtener sugerencias basadas en clasificaciones previas del mismo cliente/ERP
            sugerencias = cls._obtener_sugerencias_clasificacion(cierre.cliente, config_erp.erp)
            
            data = []
            for c in conceptos_pendientes:
                concepto_dict = {
                    'id': c.id,
                    'header': c.header_pandas if c.header_pandas else c.header_original,
                    'header_original': c.header_original,
                    'header_pandas': c.header_pandas,
                    'ocurrencia': c.ocurrencia,
                    'es_duplicado': c.es_duplicado,
                    'orden': c.orden,
                    'categoria': c.categoria,
                }
                
                # Agregar sugerencia si existe
                if c.header_original in sugerencias:
                    concepto_dict['sugerencia'] = sugerencias[c.header_original]
                
                data.append(concepto_dict)
            
            return ServiceResult.ok(data)
            
        except Exception as e:
            cls.get_logger().error(f"Error obteniendo conceptos pendientes: {e}")
            return ServiceResult.fail(str(e))
    
    @classmethod
    def _obtener_sugerencias_clasificacion(cls, cliente, erp) -> Dict[str, Dict]:
        """
        Obtiene sugerencias de clasificación basadas en conceptos previamente clasificados.
        
        Args:
            cliente: Cliente
            erp: ERP
        
        Returns:
            Dict {header_original: {'categoria': str, 'frecuencia': int}}
        """
        # Obtener conceptos clasificados del mismo cliente/ERP
        conceptos_clasificados = ConceptoLibro.objects.filter(
            cliente=cliente,
            erp=erp,
            categoria__isnull=False,
            activo=True
        ).values('header_original', 'categoria')
        
        # Agrupar por header_original y contar frecuencia
        sugerencias = {}
        for c in conceptos_clasificados:
            header = c['header_original']
            if header not in sugerencias:
                sugerencias[header] = {
                    'categoria': c['categoria'],
                    'frecuencia': 1
                }
            else:
                sugerencias[header]['frecuencia'] += 1
        
        return sugerencias
    
    @classmethod
    def aplicar_clasificacion_automatica(cls, archivo_erp: ArchivoERP, user) -> ServiceResult:
        """
        Aplica automáticamente las clasificaciones basadas en conceptos previamente clasificados.
        
        Args:
            archivo_erp: Archivo del libro
            user: Usuario que aplica la clasificación automática
        
        Returns:
            ServiceResult con cantidad de conceptos clasificados automáticamente
        """
        logger = cls.get_logger()
        
        try:
            cierre = archivo_erp.cierre
            config_erp = cierre.cliente.configuraciones_erp.filter(activo=True).first()
            
            if not config_erp:
                return ServiceResult.fail("Cliente no tiene ERP configurado")
            
            # Obtener sugerencias
            sugerencias = cls._obtener_sugerencias_clasificacion(cierre.cliente, config_erp.erp)
            
            # Obtener conceptos pendientes
            conceptos_pendientes = ConceptoLibro.objects.filter(
                cliente=cierre.cliente,
                erp=config_erp.erp,
                categoria__isnull=True,
                activo=True
            )
            
            clasificados_auto = 0
            for concepto in conceptos_pendientes:
                if concepto.header_original in sugerencias:
                    sugerencia = sugerencias[concepto.header_original]
                    concepto.categoria = sugerencia['categoria']
                    concepto.creado_por = user
                    concepto.fecha_actualizacion = timezone.now()
                    concepto.save()
                    clasificados_auto += 1
            
            logger.info(f"Clasificados automáticamente {clasificados_auto} conceptos")
            
            # Actualizar contador en archivo
            archivo_erp.headers_clasificados = ConceptoLibro.objects.filter(
                cliente=cierre.cliente,
                erp=config_erp.erp,
                categoria__isnull=False
            ).count()
            
            # Si todos están clasificados, cambiar estado a LISTO
            if archivo_erp.todos_headers_clasificados:
                archivo_erp.estado = EstadoArchivoLibro.LISTO
            
            archivo_erp.save(update_fields=['headers_clasificados', 'estado'])
            
            cls.log_action(
                'clasificacion_automatica',
                'archivo_erp',
                archivo_erp.id,
                user,
                {'clasificados_auto': clasificados_auto}
            )
            
            return ServiceResult.ok({
                'clasificados_auto': clasificados_auto,
                'total_clasificados': archivo_erp.headers_clasificados,
                'total_headers': archivo_erp.headers_total,
                'listo_para_procesar': archivo_erp.todos_headers_clasificados
            })
            
        except Exception as e:
            logger.error(f"Error en clasificación automática: {e}", exc_info=True)
            return ServiceResult.fail(f"Error en clasificación automática: {str(e)}")
