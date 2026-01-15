"""
CierreService - Lógica de negocio para Cierres.

Centraliza toda la lógica de:
- Cambios de estado
- Validaciones de transiciones
- Consolidación
- Detección de incidencias
- Finalización

Flujo de estados (7 principales):
    CARGA_ARCHIVOS → [Generar Comparación] → CON/SIN_DISCREPANCIAS
    SIN_DISCREPANCIAS → [Click manual] → CONSOLIDADO
    CONSOLIDADO → [Detectar Incidencias manual] → CON/SIN_INCIDENCIAS
    SIN_INCIDENCIAS → [Finalizar] → FINALIZADO
"""

from django.utils import timezone
from django.db import transaction
from typing import Optional, List, Dict, Any

from .base import BaseService, ServiceResult
from ..models import Cierre
from ..constants import EstadoCierre


class CierreService(BaseService):
    """
    Servicio para gestión de Cierres.
    
    Ejemplo de uso:
        from apps.validador.services import CierreService
        from apps.validador.constants import EstadoCierre
        
        result = CierreService.cambiar_estado(cierre, EstadoCierre.CONSOLIDADO, user)
        if result.success:
            cierre_actualizado = result.data
    """
    
    # Transiciones de estado permitidas (nuevo flujo de 7 estados)
    TRANSICIONES_VALIDAS = {
        # Desde hub de carga → comparación genera discrepancias o no
        EstadoCierre.CARGA_ARCHIVOS: [
            EstadoCierre.CON_DISCREPANCIAS,
            EstadoCierre.SIN_DISCREPANCIAS,
        ],
        # Puede volver a carga o pasar a sin_discrepancias al resolver todas
        EstadoCierre.CON_DISCREPANCIAS: [
            EstadoCierre.CARGA_ARCHIVOS,      # Volver a corregir archivos
            EstadoCierre.SIN_DISCREPANCIAS,   # Al resolver todas las discrepancias
        ],
        # Requiere click manual para consolidar, puede volver a carga
        EstadoCierre.SIN_DISCREPANCIAS: [
            EstadoCierre.CONSOLIDADO,         # Click manual
            EstadoCierre.CARGA_ARCHIVOS,      # Volver a corregir
        ],
        # Desde consolidado → detectar incidencias (manual)
        EstadoCierre.CONSOLIDADO: [
            EstadoCierre.CON_INCIDENCIAS,
            EstadoCierre.SIN_INCIDENCIAS,
        ],
        # Resolver incidencias lleva a sin_incidencias
        EstadoCierre.CON_INCIDENCIAS: [
            EstadoCierre.SIN_INCIDENCIAS,     # Al resolver todas
        ],
        # Desde sin_incidencias → finalizar
        EstadoCierre.SIN_INCIDENCIAS: [
            EstadoCierre.FINALIZADO,
        ],
        # Estados finales
        EstadoCierre.FINALIZADO: [],
        EstadoCierre.CANCELADO: [],
        # Desde error se puede volver a carga
        EstadoCierre.ERROR: [
            EstadoCierre.CARGA_ARCHIVOS,
        ],
    }
    
    @classmethod
    def puede_transicionar(cls, estado_actual: str, estado_nuevo: str) -> bool:
        """Verificar si una transición de estado es válida."""
        transiciones = cls.TRANSICIONES_VALIDAS.get(estado_actual, [])
        return estado_nuevo in transiciones
    
    @classmethod
    def cambiar_estado(
        cls, 
        cierre: Cierre, 
        nuevo_estado: str, 
        user=None,
        validar_transicion: bool = True
    ) -> ServiceResult[Cierre]:
        """
        Cambiar el estado de un cierre.
        
        Args:
            cierre: Instancia de Cierre
            nuevo_estado: Estado destino
            user: Usuario que realiza el cambio
            validar_transicion: Si True, valida que la transición sea permitida
            
        Returns:
            ServiceResult con el cierre actualizado o error
        """
        logger = cls.get_logger()
        estado_anterior = cierre.estado
        
        # Validar estado válido
        estados_validos = dict(Cierre.ESTADO_CHOICES).keys()
        if nuevo_estado not in estados_validos:
            return ServiceResult.fail(
                f'Estado inválido. Estados válidos: {list(estados_validos)}'
            )
        
        # Validar transición permitida
        if validar_transicion and not cls.puede_transicionar(estado_anterior, nuevo_estado):
            return ServiceResult.fail(
                f'No se puede cambiar de "{estado_anterior}" a "{nuevo_estado}"'
            )
        
        try:
            with transaction.atomic():
                cierre.estado = nuevo_estado
                
                # Actualizar campos según el nuevo estado
                if nuevo_estado == EstadoCierre.CONSOLIDADO:
                    cierre.fecha_consolidacion = timezone.now()
                elif nuevo_estado == EstadoCierre.FINALIZADO:
                    cierre.fecha_finalizacion = timezone.now()
                    if user:
                        cierre.finalizado_por = user
                
                cierre.save()
                
                # Log de auditoría
                cls.log_action(
                    action='cambio_estado',
                    entity_type='cierre',
                    entity_id=cierre.id,
                    user=user,
                    extra={
                        'estado_anterior': estado_anterior,
                        'estado_nuevo': nuevo_estado,
                    }
                )
                
                logger.info(
                    f"Cierre {cierre.id} cambió de '{estado_anterior}' a '{nuevo_estado}'"
                )
                
                return ServiceResult.ok(cierre)
                
        except Exception as e:
            logger.error(f"Error al cambiar estado del cierre {cierre.id}: {str(e)}")
            return ServiceResult.fail(f'Error al cambiar estado: {str(e)}')
    
    @classmethod
    def generar_comparacion(cls, cierre: Cierre, user=None) -> ServiceResult[Cierre]:
        """
        Generar comparación ERP vs Novedades.
        
        Validaciones:
        - Debe estar en estado CARGA_ARCHIVOS
        - Libro ERP debe estar procesado
        - Todos los conceptos clasificados
        - Novedades procesadas
        - Todos los headers mapeados
        
        Returns:
            ServiceResult con cierre en estado CON_DISCREPANCIAS o SIN_DISCREPANCIAS
        """
        logger = cls.get_logger()
        
        # Validar estado actual
        if cierre.estado != EstadoCierre.CARGA_ARCHIVOS:
            return ServiceResult.fail(
                f'Solo se puede generar comparación desde estado "carga_archivos". '
                f'Estado actual: {cierre.estado}'
            )
        
        try:
            with transaction.atomic():
                # TODO: Validar prerrequisitos
                # - Libro ERP procesado
                # - Conceptos clasificados
                # - Novedades procesadas
                # - Headers mapeados
                
                # TODO: Ejecutar task de comparación real
                # Por ahora, verificamos si hay discrepancias existentes
                tiene_discrepancias = cierre.discrepancias.exists()
                
                if tiene_discrepancias:
                    nuevo_estado = EstadoCierre.CON_DISCREPANCIAS
                else:
                    nuevo_estado = EstadoCierre.SIN_DISCREPANCIAS
                
                result = cls.cambiar_estado(cierre, nuevo_estado, user)
                
                if result.success:
                    logger.info(
                        f"Cierre {cierre.id} comparación generada. "
                        f"Discrepancias: {tiene_discrepancias}. Estado: {nuevo_estado}"
                    )
                
                return result
                
        except Exception as e:
            logger.error(f"Error al generar comparación en cierre {cierre.id}: {str(e)}")
            return ServiceResult.fail(f'Error al generar comparación: {str(e)}')
    
    @classmethod
    def consolidar(cls, cierre: Cierre, user=None) -> ServiceResult[Cierre]:
        """
        Consolidar un cierre (transición manual desde SIN_DISCREPANCIAS).
        
        Validaciones:
        - Debe estar en estado SIN_DISCREPANCIAS
        - No debe haber discrepancias pendientes
        
        Esta transición es SIEMPRE manual - el analista debe confirmar.
        """
        logger = cls.get_logger()
        
        # Validar estado actual
        if cierre.estado != EstadoCierre.SIN_DISCREPANCIAS:
            return ServiceResult.fail(
                f'Solo se puede consolidar desde estado "sin_discrepancias". Estado actual: {cierre.estado}'
            )
        
        # Validar que no haya discrepancias pendientes
        if cierre.total_discrepancias > cierre.discrepancias_resueltas:
            return ServiceResult.fail(
                'No se puede consolidar. Aún hay discrepancias pendientes.'
            )
        
        try:
            result = cls.cambiar_estado(cierre, EstadoCierre.CONSOLIDADO, user)
            
            if result.success:
                logger.info(f"Cierre {cierre.id} consolidado por {user}")
                
            return result
            
        except Exception as e:
            logger.error(f"Error al consolidar cierre {cierre.id}: {str(e)}")
            return ServiceResult.fail(f'Error al consolidar: {str(e)}')
    
    @classmethod
    def detectar_incidencias(cls, cierre: Cierre, user=None) -> ServiceResult[Cierre]:
        """
        Detectar incidencias (transición manual desde CONSOLIDADO).
        
        Validaciones:
        - Debe estar en estado CONSOLIDADO
        
        Cambia a CON_INCIDENCIAS o SIN_INCIDENCIAS según el resultado.
        """
        logger = cls.get_logger()
        
        # Validar estado actual
        if cierre.estado != EstadoCierre.CONSOLIDADO:
            return ServiceResult.fail(
                f'Solo se puede detectar incidencias desde estado "consolidado". Estado actual: {cierre.estado}'
            )
        
        try:
            with transaction.atomic():
                # TODO: Ejecutar lógica de detección de incidencias
                # Por ahora, verificamos si ya hay incidencias creadas
                tiene_incidencias = cierre.incidencias.exists()
                
                if tiene_incidencias:
                    nuevo_estado = EstadoCierre.CON_INCIDENCIAS
                else:
                    nuevo_estado = EstadoCierre.SIN_INCIDENCIAS
                
                result = cls.cambiar_estado(cierre, nuevo_estado, user)
                
                if result.success:
                    logger.info(
                        f"Cierre {cierre.id} detectó incidencias: {tiene_incidencias}. "
                        f"Nuevo estado: {nuevo_estado}"
                    )
                
                return result
                
        except Exception as e:
            logger.error(f"Error al detectar incidencias en cierre {cierre.id}: {str(e)}")
            return ServiceResult.fail(f'Error al detectar incidencias: {str(e)}')
    
    @classmethod
    def finalizar(cls, cierre: Cierre, user=None) -> ServiceResult[Cierre]:
        """
        Finalizar un cierre.
        
        Validaciones:
        - Debe estar en estado SIN_INCIDENCIAS
        """
        logger = cls.get_logger()
        
        if cierre.estado != EstadoCierre.SIN_INCIDENCIAS:
            return ServiceResult.fail(
                f'Solo se puede finalizar desde estado "sin_incidencias". Estado actual: {cierre.estado}'
            )
        
        try:
            result = cls.cambiar_estado(cierre, EstadoCierre.FINALIZADO, user)
            
            if result.success:
                logger.info(f"Cierre {cierre.id} finalizado por {user}")
                
            return result
            
        except Exception as e:
            logger.error(f"Error al finalizar cierre {cierre.id}: {str(e)}")
            return ServiceResult.fail(f'Error al finalizar: {str(e)}')
    
    @classmethod
    def volver_a_carga(cls, cierre: Cierre, user=None) -> ServiceResult[Cierre]:
        """
        Volver a estado CARGA_ARCHIVOS para corregir archivos.
        
        Permitido desde:
        - CON_DISCREPANCIAS
        - SIN_DISCREPANCIAS
        """
        logger = cls.get_logger()
        
        if not EstadoCierre.puede_retroceder(cierre.estado):
            return ServiceResult.fail(
                f'No se puede volver a carga desde estado "{cierre.estado}"'
            )
        
        try:
            result = cls.cambiar_estado(cierre, EstadoCierre.CARGA_ARCHIVOS, user)
            
            if result.success:
                logger.info(f"Cierre {cierre.id} volvió a carga_archivos por {user}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error al volver a carga cierre {cierre.id}: {str(e)}")
            return ServiceResult.fail(f'Error al volver a carga: {str(e)}')
    
    @classmethod
    def obtener_resumen(cls, cierre: Cierre) -> Dict[str, Any]:
        """
        Obtener resumen completo del estado de un cierre.
        
        Returns:
            Diccionario con estado de archivos, discrepancias, incidencias, etc.
        """
        archivos_erp = cierre.archivos_erp.filter(es_version_actual=True)
        archivos_analista = cierre.archivos_analista.filter(es_version_actual=True)
        
        return {
            'id': cierre.id,
            'cliente': {
                'id': cierre.cliente.id,
                'nombre': cierre.cliente.nombre_comercial or cierre.cliente.razon_social,
            },
            'periodo': cierre.periodo,
            'estado': cierre.estado,
            'estado_display': cierre.get_estado_display(),
            
            'archivos': {
                'erp': {
                    'libro_remuneraciones': archivos_erp.filter(tipo='libro_remuneraciones').exists(),
                    'movimientos_mes': archivos_erp.filter(tipo='movimientos_mes').exists(),
                },
                'analista': {
                    'novedades': archivos_analista.filter(tipo='novedades').exists(),
                    'asistencias': archivos_analista.filter(tipo='asistencias').exists(),
                    'finiquitos': archivos_analista.filter(tipo='finiquitos').exists(),
                    'ingresos': archivos_analista.filter(tipo='ingresos').exists(),
                },
            },
            
            'clasificacion': {
                'requiere': cierre.requiere_clasificacion,
                'conceptos_sin_clasificar': cierre.cliente.conceptos.filter(clasificado=False).count(),
            },
            
            'discrepancias': {
                'total': cierre.total_discrepancias,
                'resueltas': cierre.discrepancias_resueltas,
                'pendientes': cierre.total_discrepancias - cierre.discrepancias_resueltas,
            },
            
            'incidencias': {
                'total': cierre.total_incidencias,
                'aprobadas': cierre.incidencias_aprobadas,
                'pendientes': cierre.total_incidencias - cierre.incidencias_aprobadas,
            },
            
            'permisos': {
                'puede_consolidar': cierre.puede_consolidar,
                'puede_finalizar': cierre.puede_finalizar,
            },
            
            'metadata': {
                'es_primer_cierre': cierre.es_primer_cierre,
                'requiere_mapeo': cierre.requiere_mapeo,
                'fecha_creacion': cierre.fecha_creacion,
                'fecha_consolidacion': cierre.fecha_consolidacion,
                'fecha_finalizacion': cierre.fecha_finalizacion,
            },
        }
    
    @classmethod
    def cancelar(cls, cierre: Cierre, user=None, motivo: str = None) -> ServiceResult[Cierre]:
        """
        Cancelar un cierre.
        
        Args:
            cierre: Cierre a cancelar
            user: Usuario que cancela
            motivo: Motivo de cancelación
        """
        logger = cls.get_logger()
        
        if cierre.estado == EstadoCierre.FINALIZADO:
            return ServiceResult.fail('No se puede cancelar un cierre finalizado.')
        
        if cierre.estado == EstadoCierre.CANCELADO:
            return ServiceResult.fail('El cierre ya está cancelado.')
        
        try:
            with transaction.atomic():
                cierre.estado = EstadoCierre.CANCELADO
                if motivo:
                    cierre.notas = f"{cierre.notas or ''}\n[CANCELADO]: {motivo}".strip()
                cierre.save()
                
                cls.log_action(
                    action='cancelar',
                    entity_type='cierre',
                    entity_id=cierre.id,
                    user=user,
                    extra={'motivo': motivo}
                )
                
                logger.info(f"Cierre {cierre.id} cancelado por {user}. Motivo: {motivo}")
                
                return ServiceResult.ok(cierre)
                
        except Exception as e:
            logger.error(f"Error al cancelar cierre {cierre.id}: {str(e)}")
            return ServiceResult.fail(f'Error al cancelar: {str(e)}')
