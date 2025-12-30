"""
ViewSets para Incidencias.
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.db.models import Count, Q

from ..models import Incidencia, ComentarioIncidencia
from ..serializers import (
    IncidenciaSerializer,
    IncidenciaDetailSerializer,
    IncidenciaResolverSerializer,
    IncidenciaResumenSerializer,
    ComentarioIncidenciaSerializer,
    ComentarioCrearSerializer,
)
from shared.permissions import IsSupervisor


class IncidenciaViewSet(viewsets.ModelViewSet):
    """ViewSet para incidencias."""
    
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = Incidencia.objects.select_related(
            'cierre', 'concepto', 'categoria', 'resuelto_por'
        ).all()
        
        cierre_id = self.request.query_params.get('cierre')
        if cierre_id:
            queryset = queryset.filter(cierre_id=cierre_id)
        
        estado = self.request.query_params.get('estado')
        if estado:
            queryset = queryset.filter(estado=estado)
        
        categoria = self.request.query_params.get('categoria')
        if categoria:
            queryset = queryset.filter(categoria=categoria)
        
        return queryset.order_by('-variacion_porcentual')
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return IncidenciaDetailSerializer
        if self.action in ['aprobar', 'rechazar', 'resolver']:
            return IncidenciaResolverSerializer
        return IncidenciaSerializer
    
    @action(detail=True, methods=['post'], permission_classes=[IsSupervisor])
    def resolver(self, request, pk=None):
        """Aprobar o rechazar una incidencia (supervisor)."""
        incidencia = self.get_object()
        
        serializer = IncidenciaResolverSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        accion = serializer.validated_data['accion']
        motivo = serializer.validated_data.get('motivo', '')
        
        if accion == 'aprobar':
            incidencia.estado = 'aprobada'
        else:
            incidencia.estado = 'rechazada'
        
        incidencia.resuelto_por = request.user
        incidencia.fecha_resolucion = timezone.now()
        incidencia.motivo_resolucion = motivo
        incidencia.save()
        
        # Actualizar contadores del cierre
        incidencia.cierre.actualizar_contadores()
        
        return Response({
            'message': f'Incidencia {accion}da exitosamente',
            'incidencia': IncidenciaDetailSerializer(incidencia).data
        })
    
    @action(detail=True, methods=['post'])
    def comentar(self, request, pk=None):
        """Agregar comentario a una incidencia."""
        incidencia = self.get_object()
        
        data = request.data.copy()
        data['incidencia'] = incidencia.id
        
        serializer = ComentarioCrearSerializer(
            data=data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        comentario = serializer.save()
        
        # Cambiar estado a "en revisión" si estaba pendiente
        if incidencia.estado == 'pendiente':
            incidencia.estado = 'en_revision'
            incidencia.save()
        
        return Response(
            ComentarioIncidenciaSerializer(comentario).data,
            status=status.HTTP_201_CREATED
        )
    
    @action(detail=True, methods=['get'])
    def comentarios(self, request, pk=None):
        """Obtener comentarios de una incidencia."""
        incidencia = self.get_object()
        comentarios = incidencia.comentarios.select_related('autor').all()
        
        return Response(
            ComentarioIncidenciaSerializer(comentarios, many=True).data
        )
    
    @action(detail=False, methods=['get'])
    def resumen(self, request):
        """Resumen de incidencias para un cierre."""
        cierre_id = request.query_params.get('cierre_id')
        if not cierre_id:
            return Response(
                {'error': 'cierre_id es requerido'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        incidencias = Incidencia.objects.filter(cierre_id=cierre_id)
        
        total = incidencias.count()
        aprobadas = incidencias.filter(estado='aprobada').count()
        rechazadas = incidencias.filter(estado='rechazada').count()
        pendientes = incidencias.filter(estado__in=['pendiente', 'en_revision']).count()
        
        # Por categoría
        por_categoria = incidencias.values(
            'categoria__codigo', 'categoria__nombre'
        ).annotate(
            total=Count('id'),
            aprobadas=Count('id', filter=Q(estado='aprobada')),
            pendientes=Count('id', filter=Q(estado__in=['pendiente', 'en_revision']))
        )
        
        return Response({
            'total': total,
            'aprobadas': aprobadas,
            'rechazadas': rechazadas,
            'pendientes': pendientes,
            'por_categoria': list(por_categoria),
        })


class ComentarioIncidenciaViewSet(viewsets.ModelViewSet):
    """ViewSet para comentarios de incidencias."""
    
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return ComentarioIncidencia.objects.select_related(
            'incidencia', 'autor'
        ).all()
    
    def get_serializer_class(self):
        if self.action == 'create':
            return ComentarioCrearSerializer
        return ComentarioIncidenciaSerializer
    
    def perform_update(self, serializer):
        serializer.save(editado=True)
