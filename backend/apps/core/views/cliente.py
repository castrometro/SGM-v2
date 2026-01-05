"""
Views de Cliente para SGM v2.
"""

from django.db import models
from django.db.models import Q
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from apps.core.models import Cliente, Industria, Usuario
from apps.core.serializers import (
    ClienteSerializer,
    ClienteDetailSerializer,
    ClienteCreateSerializer,
    IndustriaSerializer,
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
        """
        Filtra clientes según el rol del usuario.
        - Gerente: todos los clientes
        - Supervisor: clientes asignados a él + clientes asignados a sus analistas
        - Analista: solo clientes asignados a él
        """
        user = self.request.user
        queryset = Cliente.objects.select_related('industria', 'usuario_asignado')
        
        # Gerentes ven todos los clientes
        if user.tipo_usuario == 'gerente':
            return queryset
        
        # Supervisores ven:
        # - Clientes asignados directamente a ellos
        # - Clientes asignados a analistas que ellos supervisan
        if user.tipo_usuario == 'supervisor':
            return queryset.filter(
                Q(usuario_asignado=user) | 
                Q(usuario_asignado__supervisor=user)
            )
        
        # Analistas ven solo clientes asignados directamente a ellos
        return queryset.filter(usuario_asignado=user)
    
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
        clientes = Cliente.objects.filter(usuario_asignado=user)
        serializer = ClienteSerializer(clientes, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated, IsGerente])
    def todos(self, request):
        """Lista todos los clientes (solo para gerentes)."""
        queryset = Cliente.objects.select_related('industria', 'usuario_asignado').all()
        
        # Aplicar búsqueda
        search = request.query_params.get('search', '')
        if search:
            queryset = queryset.filter(
                Q(razon_social__icontains=search) |
                Q(nombre_comercial__icontains=search) |
                Q(rut__icontains=search)
            )
        
        # Aplicar filtros
        activo = request.query_params.get('activo')
        if activo is not None:
            queryset = queryset.filter(activo=activo.lower() == 'true')
        
        industria = request.query_params.get('industria')
        if industria:
            queryset = queryset.filter(industria_id=industria)
        
        # Filtro por usuario asignado
        usuario_asignado = request.query_params.get('usuario_asignado')
        if usuario_asignado:
            queryset = queryset.filter(usuario_asignado_id=usuario_asignado)
        
        # Filtro por clientes sin asignar
        sin_asignar = request.query_params.get('sin_asignar')
        if sin_asignar and sin_asignar.lower() == 'true':
            queryset = queryset.filter(usuario_asignado__isnull=True)
        
        serializer = ClienteSerializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsGerente])
    def asignar_usuario(self, request, pk=None):
        """
        Asigna un usuario (analista o supervisor) a un cliente.
        Si el usuario es analista, su supervisor hereda acceso automáticamente.
        """
        cliente = self.get_object()
        usuario_id = request.data.get('usuario_id')
        
        if usuario_id:
            try:
                usuario = Usuario.objects.get(id=usuario_id)
            except Usuario.DoesNotExist:
                return Response(
                    {'error': 'Usuario no encontrado'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            if usuario.tipo_usuario not in ['analista', 'supervisor']:
                return Response(
                    {'error': 'El usuario debe ser analista o supervisor'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            if not usuario.is_active:
                return Response(
                    {'error': 'El usuario no está activo'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            cliente.usuario_asignado = usuario
            cliente.save()
            
            # Obtener info del supervisor heredado si aplica
            supervisor_heredado = cliente.get_supervisor_heredado()
            
            return Response({
                'mensaje': 'Usuario asignado correctamente',
                'usuario_asignado': {
                    'id': usuario.id,
                    'nombre': usuario.get_full_name(),
                    'email': usuario.email,
                    'tipo_usuario': usuario.tipo_usuario,
                },
                'supervisor_heredado': {
                    'id': supervisor_heredado.id,
                    'nombre': supervisor_heredado.get_full_name(),
                } if supervisor_heredado else None
            })
        else:
            # Desasignar
            cliente.usuario_asignado = None
            cliente.save()
            return Response({'mensaje': 'Usuario desasignado correctamente'})
    
    @action(detail=True, methods=['get'])
    def info_asignacion(self, request, pk=None):
        """Obtiene información de asignación del cliente."""
        cliente = self.get_object()
        
        data = {
            'cliente': {
                'id': cliente.id,
                'nombre': cliente.nombre_display,
                'rut': cliente.rut,
            },
            'usuario_asignado': None,
            'supervisor_heredado': None,
        }
        
        if cliente.usuario_asignado:
            data['usuario_asignado'] = {
                'id': cliente.usuario_asignado.id,
                'nombre': cliente.usuario_asignado.get_full_name(),
                'email': cliente.usuario_asignado.email,
                'tipo_usuario': cliente.usuario_asignado.tipo_usuario,
            }
            
            supervisor_heredado = cliente.get_supervisor_heredado()
            if supervisor_heredado:
                data['supervisor_heredado'] = {
                    'id': supervisor_heredado.id,
                    'nombre': supervisor_heredado.get_full_name(),
                    'email': supervisor_heredado.email,
                }
        
        return Response(data)
