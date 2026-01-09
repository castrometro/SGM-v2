"""
EquipoService - Lógica de negocio para gestión de equipos.

Centraliza:
- Consultas de equipos por supervisor
- Estadísticas de equipo
- Asignaciones
"""

from django.db.models import Count, Q, Prefetch
from typing import Optional, Dict, Any, List

from .base import BaseService, ServiceResult
from ..models import Cierre
from ..constants import EstadoCierre, EstadoIncidencia
from apps.core.models import Usuario, Cliente
from apps.core.constants import TipoUsuario


class EquipoService(BaseService):
    """
    Servicio para gestión de equipos y supervisión.
    
    Maneja:
    - Obtener analistas de un supervisor
    - Estadísticas de equipo
    - Cierres del equipo
    """
    
    @classmethod
    def obtener_analistas(cls, supervisor) -> List[Dict[str, Any]]:
        """
        Obtener lista de analistas supervisados.
        
        Args:
            supervisor: Usuario supervisor
            
        Returns:
            Lista de analistas con estadísticas básicas
        """
        if supervisor.tipo_usuario == TipoUsuario.GERENTE:
            # Gerente ve todos los analistas
            analistas = Usuario.objects.filter(
                tipo_usuario=TipoUsuario.ANALISTA,
                is_active=True
            )
        else:
            # Supervisor ve sus analistas directos
            analistas = supervisor.analistas_supervisados.filter(is_active=True)
        
        resultado = []
        for analista in analistas:
            clientes = Cliente.objects.filter(
                usuario_asignado=analista,
                activo=True
            )
            
            cierres_activos = Cierre.objects.filter(
                analista=analista
            ).exclude(
                estado__in=EstadoCierre.ESTADOS_FINALES
            )
            
            resultado.append({
                'id': analista.id,
                'nombre': analista.get_full_name(),
                'email': analista.email,
                'total_clientes': clientes.count(),
                'cierres_activos': cierres_activos.count(),
            })
        
        return resultado
    
    @classmethod
    def obtener_cierres_equipo(
        cls,
        supervisor,
        solo_activos: bool = True
    ) -> ServiceResult[Dict[str, Any]]:
        """
        Obtener cierres del equipo agrupados por analista.
        
        Args:
            supervisor: Usuario supervisor
            solo_activos: Si filtrar solo cierres no finalizados
        """
        logger = cls.get_logger()
        
        try:
            if supervisor.tipo_usuario == TipoUsuario.GERENTE:
                analistas = Usuario.objects.filter(
                    tipo_usuario=TipoUsuario.ANALISTA,
                    is_active=True
                )
            else:
                analistas = supervisor.analistas_supervisados.filter(is_active=True)
            
            resultado = []
            estadisticas = {
                'total_analistas': 0,
                'total_cierres': 0,
                'cierres_en_proceso': 0,
                'cierres_pendientes_revision': 0,
            }
            
            for analista in analistas:
                clientes_analista = Cliente.objects.filter(
                    usuario_asignado=analista,
                    activo=True
                )
                
                cierres = []
                for cliente in clientes_analista:
                    # Obtener cierre más reciente de cada cliente
                    cierre = Cierre.objects.filter(
                        cliente=cliente,
                        analista=analista
                    ).order_by('-periodo', '-fecha_creacion').first()
                    
                    if cierre:
                        # Aplicar filtro de activos si corresponde
                        if solo_activos and cierre.estado in EstadoCierre.ESTADOS_FINALES:
                            continue
                        
                        cierres.append({
                            'id': cierre.id,
                            'cliente': {
                                'id': cliente.id,
                                'nombre': cliente.nombre_comercial or cliente.razon_social,
                                'rut': cliente.rut,
                            },
                            'periodo': cierre.periodo,
                            'estado': cierre.estado,
                            'estado_display': cierre.get_estado_display(),
                            'fecha_creacion': cierre.fecha_creacion,
                            'requiere_atencion': cierre.estado in EstadoCierre.ESTADOS_REQUIEREN_ATENCION,
                        })
                        
                        # Actualizar estadísticas
                        estadisticas['total_cierres'] += 1
                        if cierre.estado not in EstadoCierre.ESTADOS_FINALES:
                            estadisticas['cierres_en_proceso'] += 1
                        if cierre.estado in ['revision_incidencias', 'deteccion_incidencias']:
                            estadisticas['cierres_pendientes_revision'] += 1
                
                if cierres or clientes_analista.exists():
                    resultado.append({
                        'analista': {
                            'id': analista.id,
                            'nombre': analista.get_full_name(),
                            'email': analista.email,
                        },
                        'total_clientes': clientes_analista.count(),
                        'total_cierres': len(cierres),
                        'cierres': cierres,
                    })
                    estadisticas['total_analistas'] += 1
            
            return ServiceResult.ok({
                'equipo': resultado,
                'estadisticas': estadisticas,
            })
            
        except Exception as e:
            logger.error(f"Error al obtener cierres del equipo: {str(e)}")
            return ServiceResult.fail(f'Error: {str(e)}')
    
    @classmethod
    def obtener_estadisticas_equipo(cls, supervisor) -> Dict[str, Any]:
        """
        Obtener estadísticas completas del equipo.
        """
        if supervisor.tipo_usuario == TipoUsuario.GERENTE:
            analistas = Usuario.objects.filter(
                tipo_usuario=TipoUsuario.ANALISTA,
                is_active=True
            )
        else:
            analistas = supervisor.analistas_supervisados.filter(is_active=True)
        
        analistas_ids = list(analistas.values_list('id', flat=True))
        
        # Estadísticas de cierres
        cierres = Cierre.objects.filter(analista_id__in=analistas_ids)
        
        cierres_por_estado = cierres.values('estado').annotate(
            total=Count('id')
        )
        
        # Estadísticas de incidencias
        from ..models import Incidencia
        incidencias = Incidencia.objects.filter(
            cierre__analista_id__in=analistas_ids
        )
        
        incidencias_por_estado = incidencias.values('estado').annotate(
            total=Count('id')
        )
        
        return {
            'analistas': {
                'total': analistas.count(),
                'activos': analistas.filter(is_active=True).count(),
            },
            'clientes': {
                'total': Cliente.objects.filter(
                    usuario_asignado_id__in=analistas_ids
                ).count(),
                'activos': Cliente.objects.filter(
                    usuario_asignado_id__in=analistas_ids,
                    activo=True
                ).count(),
            },
            'cierres': {
                'total': cierres.count(),
                'por_estado': {
                    item['estado']: item['total']
                    for item in cierres_por_estado
                },
                'en_proceso': cierres.exclude(
                    estado__in=EstadoCierre.ESTADOS_FINALES
                ).count(),
            },
            'incidencias': {
                'total': incidencias.count(),
                'por_estado': {
                    item['estado']: item['total']
                    for item in incidencias_por_estado
                },
                'pendientes': incidencias.filter(
                    estado__in=EstadoIncidencia.ESTADOS_ABIERTOS
                ).count(),
            },
        }
    
    @classmethod
    def asignar_analista_a_supervisor(
        cls,
        analista: Usuario,
        supervisor: Usuario,
        user=None
    ) -> ServiceResult[Usuario]:
        """
        Asignar un analista a un supervisor.
        """
        logger = cls.get_logger()
        
        if analista.tipo_usuario != TipoUsuario.ANALISTA:
            return ServiceResult.fail('El usuario debe ser analista')
        
        if supervisor.tipo_usuario not in TipoUsuario.PUEDEN_SER_SUPERVISORES:
            return ServiceResult.fail('El supervisor debe ser de tipo supervisor o senior')
        
        try:
            supervisor_anterior = analista.supervisor
            analista.supervisor = supervisor
            analista.save()
            
            cls.log_action(
                action='asignar_supervisor',
                entity_type='usuario',
                entity_id=analista.id,
                user=user,
                extra={
                    'supervisor_anterior_id': supervisor_anterior.id if supervisor_anterior else None,
                    'supervisor_nuevo_id': supervisor.id,
                }
            )
            
            logger.info(
                f"Analista {analista} asignado a supervisor {supervisor}"
            )
            
            return ServiceResult.ok(analista)
            
        except Exception as e:
            logger.error(f"Error al asignar analista: {str(e)}")
            return ServiceResult.fail(f'Error: {str(e)}')
