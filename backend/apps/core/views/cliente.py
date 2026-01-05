"""
Views de Cliente para SGM v2.
"""

from django.db import models
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from apps.core.models import Cliente, Industria, AsignacionClienteUsuario, Usuario
from apps.core.serializers import (
    ClienteSerializer,
    ClienteDetailSerializer,
    ClienteCreateSerializer,
    IndustriaSerializer,
    AsignacionClienteUsuarioSerializer,
    AsignarAnalistaSerializer,
    AsignarSupervisorSerializer,
    ClienteConAsignacionesSerializer,
    CargaTrabajoSupervisorSerializer,
)
from shared.permissions import IsGerente, IsSupervisor


class IndustriaViewSet(viewsets.ModelViewSet):
    """ViewSet para gestión de industrias."""
    
    queryset = Industria.objects.all()
    serializer_class = IndustriaSerializer
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['nombre']
    ordering = ['nombre']
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), IsGerente()]
        return [IsAuthenticated()]


class ClienteViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión de clientes.
    Los usuarios solo ven los clientes a los que tienen acceso.
    """
    
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['industria', 'activo', 'bilingue']
    search_fields = ['razon_social', 'nombre_comercial', 'rut']
    ordering_fields = ['razon_social', 'fecha_registro']
    ordering = ['razon_social']
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return ClienteDetailSerializer
        if self.action in ['create', 'update', 'partial_update']:
            return ClienteCreateSerializer
        return ClienteSerializer
    
    def get_permissions(self):
        if self.action in ['create', 'destroy']:
            return [IsAuthenticated(), IsGerente()]
        if self.action in ['update', 'partial_update']:
            return [IsAuthenticated(), IsSupervisor()]
        return [IsAuthenticated()]
    
    def get_queryset(self):
        """Filtra clientes según el rol del usuario."""
        user = self.request.user
        queryset = Cliente.objects.select_related('industria')
        
        # Gerentes ven todos los clientes
        if user.tipo_usuario == 'gerente':
            return queryset
        
        # Supervisores ven clientes de sus analistas
        if user.tipo_usuario == 'supervisor':
            analistas_ids = user.analistas_supervisados.values_list('id', flat=True)
            clientes_ids = AsignacionClienteUsuario.objects.filter(
                usuario_id__in=analistas_ids,
                activa=True
            ).values_list('cliente_id', flat=True)
            return queryset.filter(id__in=clientes_ids)
        
        # Analistas y seniors ven solo sus clientes asignados
        clientes_ids = user.asignaciones.filter(activa=True).values_list('cliente_id', flat=True)
        return queryset.filter(id__in=clientes_ids)
    
    @action(detail=True, methods=['get'])
    def cierres(self, request, pk=None):
        """Obtiene los cierres de un cliente específico."""
        cliente = self.get_object()
        # Importar aquí para evitar dependencia circular
        from apps.validador.models import Cierre
        from apps.validador.serializers import CierreListSerializer
        
        cierres = Cierre.objects.filter(cliente=cliente).order_by('-periodo')
        serializer = CierreListSerializer(cierres, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def mis_clientes(self, request):
        """Obtiene solo los clientes asignados directamente al usuario."""
        user = request.user
        clientes_ids = user.asignaciones.filter(activa=True).values_list('cliente_id', flat=True)
        clientes = Cliente.objects.filter(id__in=clientes_ids)
        serializer = ClienteSerializer(clientes, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated, IsGerente])
    def todos(self, request):
        """Lista todos los clientes (solo para gerentes)."""
        queryset = Cliente.objects.select_related('industria').all()
        
        # Aplicar búsqueda
        search = request.query_params.get('search', '')
        if search:
            queryset = queryset.filter(
                models.Q(razon_social__icontains=search) |
                models.Q(nombre_comercial__icontains=search) |
                models.Q(rut__icontains=search)
            )
        
        # Aplicar filtros
        activo = request.query_params.get('activo')
        if activo is not None:
            queryset = queryset.filter(activo=activo.lower() == 'true')
        
        industria = request.query_params.get('industria')
        if industria:
            queryset = queryset.filter(industria_id=industria)
        
        serializer = ClienteSerializer(queryset, many=True)
        return Response(serializer.data)

    # ==================== ENDPOINTS DE ASIGNACIÓN ====================
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated, IsGerente])
    def con_asignaciones(self, request):
        """Lista todos los clientes con sus asignaciones (solo gerentes)."""
        queryset = Cliente.objects.select_related('industria', 'supervisor').prefetch_related(
            'asignaciones__usuario',
            'asignaciones__asignado_por'
        ).all()
        
        # Aplicar búsqueda
        search = request.query_params.get('search', '')
        if search:
            queryset = queryset.filter(
                models.Q(razon_social__icontains=search) |
                models.Q(nombre_comercial__icontains=search) |
                models.Q(rut__icontains=search)
            )
        
        # Filtro por supervisor
        supervisor_id = request.query_params.get('supervisor')
        if supervisor_id:
            queryset = queryset.filter(supervisor_id=supervisor_id)
        
        # Filtro por clientes sin supervisor
        sin_supervisor = request.query_params.get('sin_supervisor')
        if sin_supervisor and sin_supervisor.lower() == 'true':
            queryset = queryset.filter(supervisor__isnull=True)
        
        # Filtro por clientes sin analistas
        sin_analistas = request.query_params.get('sin_analistas')
        if sin_analistas and sin_analistas.lower() == 'true':
            clientes_con_analistas = AsignacionClienteUsuario.objects.filter(
                activa=True
            ).values_list('cliente_id', flat=True)
            queryset = queryset.exclude(id__in=clientes_con_analistas)
        
        serializer = ClienteConAsignacionesSerializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'], permission_classes=[IsAuthenticated, IsGerente])
    def asignaciones(self, request, pk=None):
        """Obtiene las asignaciones de un cliente específico."""
        cliente = self.get_object()
        asignaciones = AsignacionClienteUsuario.objects.filter(
            cliente=cliente,
            activa=True
        ).select_related('usuario', 'asignado_por')
        
        data = {
            'cliente': {
                'id': cliente.id,
                'nombre': cliente.nombre_display,
                'rut': cliente.rut,
            },
            'supervisor': None,
            'analistas': AsignacionClienteUsuarioSerializer(asignaciones, many=True).data,
        }
        
        if cliente.supervisor:
            data['supervisor'] = {
                'id': cliente.supervisor.id,
                'nombre': cliente.supervisor.get_full_name(),
                'email': cliente.supervisor.email,
            }
        
        return Response(data)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsGerente])
    def asignar_supervisor(self, request, pk=None):
        """Asigna un supervisor a un cliente."""
        cliente = self.get_object()
        serializer = AsignarSupervisorSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        supervisor_id = serializer.validated_data.get('supervisor_id')
        
        if supervisor_id:
            supervisor = Usuario.objects.get(id=supervisor_id)
            cliente.supervisor = supervisor
        else:
            cliente.supervisor = None
        
        cliente.save()
        
        return Response({
            'mensaje': 'Supervisor asignado correctamente' if supervisor_id else 'Supervisor desasignado',
            'supervisor': {
                'id': cliente.supervisor.id,
                'nombre': cliente.supervisor.get_full_name(),
            } if cliente.supervisor else None
        })
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsGerente])
    def asignar_analista(self, request, pk=None):
        """Asigna un analista a un cliente."""
        cliente = self.get_object()
        serializer = AsignarAnalistaSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        usuario_id = serializer.validated_data['usuario_id']
        es_principal = serializer.validated_data.get('es_principal', False)
        notas = serializer.validated_data.get('notas', '')
        
        usuario = Usuario.objects.get(id=usuario_id)
        
        # Verificar si ya existe la asignación
        asignacion, created = AsignacionClienteUsuario.objects.get_or_create(
            cliente=cliente,
            usuario=usuario,
            defaults={
                'es_principal': es_principal,
                'notas': notas,
                'activa': True,
                'asignado_por': request.user,
            }
        )
        
        if not created:
            if asignacion.activa:
                return Response(
                    {'error': 'El usuario ya está asignado a este cliente'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            # Reactivar asignación existente
            asignacion.activa = True
            asignacion.es_principal = es_principal
            asignacion.notas = notas
            asignacion.asignado_por = request.user
            asignacion.fecha_desasignacion = None
            asignacion.save()
        
        # Si es principal, desmarcar otros como principal
        if es_principal:
            AsignacionClienteUsuario.objects.filter(
                cliente=cliente,
                activa=True
            ).exclude(id=asignacion.id).update(es_principal=False)
        
        return Response(
            AsignacionClienteUsuarioSerializer(asignacion).data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK
        )
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsGerente], url_path='desasignar_analista/(?P<usuario_id>[^/.]+)')
    def desasignar_analista(self, request, pk=None, usuario_id=None):
        """Desasigna un analista de un cliente."""
        cliente = self.get_object()
        
        try:
            asignacion = AsignacionClienteUsuario.objects.get(
                cliente=cliente,
                usuario_id=usuario_id,
                activa=True
            )
        except AsignacionClienteUsuario.DoesNotExist:
            return Response(
                {'error': 'Asignación no encontrada'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        asignacion.activa = False
        asignacion.fecha_desasignacion = timezone.now()
        asignacion.save()
        
        return Response({'mensaje': 'Analista desasignado correctamente'})
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated, IsGerente])
    def supervisores_carga(self, request):
        """Obtiene la carga de trabajo de todos los supervisores."""
        supervisores = Usuario.objects.filter(
            tipo_usuario__in=['supervisor', 'gerente'],
            is_active=True
        )
        serializer = CargaTrabajoSupervisorSerializer(supervisores, many=True)
        return Response(serializer.data)
