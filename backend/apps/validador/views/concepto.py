"""
ViewSets para Conceptos y Mapeos.
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone

from ..models import CategoriaConcepto, ConceptoCliente, MapeoItemNovedades, RegistroNovedades
from ..serializers import (
    CategoriaConceptoSerializer,
    ConceptoClienteSerializer,
    ConceptoClienteClasificarSerializer,
    ConceptoSinClasificarSerializer,
    MapeoItemNovedadesSerializer,
    MapeoItemCrearSerializer,
    ItemSinMapearSerializer,
)


class CategoriaConceptoViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet de solo lectura para categorías de conceptos."""
    
    permission_classes = [IsAuthenticated]
    queryset = CategoriaConcepto.objects.all().order_by('orden')
    serializer_class = CategoriaConceptoSerializer


class ConceptoClienteViewSet(viewsets.ModelViewSet):
    """ViewSet para conceptos de cliente."""
    
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = ConceptoCliente.objects.select_related(
            'cliente', 'categoria', 'clasificado_por'
        ).all()
        
        cliente_id = self.request.query_params.get('cliente')
        if cliente_id:
            queryset = queryset.filter(cliente_id=cliente_id)
        
        clasificado = self.request.query_params.get('clasificado')
        if clasificado is not None:
            queryset = queryset.filter(clasificado=clasificado.lower() == 'true')
        
        categoria = self.request.query_params.get('categoria')
        if categoria:
            queryset = queryset.filter(categoria=categoria)
        
        return queryset.order_by('categoria', 'nombre_erp')
    
    def get_serializer_class(self):
        if self.action == 'clasificar_batch':
            return ConceptoClienteClasificarSerializer
        if self.action == 'sin_clasificar':
            return ConceptoSinClasificarSerializer
        return ConceptoClienteSerializer
    
    @action(detail=False, methods=['get'])
    def sin_clasificar(self, request):
        """Obtener conceptos sin clasificar de un cliente."""
        cliente_id = request.query_params.get('cliente_id')
        if not cliente_id:
            return Response(
                {'error': 'cliente_id es requerido'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        conceptos = ConceptoCliente.objects.filter(
            cliente_id=cliente_id,
            clasificado=False
        )
        
        serializer = ConceptoSinClasificarSerializer(conceptos, many=True)
        return Response({
            'count': conceptos.count(),
            'conceptos': serializer.data
        })
    
    @action(detail=False, methods=['post'])
    def clasificar_batch(self, request):
        """Clasificar múltiples conceptos a la vez."""
        serializer = ConceptoClienteClasificarSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        clasificados = 0
        errores = []
        
        for item in serializer.validated_data['conceptos']:
            try:
                concepto = ConceptoCliente.objects.get(id=item['id'])
                concepto.categoria_id = item['categoria']
                concepto.clasificado = True
                concepto.clasificado_por = request.user
                concepto.fecha_clasificacion = timezone.now()
                concepto.save()
                clasificados += 1
            except ConceptoCliente.DoesNotExist:
                errores.append(f"Concepto {item['id']} no encontrado")
            except Exception as e:
                errores.append(f"Error en concepto {item['id']}: {str(e)}")
        
        return Response({
            'clasificados': clasificados,
            'errores': errores
        })


class MapeoItemNovedadesViewSet(viewsets.ModelViewSet):
    """ViewSet para mapeos de items de novedades."""
    
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = MapeoItemNovedades.objects.select_related(
            'cliente', 'concepto_erp', 'mapeado_por'
        ).all()
        
        cliente_id = self.request.query_params.get('cliente')
        if cliente_id:
            queryset = queryset.filter(cliente_id=cliente_id)
        
        return queryset.order_by('nombre_novedades')
    
    def get_serializer_class(self):
        if self.action == 'crear_batch':
            return MapeoItemCrearSerializer
        return MapeoItemNovedadesSerializer
    
    @action(detail=False, methods=['get'])
    def sin_mapear(self, request):
        """Obtener items de novedades sin mapear para un cierre."""
        cierre_id = request.query_params.get('cierre_id')
        if not cierre_id:
            return Response(
                {'error': 'cierre_id es requerido'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Items en novedades que no tienen mapeo
        from django.db.models import Count
        
        items_sin_mapear = RegistroNovedades.objects.filter(
            cierre_id=cierre_id,
            mapeo__isnull=True
        ).values('nombre_item').annotate(
            cantidad_registros=Count('id')
        ).order_by('nombre_item')
        
        return Response({
            'count': items_sin_mapear.count(),
            'items': [
                {
                    'nombre_novedades': item['nombre_item'],
                    'cantidad_registros': item['cantidad_registros']
                }
                for item in items_sin_mapear
            ]
        })
    
    @action(detail=False, methods=['post'])
    def crear_batch(self, request):
        """Crear múltiples mapeos a la vez."""
        serializer = MapeoItemCrearSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        cliente_id = request.data.get('cliente_id')
        if not cliente_id:
            return Response(
                {'error': 'cliente_id es requerido'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        creados = 0
        errores = []
        
        for item in serializer.validated_data['mapeos']:
            try:
                MapeoItemNovedades.objects.create(
                    cliente_id=cliente_id,
                    nombre_novedades=item['nombre_novedades'],
                    concepto_erp_id=item['concepto_erp_id'],
                    mapeado_por=request.user
                )
                creados += 1
            except Exception as e:
                errores.append(f"Error en '{item['nombre_novedades']}': {str(e)}")
        
        # Actualizar mapeos en registros existentes
        from ..models import Cierre
        cierre_id = request.data.get('cierre_id')
        if cierre_id:
            try:
                cierre = Cierre.objects.get(id=cierre_id)
                for registro in RegistroNovedades.objects.filter(cierre=cierre, mapeo__isnull=True):
                    mapeo = MapeoItemNovedades.objects.filter(
                        cliente=cierre.cliente,
                        nombre_novedades=registro.nombre_item
                    ).first()
                    if mapeo:
                        registro.mapeo = mapeo
                        registro.save()
            except Exception as e:
                errores.append(f"Error actualizando registros: {str(e)}")
        
        return Response({
            'creados': creados,
            'errores': errores
        })
