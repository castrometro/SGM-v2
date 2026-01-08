"""
IncidenciaService - Lógica de negocio para Incidencias.

Centraliza:
- Detección de incidencias
- Resolución (aprobar/rechazar)
- Comentarios
- Estadísticas
"""

from django.utils import timezone
from django.db import transaction
from django.db.models import Count, Q
from typing import Optional, Dict, Any, List

from .base import BaseService, ServiceResult
from ..models import Incidencia, ComentarioIncidencia, Cierre
from ..constants import EstadoIncidencia
from apps.core.constants import TipoUsuario


class IncidenciaService(BaseService):
    """
    Servicio para gestión de Incidencias.
    
    Las incidencias son variaciones detectadas entre cierres consecutivos
    que requieren aprobación de un supervisor.
    """
    
    ESTADOS_INCIDENCIA = EstadoIncidencia.ALL
    
    @classmethod
    def resolver(
        cls,
        incidencia: Incidencia,
        accion: str,
        user,
        motivo: str = None
    ) -> ServiceResult[Incidencia]:
        """
        Resolver una incidencia (aprobar o rechazar).
        
        Args:
            incidencia: Incidencia a resolver
            accion: 'aprobar' o 'rechazar'
            user: Usuario que resuelve (debe ser supervisor+)
            motivo: Motivo de la resolución
        """
        logger = cls.get_logger()
        
        if accion not in ['aprobar', 'rechazar']:
            return ServiceResult.fail("Acción debe ser 'aprobar' o 'rechazar'")
        
        if incidencia.estado in EstadoIncidencia.ESTADOS_RESUELTOS:
            return ServiceResult.fail(
                f'La incidencia ya fue {incidencia.estado}'
            )
        
        # Verificar permisos
        if not cls._puede_resolver(user):
            return ServiceResult.fail(
                'No tiene permisos para resolver incidencias'
            )
        
        try:
            with transaction.atomic():
                # Actualizar incidencia
                incidencia.estado = EstadoIncidencia.APROBADA if accion == 'aprobar' else EstadoIncidencia.RECHAZADA
                incidencia.resuelto_por = user
                incidencia.fecha_resolucion = timezone.now()
                incidencia.motivo_resolucion = motivo or ''
                incidencia.save()
                
                # Actualizar contadores del cierre
                incidencia.cierre.actualizar_contadores()
                
                cls.log_action(
                    action=f'incidencia_{accion}',
                    entity_type='incidencia',
                    entity_id=incidencia.id,
                    user=user,
                    extra={
                        'cierre_id': incidencia.cierre_id,
                        'motivo': motivo,
                    }
                )
                
                logger.info(
                    f"Incidencia {incidencia.id} {accion}da por {user}"
                )
                
                return ServiceResult.ok(incidencia)
                
        except Exception as e:
            logger.error(f"Error al resolver incidencia {incidencia.id}: {str(e)}")
            return ServiceResult.fail(f'Error al resolver: {str(e)}')
    
    @classmethod
    def agregar_comentario(
        cls,
        incidencia: Incidencia,
        texto: str,
        user,
        tipo: str = 'comentario'
    ) -> ServiceResult[ComentarioIncidencia]:
        """
        Agregar comentario a una incidencia.
        
        Args:
            incidencia: Incidencia a comentar
            texto: Texto del comentario
            user: Usuario que comenta
            tipo: Tipo de comentario (comentario, justificacion, etc.)
        """
        logger = cls.get_logger()
        
        if not texto or not texto.strip():
            return ServiceResult.fail('El comentario no puede estar vacío')
        
        try:
            with transaction.atomic():
                comentario = ComentarioIncidencia.objects.create(
                    incidencia=incidencia,
                    usuario=user,
                    texto=texto.strip(),
                    tipo=tipo
                )
                
                # Si estaba pendiente, cambiar a en_revision
                if incidencia.estado == EstadoIncidencia.PENDIENTE:
                    incidencia.estado = EstadoIncidencia.EN_REVISION
                    incidencia.save()
                
                cls.log_action(
                    action='agregar_comentario',
                    entity_type='incidencia',
                    entity_id=incidencia.id,
                    user=user,
                    extra={
                        'comentario_id': comentario.id,
                        'tipo': tipo,
                    }
                )
                
                return ServiceResult.ok(comentario)
                
        except Exception as e:
            logger.error(f"Error al agregar comentario: {str(e)}")
            return ServiceResult.fail(f'Error al agregar comentario: {str(e)}')
    
    @classmethod
    def obtener_estadisticas_cierre(cls, cierre: Cierre) -> Dict[str, Any]:
        """
        Obtener estadísticas de incidencias de un cierre.
        """
        incidencias = Incidencia.objects.filter(cierre=cierre)
        
        por_estado = incidencias.values('estado').annotate(
            total=Count('id')
        )
        
        por_categoria = incidencias.values('categoria__nombre').annotate(
            total=Count('id')
        )
        
        return {
            'total': incidencias.count(),
            'por_estado': {
                item['estado']: item['total'] 
                for item in por_estado
            },
            'por_categoria': {
                item['categoria__nombre'] or 'Sin categoría': item['total']
                for item in por_categoria
            },
            'resumen': {
                'pendientes': incidencias.filter(
                    estado__in=EstadoIncidencia.ESTADOS_ABIERTOS
                ).count(),
                'aprobadas': incidencias.filter(estado=EstadoIncidencia.APROBADA).count(),
                'rechazadas': incidencias.filter(estado=EstadoIncidencia.RECHAZADA).count(),
            },
            'puede_finalizar': not incidencias.filter(
                estado__in=EstadoIncidencia.ESTADOS_ABIERTOS
            ).exists(),
        }
    
    @classmethod
    def obtener_incidencias_equipo(
        cls,
        supervisor,
        solo_pendientes: bool = False
    ) -> Dict[str, Any]:
        """
        Obtener incidencias del equipo de un supervisor.
        
        Args:
            supervisor: Usuario supervisor
            solo_pendientes: Si filtrar solo pendientes
        """
        # Obtener analistas del equipo
        analistas = supervisor.analistas_supervisados.filter(is_active=True)
        
        # Obtener cierres del equipo
        cierres_ids = Cierre.objects.filter(
            analista__in=analistas
        ).values_list('id', flat=True)
        
        # Obtener incidencias
        incidencias = Incidencia.objects.filter(
            cierre_id__in=cierres_ids
        ).select_related('cierre', 'cierre__analista', 'cierre__cliente')
        
        if solo_pendientes:
            incidencias = incidencias.filter(
                estado__in=EstadoIncidencia.ESTADOS_ABIERTOS
            )
        
        # Agrupar por analista
        resultado = {}
        for incidencia in incidencias.order_by('-fecha_creacion')[:100]:
            analista = incidencia.cierre.analista
            analista_key = str(analista.id)
            
            if analista_key not in resultado:
                resultado[analista_key] = {
                    'analista': {
                        'id': analista.id,
                        'nombre': analista.get_full_name(),
                    },
                    'incidencias': []
                }
            
            resultado[analista_key]['incidencias'].append({
                'id': incidencia.id,
                'tipo': incidencia.tipo,
                'estado': incidencia.estado,
                'variacion_porcentual': incidencia.variacion_porcentual,
                'cliente': incidencia.cierre.cliente.nombre_comercial,
                'periodo': incidencia.cierre.periodo,
                'fecha_creacion': incidencia.fecha_creacion,
            })
        
        return {
            'por_analista': list(resultado.values()),
            'total': incidencias.count(),
            'pendientes': incidencias.filter(
                estado__in=EstadoIncidencia.ESTADOS_ABIERTOS
            ).count(),
        }
    
    @classmethod
    def _puede_resolver(cls, user) -> bool:
        """Verificar si el usuario puede resolver incidencias."""
        return user.tipo_usuario in TipoUsuario.PUEDEN_APROBAR
