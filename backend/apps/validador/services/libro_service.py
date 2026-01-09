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
            
            # Actualizar archivo
            archivo_erp.headers_total = len(headers)
            archivo_erp.estado = EstadoArchivoLibro.PENDIENTE_CLASIFICACION
            archivo_erp.save(update_fields=['headers_total', 'estado'])
            
            # Crear/actualizar conceptos en BD
            cls._sincronizar_conceptos(archivo_erp, headers)
            
            # Contar clasificados
            headers_clasificados = ConceptoLibro.objects.filter(
                cliente=cierre.cliente,
                erp=cierre.cliente.configuraciones_erp.filter(activo=True).first().erp,
                header_original__in=headers,
                categoria__isnull=False
            ).count()
            
            archivo_erp.headers_clasificados = headers_clasificados
            archivo_erp.save(update_fields=['headers_clasificados'])
            
            # Si todos están clasificados, cambiar a LISTO
            if headers_clasificados >= len(headers):
                archivo_erp.estado = EstadoArchivoLibro.LISTO
                archivo_erp.save(update_fields=['estado'])
            
            return ServiceResult.ok(headers)
            
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
        
        Args:
            archivo_erp: Archivo de donde vienen los headers
            headers: Lista de headers a sincronizar
        """
        cierre = archivo_erp.cierre
        config_erp = cierre.cliente.configuraciones_erp.filter(activo=True).first()
        
        if not config_erp:
            return
        
        for orden, header in enumerate(headers):
            # Crear o actualizar concepto
            concepto, created = ConceptoLibro.objects.get_or_create(
                cliente=cierre.cliente,
                erp=config_erp.erp,
                header_original=header,
                defaults={
                    'orden': orden,
                    'activo': True,
                }
            )
            
            if not created and concepto.orden != orden:
                # Actualizar orden si cambió
                concepto.orden = orden
                concepto.save(update_fields=['orden'])
    
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
                        'categoria': 'haberes_imponibles',
                        'es_identificador': False
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
                header = clas.get('header')
                categoria = clas.get('categoria')
                es_identificador = clas.get('es_identificador', False)
                
                # Validar categoría
                if not CategoriaConceptoLibro.es_valido(categoria):
                    logger.warning(f"Categoría inválida '{categoria}' para header '{header}'")
                    continue
                
                # Actualizar concepto
                try:
                    concepto = ConceptoLibro.objects.get(
                        cliente=cierre.cliente,
                        erp=config_erp.erp,
                        header_original=header
                    )
                    
                    concepto.categoria = categoria
                    concepto.es_identificador = es_identificador
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
    def procesar_libro(cls, archivo_erp: ArchivoERP) -> ServiceResult:
        """
        Procesa el libro completo y crea EmpleadoLibro para cada empleado.
        
        Args:
            archivo_erp: Archivo del libro a procesar
        
        Returns:
            ServiceResult con estadísticas o error
        """
        logger = cls.get_logger()
        
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
            
            # Obtener conceptos clasificados
            config_erp = cierre.cliente.configuraciones_erp.filter(activo=True).first()
            conceptos_qs = ConceptoLibro.objects.filter(
                cliente=cierre.cliente,
                erp=config_erp.erp,
                activo=True
            )
            
            # Crear dict {header: ConceptoLibro}
            conceptos_clasificados = {
                c.header_original: c for c in conceptos_qs
            }
            
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
            
            # Limpiar empleados previos de este archivo
            EmpleadoLibro.objects.filter(
                cierre=cierre,
                archivo_erp=archivo_erp
            ).delete()
            
            # Crear EmpleadoLibro para cada empleado
            empleados_a_crear = []
            for emp_data in result.data:
                empleado = EmpleadoLibro(
                    cierre=cierre,
                    archivo_erp=archivo_erp,
                    rut=emp_data['rut'],
                    nombre=emp_data.get('nombre', ''),
                    cargo=emp_data.get('cargo', ''),
                    centro_costo=emp_data.get('centro_costo', ''),
                    area=emp_data.get('area', ''),
                    fecha_ingreso=emp_data.get('fecha_ingreso'),
                    datos_json=emp_data['datos_json'],
                    total_haberes_imponibles=emp_data.get('total_haberes_imponibles', Decimal('0')),
                    total_haberes_no_imponibles=emp_data.get('total_haberes_no_imponibles', Decimal('0')),
                    total_descuentos_legales=emp_data.get('total_descuentos_legales', Decimal('0')),
                    total_otros_descuentos=emp_data.get('total_otros_descuentos', Decimal('0')),
                    total_aportes_patronales=emp_data.get('total_aportes_patronales', Decimal('0')),
                    total_liquido=emp_data.get('total_liquido', Decimal('0')),
                )
                empleados_a_crear.append(empleado)
            
            # Bulk create
            EmpleadoLibro.objects.bulk_create(empleados_a_crear, batch_size=500)
            
            # Actualizar archivo
            archivo_erp.empleados_procesados = len(empleados_a_crear)
            archivo_erp.estado = EstadoArchivoLibro.PROCESADO
            archivo_erp.fecha_procesamiento = timezone.now()
            archivo_erp.save(update_fields=[
                'empleados_procesados', 'estado', 'fecha_procesamiento'
            ])
            
            logger.info(f"Libro procesado: {len(empleados_a_crear)} empleados creados")
            
            cls.log_action(
                'procesar_libro',
                'archivo_erp',
                archivo_erp.id,
                None,
                {
                    'empleados_procesados': len(empleados_a_crear),
                    'warnings': len(result.warnings)
                }
            )
            
            return ServiceResult.ok({
                'empleados_procesados': len(empleados_a_crear),
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
        Obtiene la lista de conceptos pendientes de clasificación.
        
        Args:
            archivo_erp: Archivo del libro
        
        Returns:
            ServiceResult con lista de conceptos pendientes
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
            
            data = [
                {
                    'id': c.id,
                    'header': c.header_original,
                    'orden': c.orden,
                    'categoria': c.categoria,
                }
                for c in conceptos_pendientes
            ]
            
            return ServiceResult.ok(data)
            
        except Exception as e:
            cls.get_logger().error(f"Error obteniendo conceptos pendientes: {e}")
            return ServiceResult.fail(str(e))
