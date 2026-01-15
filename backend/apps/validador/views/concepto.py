"""
ViewSets para Conceptos y Mapeos.
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone

from ..models import (
    CategoriaConcepto, ConceptoCliente, 
    RegistroNovedades, ConceptoLibro, ConceptoNovedades, ArchivoAnalista
)
from ..serializers import (
    CategoriaConceptoSerializer,
    ConceptoClienteSerializer,
    ConceptoClienteClasificarSerializer,
    ConceptoSinClasificarSerializer,
)
from ..constants import EstadoArchivoNovedades


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
    """
    ViewSet para ConceptoNovedades (antes MapeoItemNovedades).
    
    Los conceptos de novedades conectan headers del archivo de novedades (del cliente)
    con ConceptoLibro (headers clasificados del libro ERP).
    
    Los mapeos son por cliente+ERP y se reutilizan entre cierres.
    Similar en patrón a ConceptoLibro, pero con FK a ConceptoLibro en vez de categoria.
    """
    
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = ConceptoNovedades.objects.select_related(
            'cliente', 'erp', 'concepto_libro', 'mapeado_por'
        ).filter(activo=True)
        
        cliente_id = self.request.query_params.get('cliente')
        if cliente_id:
            queryset = queryset.filter(cliente_id=cliente_id)
        
        erp_id = self.request.query_params.get('erp')
        if erp_id:
            queryset = queryset.filter(erp_id=erp_id)
        
        return queryset.order_by('orden', 'header_original')
    
    @action(detail=False, methods=['get'])
    def sin_mapear(self, request):
        """
        Obtener conceptos de novedades sin mapear para un cliente+ERP.
        
        Query params:
            cliente_id: ID del cliente (requerido)
            erp_id: ID del ERP (opcional, se infiere del cliente si no se da)
        """
        cliente_id = request.query_params.get('cliente_id')
        if not cliente_id:
            return Response(
                {'error': 'cliente_id es requerido'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        queryset = ConceptoNovedades.objects.filter(
            cliente_id=cliente_id,
            concepto_libro__isnull=True,
            activo=True
        ).order_by('orden')
        
        erp_id = request.query_params.get('erp_id')
        if erp_id:
            queryset = queryset.filter(erp_id=erp_id)
        
        return Response({
            'count': queryset.count(),
            'items': [
                {
                    'id': item.id,
                    'header_original': item.header_original,
                    'orden': item.orden,
                }
                for item in queryset
            ]
        })
    
    @action(detail=False, methods=['get'])
    def conceptos_libro(self, request):
        """
        Obtener ConceptosLibro disponibles para mapear.
        
        Retorna solo conceptos clasificados (no ignorar) del cliente+ERP.
        """
        cliente_id = request.query_params.get('cliente_id')
        erp_id = request.query_params.get('erp_id')
        
        if not cliente_id:
            return Response(
                {'error': 'cliente_id es requerido'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        queryset = ConceptoLibro.objects.filter(
            cliente_id=cliente_id,
            activo=True,
            categoria__isnull=False
        ).exclude(categoria='ignorar')
        
        if erp_id:
            queryset = queryset.filter(erp_id=erp_id)
        
        conceptos = queryset.order_by('categoria', 'orden', 'header_original')
        
        return Response({
            'count': conceptos.count(),
            'conceptos': [
                {
                    'id': c.id,
                    'header_original': c.header_original,
                    'header_pandas': c.header_pandas,
                    'categoria': c.categoria,
                    'categoria_display': c.get_categoria_display(),
                }
                for c in conceptos
            ]
        })
    
    @action(detail=False, methods=['post'])
    def mapear_batch(self, request):
        """
        Mapear múltiples ConceptoNovedades a ConceptoLibro.
        
        Espera:
            mapeos: [
                { concepto_novedades_id: 1, concepto_libro_id: 45 },
                { concepto_novedades_id: 2, concepto_libro_id: 67 },
            ]
        
        Actualiza ConceptoNovedades con el concepto_libro correspondiente.
        """
        mapeos_data = request.data.get('mapeos', [])
        
        if not mapeos_data:
            return Response(
                {'error': 'mapeos es requerido'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        mapeados = 0
        errores = []
        
        for mapeo_data in mapeos_data:
            concepto_novedades_id = mapeo_data.get('concepto_novedades_id')
            concepto_libro_id = mapeo_data.get('concepto_libro_id')
            
            if not concepto_novedades_id or not concepto_libro_id:
                errores.append(f"Datos incompletos: {mapeo_data}")
                continue
            
            try:
                concepto_novedades = ConceptoNovedades.objects.get(id=concepto_novedades_id)
                concepto_libro = ConceptoLibro.objects.get(
                    id=concepto_libro_id, 
                    cliente=concepto_novedades.cliente
                )
                
                concepto_novedades.concepto_libro = concepto_libro
                concepto_novedades.mapeado_por = request.user
                concepto_novedades.fecha_mapeo = timezone.now()
                concepto_novedades.save()
                mapeados += 1
                
            except ConceptoNovedades.DoesNotExist:
                errores.append(f"ConceptoNovedades {concepto_novedades_id} no encontrado")
            except ConceptoLibro.DoesNotExist:
                errores.append(f"ConceptoLibro {concepto_libro_id} no encontrado")
            except Exception as e:
                errores.append(f"Error en concepto {concepto_novedades_id}: {str(e)}")
        
        # Obtener cliente_id del primer mapeo para verificar estado
        if mapeos_data and mapeados > 0:
            try:
                primer_concepto = ConceptoNovedades.objects.get(
                    id=mapeos_data[0].get('concepto_novedades_id')
                )
                cliente_id = primer_concepto.cliente_id
                erp_id = primer_concepto.erp_id
                
                # Verificar si todos los conceptos están mapeados
                sin_mapear = ConceptoNovedades.objects.filter(
                    cliente_id=cliente_id,
                    erp_id=erp_id,
                    concepto_libro__isnull=True,
                    activo=True
                ).count()
            except:
                sin_mapear = -1
        else:
            sin_mapear = -1
        
        return Response({
            'mapeados': mapeados,
            'errores': errores,
            'sin_mapear': sin_mapear,
        })
