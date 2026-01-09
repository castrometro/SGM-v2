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

from apps.core.models import Cliente, Industria, Usuario, ERP, ConfiguracionERPCliente
from apps.core.constants import TipoUsuario
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
        queryset = Cliente.objects.select_related(
            'industria', 
            'usuario_asignado'
        ).prefetch_related(
            'configuraciones_erp',
            'configuraciones_erp__erp'
        )
        
        # Gerentes ven todos los clientes
        if user.tipo_usuario == TipoUsuario.GERENTE:
            return queryset
        
        # Supervisores ven:
        # - Clientes asignados directamente a ellos
        # - Clientes asignados a analistas que ellos supervisan
        if user.tipo_usuario == TipoUsuario.SUPERVISOR:
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
            
            if usuario.tipo_usuario not in TipoUsuario.PUEDEN_SER_ASIGNADOS_CLIENTE:
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

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated, IsSupervisor])
    def mi_equipo(self, request):
        """
        Obtiene clientes agrupados por analista del equipo del supervisor.
        Solo para supervisores y gerentes.
        """
        user = request.user
        
        # Obtener analistas del equipo
        if user.tipo_usuario == TipoUsuario.GERENTE:
            # Gerente ve todos los analistas
            analistas = Usuario.objects.filter(
                tipo_usuario=TipoUsuario.ANALISTA,
                is_active=True
            ).select_related('supervisor')
        else:
            # Supervisor ve solo sus analistas
            analistas = user.analistas_supervisados.filter(is_active=True)
        
        # Construir respuesta con clientes por analista
        resultado = []
        for analista in analistas:
            clientes_analista = Cliente.objects.filter(
                usuario_asignado=analista,
                activo=True
            ).select_related('industria')
            
            resultado.append({
                'analista': {
                    'id': analista.id,
                    'nombre': analista.get_full_name(),
                    'email': analista.email,
                },
                'total_clientes': clientes_analista.count(),
                'clientes': ClienteSerializer(clientes_analista, many=True).data
            })
        
        # Agregar clientes asignados directamente al supervisor (si no es gerente)
        if user.tipo_usuario == TipoUsuario.SUPERVISOR:
            clientes_supervisor = Cliente.objects.filter(
                usuario_asignado=user,
                activo=True
            ).select_related('industria')
            
            resultado.insert(0, {
                'analista': {
                    'id': user.id,
                    'nombre': f"{user.get_full_name()} (Yo)",
                    'email': user.email,
                },
                'total_clientes': clientes_supervisor.count(),
                'clientes': ClienteSerializer(clientes_supervisor, many=True).data
            })
        
        # Estadísticas generales
        total_clientes = sum(item['total_clientes'] for item in resultado)
        
        return Response({
            'equipo': resultado,
            'estadisticas': {
                'total_analistas': len(analistas),
                'total_clientes': total_clientes,
            }
        })

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsSupervisor])
    def reasignar(self, request, pk=None):
        """
        Reasigna un cliente a otro analista del equipo del supervisor.
        El supervisor solo puede reasignar a analistas de su equipo.
        """
        cliente = self.get_object()
        user = request.user
        nuevo_usuario_id = request.data.get('usuario_id')
        
        if not nuevo_usuario_id:
            return Response(
                {'error': 'Debe especificar el usuario al que reasignar'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            nuevo_usuario = Usuario.objects.get(id=nuevo_usuario_id)
        except Usuario.DoesNotExist:
            return Response(
                {'error': 'Usuario no encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Validar permisos
        if user.tipo_usuario == TipoUsuario.GERENTE:
            # Gerente puede reasignar a cualquier analista/supervisor
            if nuevo_usuario.tipo_usuario not in TipoUsuario.PUEDEN_SER_ASIGNADOS_CLIENTE:
                return Response(
                    {'error': 'Solo se puede asignar a analistas o supervisores'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        else:
            # Supervisor solo puede reasignar entre su equipo o a sí mismo
            es_su_equipo = (
                nuevo_usuario.id == user.id or
                nuevo_usuario.supervisor_id == user.id
            )
            if not es_su_equipo:
                return Response(
                    {'error': 'Solo puede reasignar a analistas de su equipo'},
                    status=status.HTTP_403_FORBIDDEN
                )
        
        if not nuevo_usuario.is_active:
            return Response(
                {'error': 'El usuario no está activo'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Guardar usuario anterior para log
        usuario_anterior = cliente.usuario_asignado
        
        # Reasignar
        cliente.usuario_asignado = nuevo_usuario
        cliente.save()
        
        return Response({
            'mensaje': f'Cliente reasignado a {nuevo_usuario.get_full_name()}',
            'cliente': ClienteSerializer(cliente).data,
            'usuario_anterior': {
                'id': usuario_anterior.id,
                'nombre': usuario_anterior.get_full_name(),
            } if usuario_anterior else None,
            'usuario_nuevo': {
                'id': nuevo_usuario.id,
                'nombre': nuevo_usuario.get_full_name(),
            }
        })

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsGerente])
    def asignar_erp(self, request, pk=None):
        """
        Asigna o cambia el ERP activo de un cliente.
        Solo para gerentes.
        
        Body:
            erp_id: ID del ERP a asignar (null para quitar asignación)
        """
        cliente = self.get_object()
        erp_id = request.data.get('erp_id')
        
        if erp_id is None:
            # Desactivar configuración actual
            ConfiguracionERPCliente.objects.filter(
                cliente=cliente,
                activo=True
            ).update(activo=False)
            
            return Response({
                'mensaje': 'ERP desasignado del cliente',
                'erp_activo': None
            })
        
        # Validar que el ERP existe y está activo
        try:
            erp = ERP.objects.get(id=erp_id, activo=True)
        except ERP.DoesNotExist:
            return Response(
                {'error': 'ERP no encontrado o no está activo'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Desactivar configuración actual si existe
        ConfiguracionERPCliente.objects.filter(
            cliente=cliente,
            activo=True
        ).update(activo=False)
        
        # Crear o actualizar configuración para el nuevo ERP
        config, created = ConfiguracionERPCliente.objects.update_or_create(
            cliente=cliente,
            erp=erp,
            defaults={
                'activo': True,
                'fecha_activacion': timezone.now().date(),
            }
        )
        
        return Response({
            'mensaje': f'ERP {erp.nombre} asignado correctamente',
            'erp_activo': {
                'id': erp.id,
                'nombre': erp.nombre,
                'slug': erp.slug,
            }
        })
