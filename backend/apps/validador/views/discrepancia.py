"""
ViewSets para Discrepancias.
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Count, Q

from ..models import Discrepancia
from ..serializers import (
    DiscrepanciaSerializer,
    DiscrepanciaResumenSerializer,
)


class DiscrepanciaViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet de solo lectura para discrepancias."""
    
    permission_classes = [IsAuthenticated]
    serializer_class = DiscrepanciaSerializer
    
    def get_queryset(self):
        queryset = Discrepancia.objects.select_related(
            'cierre', 'concepto'
        ).all()
        
        cierre_id = self.request.query_params.get('cierre')
        if cierre_id:
            queryset = queryset.filter(cierre_id=cierre_id)
        
        tipo = self.request.query_params.get('tipo')
        if tipo:
            queryset = queryset.filter(tipo=tipo)
        
        origen = self.request.query_params.get('origen')
        if origen:
            queryset = queryset.filter(origen=origen)
        
        resuelta = self.request.query_params.get('resuelta')
        if resuelta is not None:
            queryset = queryset.filter(resuelta=resuelta.lower() == 'true')
        
        return queryset.order_by('-fecha_deteccion')
    
    @action(detail=False, methods=['get'])
    def resumen(self, request):
        """Resumen de discrepancias para un cierre."""
        cierre_id = request.query_params.get('cierre_id')
        if not cierre_id:
            return Response(
                {'error': 'cierre_id es requerido'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        discrepancias = Discrepancia.objects.filter(cierre_id=cierre_id)
        
        # Agrupar por tipo
        por_tipo = discrepancias.values('tipo').annotate(
            count=Count('id')
        )
        por_tipo_dict = {item['tipo']: item['count'] for item in por_tipo}
        
        # Agrupar por origen
        por_origen = discrepancias.values('origen').annotate(
            count=Count('id')
        )
        por_origen_dict = {item['origen']: item['count'] for item in por_origen}
        
        total = discrepancias.count()
        resueltas = discrepancias.filter(resuelta=True).count()
        
        return Response({
            'total': total,
            'resueltas': resueltas,
            'pendientes': total - resueltas,
            'por_tipo': por_tipo_dict,
            'por_origen': por_origen_dict,
        })
    
    @action(detail=False, methods=['get'])
    def por_empleado(self, request):
        """Discrepancias agrupadas por empleado."""
        cierre_id = request.query_params.get('cierre_id')
        if not cierre_id:
            return Response(
                {'error': 'cierre_id es requerido'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Agrupar por RUT
        discrepancias = Discrepancia.objects.filter(
            cierre_id=cierre_id
        ).values('rut_empleado', 'nombre_empleado').annotate(
            total=Count('id'),
            resueltas=Count('id', filter=Q(resuelta=True))
        ).order_by('-total')
        
        return Response({
            'empleados': list(discrepancias)
        })
