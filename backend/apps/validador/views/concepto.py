"""
ViewSets para Conceptos y Mapeos.
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.throttling import ScopedRateThrottle
from django.utils import timezone

from apps.core.models import Cliente
from apps.core.constants import TipoUsuario
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

# Constantes de seguridad
MAX_BATCH_SIZE = 100  # Máximo de items por operación batch


def verificar_acceso_cliente(user, cliente_id):
    """
    Verifica si el usuario tiene acceso al cliente especificado.
    
    Returns:
        tuple: (tiene_acceso: bool, cliente: Cliente | None, error_response: Response | None)
    """
    try:
        cliente = Cliente.objects.get(id=cliente_id, activo=True)
    except Cliente.DoesNotExist:
        return False, None, Response(
            {'error': 'Cliente no encontrado'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Gerentes tienen acceso total
    if user.tipo_usuario == TipoUsuario.GERENTE:
        return True, cliente, None
    
    # Verificar acceso según rol
    clientes_permitidos = user.get_todos_los_clientes()
    if cliente not in clientes_permitidos:
        return False, cliente, Response(
            {'error': 'No tiene acceso a este cliente'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    return True, cliente, None


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
    
    Seguridad:
    - Autenticación requerida
    - Verificación de acceso a cliente en cada endpoint
    - Rate limiting en operaciones batch
    """
    
    permission_classes = [IsAuthenticated]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'mapeo'
    
    def get_queryset(self):
        queryset = ConceptoNovedades.objects.select_related(
            'cliente', 'erp', 'concepto_libro', 'mapeado_por'
        ).filter(activo=True)
        
        # Filtrar por clientes permitidos para el usuario
        user = self.request.user
        if user.tipo_usuario != TipoUsuario.GERENTE:
            clientes_permitidos = user.get_todos_los_clientes()
            queryset = queryset.filter(cliente__in=clientes_permitidos)
        
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
        
        Sin mapear = no tiene concepto_libro Y no está marcado sin_asignacion
        
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
        
        # Verificar acceso al cliente
        tiene_acceso, cliente, error_response = verificar_acceso_cliente(request.user, cliente_id)
        if not tiene_acceso:
            return error_response
        
        queryset = ConceptoNovedades.objects.filter(
            cliente_id=cliente_id,
            concepto_libro__isnull=True,
            sin_asignacion=False,
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
    def mapeados(self, request):
        """
        Obtener conceptos de novedades ya mapeados para un cliente+ERP.
        
        Mapeado = tiene concepto_libro O está marcado sin_asignacion
        
        Query params:
            cliente_id: ID del cliente (requerido)
            erp_id: ID del ERP (opcional)
        """
        cliente_id = request.query_params.get('cliente_id')
        if not cliente_id:
            return Response(
                {'error': 'cliente_id es requerido'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Verificar acceso al cliente
        tiene_acceso, cliente, error_response = verificar_acceso_cliente(request.user, cliente_id)
        if not tiene_acceso:
            return error_response
        
        from django.db.models import Q
        queryset = ConceptoNovedades.objects.filter(
            cliente_id=cliente_id,
            activo=True
        ).filter(
            Q(concepto_libro__isnull=False) | Q(sin_asignacion=True)
        ).select_related('concepto_libro').order_by('orden')
        
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
                    'sin_asignacion': item.sin_asignacion,
                    'concepto_libro': {
                        'id': item.concepto_libro.id,
                        'header_original': item.concepto_libro.header_original,
                        'categoria': item.concepto_libro.categoria,
                        'categoria_display': item.concepto_libro.get_categoria_display(),
                    } if item.concepto_libro else None,
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
        
        # Verificar acceso al cliente
        tiene_acceso, cliente, error_response = verificar_acceso_cliente(request.user, cliente_id)
        if not tiene_acceso:
            return error_response
        
        queryset = ConceptoLibro.objects.filter(
            cliente_id=cliente_id,
            activo=True,
            categoria__isnull=False
        ).exclude(categoria='ignorar')
        
        if erp_id:
            queryset = queryset.filter(erp_id=erp_id)
        
        conceptos = queryset.order_by('categoria', 'orden', 'header_original')
        
        # Obtener IDs de conceptos ya mapeados en novedades
        conceptos_usados = set(
            ConceptoNovedades.objects.filter(
                cliente_id=cliente_id,
                erp_id=erp_id,
                concepto_libro__isnull=False,
                activo=True
            ).values_list('concepto_libro_id', flat=True)
        )
        
        return Response({
            'count': conceptos.count(),
            'conceptos': [
                {
                    'id': c.id,
                    'header_original': c.header_original,
                    'header_pandas': c.header_pandas,
                    'categoria': c.categoria,
                    'categoria_display': c.get_categoria_display(),
                    'usado': c.id in conceptos_usados,
                }
                for c in conceptos
            ]
        })
    
    @action(detail=False, methods=['post'])
    def mapear_batch(self, request):
        """
        Mapear múltiples ConceptoNovedades a ConceptoLibro o marcar sin_asignacion.
        
        Espera:
            mapeos: [
                { concepto_novedades_id: 1, concepto_libro_id: 45 },
                { concepto_novedades_id: 2, sin_asignacion: true },
            ]
            archivo_id: ID del ArchivoAnalista (opcional, para actualizar estado)
        
        Actualiza ConceptoNovedades con el mapeo correspondiente.
        Si todos los conceptos quedan mapeados/sin_asignacion, actualiza estado archivo a LISTO.
        
        Seguridad:
        - Rate limiting: máx 10/hora para operaciones bulk
        - Validación de tamaño: máx 100 items por batch
        - Verificación de acceso a cliente
        """
        mapeos_data = request.data.get('mapeos', [])
        archivo_id = request.data.get('archivo_id')
        
        if not mapeos_data:
            return Response(
                {'error': 'mapeos es requerido'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validación de tamaño del batch
        if len(mapeos_data) > MAX_BATCH_SIZE:
            return Response(
                {'error': f'Máximo {MAX_BATCH_SIZE} mapeos por operación'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Obtener el primer concepto para verificar acceso al cliente
        primer_concepto_id = None
        for m in mapeos_data:
            if m.get('concepto_novedades_id'):
                primer_concepto_id = m['concepto_novedades_id']
                break
        
        if primer_concepto_id:
            try:
                primer_concepto = ConceptoNovedades.objects.get(id=primer_concepto_id)
                tiene_acceso, cliente, error_response = verificar_acceso_cliente(
                    request.user, primer_concepto.cliente_id
                )
                if not tiene_acceso:
                    return error_response
            except ConceptoNovedades.DoesNotExist:
                pass
        
        mapeados = 0
        errores = []
        cliente_id = None
        erp_id = None
        
        for mapeo_data in mapeos_data:
            concepto_novedades_id = mapeo_data.get('concepto_novedades_id')
            concepto_libro_id = mapeo_data.get('concepto_libro_id')
            marcar_sin_asignacion = mapeo_data.get('sin_asignacion', False)
            
            if not concepto_novedades_id:
                errores.append(f"Falta concepto_novedades_id: {mapeo_data}")
                continue
            
            # Debe tener concepto_libro_id O sin_asignacion=True
            if not concepto_libro_id and not marcar_sin_asignacion:
                errores.append(f"Debe indicar concepto_libro_id o sin_asignacion=true: {mapeo_data}")
                continue
            
            try:
                concepto_novedades = ConceptoNovedades.objects.get(id=concepto_novedades_id)
                cliente_id = concepto_novedades.cliente_id
                erp_id = concepto_novedades.erp_id
                
                if marcar_sin_asignacion:
                    # Marcar como sin asignación
                    concepto_novedades.sin_asignacion = True
                    concepto_novedades.concepto_libro = None
                    concepto_novedades.mapeado_por = request.user
                    concepto_novedades.fecha_mapeo = timezone.now()
                    concepto_novedades.save()
                    mapeados += 1
                else:
                    # Mapear a concepto del libro
                    concepto_libro = ConceptoLibro.objects.get(
                        id=concepto_libro_id, 
                        cliente=concepto_novedades.cliente
                    )
                    
                    # Validar mapeo 1:1 - verificar que el concepto_libro no esté ya usado
                    ya_mapeado = ConceptoNovedades.objects.filter(
                        cliente=concepto_novedades.cliente,
                        erp=concepto_novedades.erp,
                        concepto_libro=concepto_libro,
                        activo=True
                    ).exclude(id=concepto_novedades.id).first()
                    
                    if ya_mapeado:
                        errores.append(
                            f"ConceptoLibro '{concepto_libro.header_original}' ya está mapeado a "
                            f"'{ya_mapeado.header_original}'"
                        )
                        continue
                    
                    concepto_novedades.concepto_libro = concepto_libro
                    concepto_novedades.sin_asignacion = False
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
        
        # Verificar si todos los conceptos están completos (mapeados o sin_asignacion)
        sin_mapear = -1
        estado_archivo = None
        
        if cliente_id and erp_id and mapeados > 0:
            sin_mapear = ConceptoNovedades.objects.filter(
                cliente_id=cliente_id,
                erp_id=erp_id,
                concepto_libro__isnull=True,
                sin_asignacion=False,
                activo=True
            ).count()
            
            # Actualizar estado del archivo si se proporcionó archivo_id
            if archivo_id and sin_mapear == 0:
                try:
                    archivo = ArchivoAnalista.objects.get(id=archivo_id)
                    if archivo.estado == EstadoArchivoNovedades.PENDIENTE_MAPEO:
                        archivo.estado = EstadoArchivoNovedades.LISTO
                        archivo.save()
                        estado_archivo = archivo.estado
                except ArchivoAnalista.DoesNotExist:
                    pass
        
        return Response({
            'mapeados': mapeados,
            'errores': errores,
            'sin_mapear': sin_mapear,
            'estado_archivo': estado_archivo,
        })
    
    @action(detail=False, methods=['post'])
    def desmapear(self, request):
        """
        Quitar mapeo de conceptos de novedades.
        
        Espera:
            concepto_ids: [1, 2, 3]  - IDs de ConceptoNovedades a desmapear
            archivo_id: ID del ArchivoAnalista (opcional, para actualizar estado)
        
        Pone concepto_libro=None y sin_asignacion=False.
        
        Seguridad:
        - Rate limiting: máx 10/hora para operaciones bulk
        - Validación de tamaño: máx 100 items por batch
        - Verificación de acceso a cliente
        """
        concepto_ids = request.data.get('concepto_ids', [])
        archivo_id = request.data.get('archivo_id')
        
        if not concepto_ids:
            return Response(
                {'error': 'concepto_ids es requerido'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validación de tamaño del batch
        if len(concepto_ids) > MAX_BATCH_SIZE:
            return Response(
                {'error': f'Máximo {MAX_BATCH_SIZE} conceptos por operación'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Verificar acceso al cliente del primer concepto
        if concepto_ids:
            try:
                primer_concepto = ConceptoNovedades.objects.get(id=concepto_ids[0])
                tiene_acceso, cliente, error_response = verificar_acceso_cliente(
                    request.user, primer_concepto.cliente_id
                )
                if not tiene_acceso:
                    return error_response
            except ConceptoNovedades.DoesNotExist:
                pass
        
        desmapeados = 0
        cliente_id = None
        erp_id = None
        
        for concepto_id in concepto_ids:
            try:
                concepto = ConceptoNovedades.objects.get(id=concepto_id, activo=True)
                cliente_id = concepto.cliente_id
                erp_id = concepto.erp_id
                
                concepto.concepto_libro = None
                concepto.sin_asignacion = False
                concepto.mapeado_por = None
                concepto.fecha_mapeo = None
                concepto.save()
                desmapeados += 1
            except ConceptoNovedades.DoesNotExist:
                pass
        
        # Actualizar estado del archivo si hay conceptos sin mapear
        estado_archivo = None
        if archivo_id and cliente_id and erp_id:
            sin_mapear = ConceptoNovedades.objects.filter(
                cliente_id=cliente_id,
                erp_id=erp_id,
                concepto_libro__isnull=True,
                sin_asignacion=False,
                activo=True
            ).count()
            
            if sin_mapear > 0:
                try:
                    archivo = ArchivoAnalista.objects.get(id=archivo_id)
                    if archivo.estado == EstadoArchivoNovedades.LISTO:
                        archivo.estado = EstadoArchivoNovedades.PENDIENTE_MAPEO
                        archivo.save()
                        estado_archivo = archivo.estado
                except ArchivoAnalista.DoesNotExist:
                    pass
        
        return Response({
            'desmapeados': desmapeados,
            'estado_archivo': estado_archivo,
        })
