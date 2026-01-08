"""
CierreService - Lógica de negocio para Cierres.

Centraliza toda la lógica de:
- Cambios de estado
- Validaciones de transiciones
- Consolidación
- Finalización
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
        
        result = CierreService.cambiar_estado(cierre, 'consolidado', user)
        if result.success:
            cierre_actualizado = result.data
    """
    
    # Transiciones de estado permitidas
    TRANSICIONES_VALIDAS = {
        'pendiente': ['en_proceso', 'cancelado'],
        'en_proceso': ['carga_archivos', 'cancelado'],
        'carga_archivos': ['procesando', 'en_proceso'],
        'procesando': ['comparacion', 'carga_archivos', 'error'],
        'comparacion': ['consolidado', 'procesando'],
        'consolidado': ['deteccion_incidencias', 'finalizado'],  # finalizado si es primer cierre
        'deteccion_incidencias': ['revision_incidencias', 'finalizado'],
        'revision_incidencias': ['finalizado', 'deteccion_incidencias'],
        'finalizado': [],  # Estado final
        'cancelado': [],   # Estado final
        'error': ['en_proceso', 'carga_archivos'],
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
    def consolidar(cls, cierre: Cierre, user=None) -> ServiceResult[Cierre]:
        """
        Consolidar un cierre.
        
        Validaciones:
        - No debe haber discrepancias pendientes
        - Debe estar en estado 'comparacion'
        
        Si es primer cierre, finaliza automáticamente.
        """
        logger = cls.get_logger()
        
        # Validar que pueda consolidar
        if not cierre.puede_consolidar:
            return ServiceResult.fail(
                'No se puede consolidar. Hay discrepancias pendientes o archivos faltantes.'
            )
        
        if cierre.estado != EstadoCierre.COMPARACION:
            return ServiceResult.fail(
                f'Solo se puede consolidar desde estado "comparacion". Estado actual: {cierre.estado}'
            )
        
        try:
            with transaction.atomic():
                # Cambiar a consolidado
                result = cls.cambiar_estado(cierre, EstadoCierre.CONSOLIDADO, user, validar_transicion=False)
                if not result.success:
                    return result
                
                cierre = result.data
                
                # Si es primer cierre, finalizar automáticamente
                if cierre.es_primer_cierre:
                    logger.info(f"Cierre {cierre.id} es primer cierre, finalizando automáticamente")
                    return cls.finalizar(cierre, user)
                
                # Si no, pasar a detección de incidencias
                result = cls.cambiar_estado(cierre, EstadoCierre.DETECCION_INCIDENCIAS, user, validar_transicion=False)
                if not result.success:
                    return result
                
                # TODO: Disparar task de detección de incidencias
                # from ..tasks import detectar_incidencias
                # detectar_incidencias.delay(cierre.id)
                
                return ServiceResult.ok(result.data)
                
        except Exception as e:
            logger.error(f"Error al consolidar cierre {cierre.id}: {str(e)}")
            return ServiceResult.fail(f'Error al consolidar: {str(e)}')
    
    @classmethod
    def finalizar(cls, cierre: Cierre, user=None) -> ServiceResult[Cierre]:
        """
        Finalizar un cierre.
        
        Validaciones:
        - Todas las incidencias deben estar resueltas
        - Debe estar en estado permitido para finalizar
        """
        logger = cls.get_logger()
        
        if not cierre.puede_finalizar:
            return ServiceResult.fail(
                'No se puede finalizar. Hay incidencias pendientes de aprobación.'
            )
        
        estados_permitidos = EstadoCierre.ESTADOS_PUEDEN_FINALIZAR
        if cierre.estado not in estados_permitidos:
            return ServiceResult.fail(
                f'Solo se puede finalizar desde estados {estados_permitidos}. Estado actual: {cierre.estado}'
            )
        
        try:
            result = cls.cambiar_estado(cierre, EstadoCierre.FINALIZADO, user, validar_transicion=False)
            
            if result.success:
                logger.info(f"Cierre {cierre.id} finalizado por {user}")
                
            return result
            
        except Exception as e:
            logger.error(f"Error al finalizar cierre {cierre.id}: {str(e)}")
            return ServiceResult.fail(f'Error al finalizar: {str(e)}')
    
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
