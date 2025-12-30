"""
ViewSets para Consolidación y Dashboards.
"""

from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Sum, Avg, Min, Max

from ..models import (
    ResumenConsolidado,
    ResumenCategoria,
    ResumenMovimientos,
    Cierre,
    EmpleadoCierre,
)
from ..serializers import (
    ResumenConsolidadoSerializer,
    ResumenCategoriaSerializer,
    ResumenMovimientosSerializer,
)


class DashboardViewSet(viewsets.ViewSet):
    """ViewSet para dashboards del cierre."""
    
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def libro(self, request):
        """Dashboard del Libro de Remuneraciones."""
        cierre_id = request.query_params.get('cierre_id')
        if not cierre_id:
            return Response({'error': 'cierre_id es requerido'}, status=400)
        
        try:
            cierre = Cierre.objects.select_related('cliente').get(id=cierre_id)
        except Cierre.DoesNotExist:
            return Response({'error': 'Cierre no encontrado'}, status=404)
        
        # Totales de empleados
        empleados = EmpleadoCierre.objects.filter(cierre=cierre)
        totales_empleados = empleados.aggregate(
            total_haberes=Sum('total_haberes'),
            total_descuentos=Sum('total_descuentos'),
            total_liquido=Sum('liquido'),
        )
        
        # Resumen por categoría
        resumenes_cat = ResumenCategoria.objects.filter(cierre=cierre).select_related('categoria')
        
        # Top conceptos por monto
        top_conceptos = ResumenConsolidado.objects.filter(
            cierre=cierre
        ).select_related('concepto', 'categoria').order_by('-total_monto')[:10]
        
        return Response({
            'periodo': cierre.periodo,
            'cliente_nombre': cierre.cliente.nombre_display,
            'total_empleados': empleados.count(),
            'total_haberes': totales_empleados['total_haberes'] or 0,
            'total_descuentos': totales_empleados['total_descuentos'] or 0,
            'total_liquido': totales_empleados['total_liquido'] or 0,
            'por_categoria': ResumenCategoriaSerializer(resumenes_cat, many=True).data,
            'top_conceptos': ResumenConsolidadoSerializer(top_conceptos, many=True).data,
        })
    
    @action(detail=False, methods=['get'])
    def movimientos(self, request):
        """Dashboard de Movimientos del Mes."""
        cierre_id = request.query_params.get('cierre_id')
        if not cierre_id:
            return Response({'error': 'cierre_id es requerido'}, status=400)
        
        try:
            cierre = Cierre.objects.select_related('cliente').get(id=cierre_id)
        except Cierre.DoesNotExist:
            return Response({'error': 'Cierre no encontrado'}, status=404)
        
        # Resúmenes de movimientos
        resumenes = ResumenMovimientos.objects.filter(cierre=cierre)
        
        # Totales por tipo
        totales = {r.tipo: r.cantidad for r in resumenes}
        
        return Response({
            'periodo': cierre.periodo,
            'cliente_nombre': cierre.cliente.nombre_display,
            'total_altas': totales.get('alta', 0),
            'total_bajas': totales.get('baja', 0),
            'total_licencias': totales.get('licencia', 0),
            'total_vacaciones': totales.get('vacaciones', 0),
            'movimientos': ResumenMovimientosSerializer(resumenes, many=True).data,
        })
    
    @action(detail=False, methods=['get'])
    def comparativo(self, request):
        """Comparativo con mes anterior."""
        cierre_id = request.query_params.get('cierre_id')
        if not cierre_id:
            return Response({'error': 'cierre_id es requerido'}, status=400)
        
        try:
            cierre = Cierre.objects.select_related('cliente').get(id=cierre_id)
        except Cierre.DoesNotExist:
            return Response({'error': 'Cierre no encontrado'}, status=404)
        
        cierre_anterior = cierre.get_cierre_anterior()
        
        if not cierre_anterior:
            return Response({
                'mensaje': 'No hay cierre anterior para comparar',
                'es_primer_cierre': True,
            })
        
        # Comparar totales por categoría
        categorias_actual = {
            r.categoria_id: r.total_monto 
            for r in ResumenCategoria.objects.filter(cierre=cierre)
        }
        categorias_anterior = {
            r.categoria_id: r.total_monto 
            for r in ResumenCategoria.objects.filter(cierre=cierre_anterior)
        }
        
        comparativo = []
        for cat_id, monto_actual in categorias_actual.items():
            monto_anterior = categorias_anterior.get(cat_id, 0)
            if monto_anterior > 0:
                variacion = ((monto_actual - monto_anterior) / monto_anterior) * 100
            else:
                variacion = 100 if monto_actual > 0 else 0
            
            comparativo.append({
                'categoria': cat_id,
                'monto_anterior': monto_anterior,
                'monto_actual': monto_actual,
                'diferencia': monto_actual - monto_anterior,
                'variacion_porcentual': round(variacion, 2),
            })
        
        return Response({
            'periodo_actual': cierre.periodo,
            'periodo_anterior': cierre_anterior.periodo,
            'comparativo': comparativo,
        })


class ResumenConsolidadoViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet para resúmenes consolidados."""
    
    permission_classes = [IsAuthenticated]
    serializer_class = ResumenConsolidadoSerializer
    
    def get_queryset(self):
        queryset = ResumenConsolidado.objects.select_related(
            'cierre', 'categoria', 'concepto'
        ).all()
        
        cierre_id = self.request.query_params.get('cierre')
        if cierre_id:
            queryset = queryset.filter(cierre_id=cierre_id)
        
        categoria = self.request.query_params.get('categoria')
        if categoria:
            queryset = queryset.filter(categoria=categoria)
        
        return queryset.order_by('categoria', '-total_monto')
