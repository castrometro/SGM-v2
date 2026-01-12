"""
Views de Usuario para SGM v2.
"""

from django.db import models
from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from apps.core.models import Usuario
from apps.core.constants import TipoUsuario
from apps.core.serializers import (
    UsuarioSerializer, 
    UsuarioCreateSerializer,
    UsuarioUpdateSerializer,
    UsuarioMeSerializer,
    ResetPasswordSerializer,
    ChangePasswordSerializer,
)
from shared.permissions import IsGerente, IsSupervisor
from shared.audit import audit_create, audit_update, audit_delete, modelo_a_dict


class UsuarioViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión de usuarios.
    Solo gerentes pueden crear/editar usuarios.
    """
    
    queryset = Usuario.objects.all()
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['tipo_usuario', 'is_active', 'supervisor']
    search_fields = ['nombre', 'apellido', 'email']
    ordering_fields = ['nombre', 'apellido', 'fecha_registro']
    ordering = ['apellido', 'nombre']
    
    def get_serializer_class(self):
        if self.action == 'create':
            return UsuarioCreateSerializer
        if self.action in ['update', 'partial_update']:
            return UsuarioUpdateSerializer
        if self.action == 'reset_password':
            return ResetPasswordSerializer
        return UsuarioSerializer
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy', 'reset_password', 'todos']:
            return [IsAuthenticated(), IsGerente()]
        return [IsAuthenticated()]
    
    def get_queryset(self):
        """Filtra usuarios según el rol del solicitante."""
        user = self.request.user
        queryset = Usuario.objects.select_related('supervisor')
        
        # Gerentes ven todos
        if user.tipo_usuario == TipoUsuario.GERENTE:
            return queryset
        
        # Supervisores ven a sus analistas y a sí mismos
        if user.tipo_usuario == TipoUsuario.SUPERVISOR:
            from django.db.models import Q
            return queryset.filter(
                Q(id=user.id) | Q(supervisor=user)
            )
        
        # Otros solo se ven a sí mismos
        return queryset.filter(id=user.id)
    
    def perform_create(self, serializer):
        """Registrar creación de usuario en auditoría."""
        usuario = serializer.save()
        audit_create(self.request, usuario)
    
    def perform_update(self, serializer):
        """Registrar actualización de usuario en auditoría."""
        datos_anteriores = modelo_a_dict(serializer.instance, excluir=['password'])
        usuario = serializer.save()
        audit_update(self.request, usuario, datos_anteriores)
    
    def perform_destroy(self, instance):
        """Registrar eliminación de usuario en auditoría."""
        audit_delete(self.request, instance)
        instance.delete()
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated, IsGerente])
    def todos(self, request):
        """Lista todos los usuarios (solo para gerentes)."""
        queryset = Usuario.objects.select_related('supervisor').all()
        
        # Aplicar búsqueda
        search = request.query_params.get('search', '')
        if search:
            queryset = queryset.filter(
                models.Q(nombre__icontains=search) |
                models.Q(apellido__icontains=search) |
                models.Q(email__icontains=search)
            )
        
        # Filtrar por tipo_usuario
        tipo = request.query_params.get('tipo_usuario')
        if tipo:
            queryset = queryset.filter(tipo_usuario=tipo)
        
        # Filtrar por estado activo
        activo = request.query_params.get('is_active')
        if activo is not None:
            queryset = queryset.filter(is_active=activo.lower() == 'true')
        
        # Filtrar por supervisor
        supervisor = request.query_params.get('supervisor')
        if supervisor:
            queryset = queryset.filter(supervisor_id=supervisor)
        
        serializer = UsuarioSerializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def analistas(self, request):
        """Lista solo usuarios con rol de analista."""
        analistas = self.get_queryset().filter(tipo_usuario=TipoUsuario.ANALISTA, is_active=True)
        serializer = self.get_serializer(analistas, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def supervisores(self, request):
        """Lista solo usuarios con rol de supervisor."""
        supervisores = Usuario.objects.filter(tipo_usuario=TipoUsuario.SUPERVISOR, is_active=True)
        serializer = self.get_serializer(supervisores, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsGerente])
    def reset_password(self, request, pk=None):
        """
        Resetea la contraseña de un usuario (solo gerentes).
        Si no se proporciona contraseña, genera una automáticamente.
        """
        import secrets
        import string
        
        usuario = self.get_object()
        
        # Si se proporciona contraseña manual, validarla
        if request.data.get('new_password'):
            serializer = ResetPasswordSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            new_password = serializer.validated_data['new_password']
            show_password = False
        else:
            # Generar contraseña automática segura (12 caracteres)
            alphabet = string.ascii_letters + string.digits + "!@#$%"
            new_password = ''.join(secrets.choice(alphabet) for _ in range(12))
            show_password = True
        
        usuario.set_password(new_password)
        usuario.save()
        
        response_data = {
            'message': f'Contraseña de {usuario.get_full_name()} actualizada correctamente.',
        }
        
        # Solo devolver la contraseña si fue generada automáticamente
        if show_password:
            response_data['new_password'] = new_password
        
        return Response(response_data)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsGerente])
    def toggle_active(self, request, pk=None):
        """Activa/desactiva un usuario."""
        usuario = self.get_object()
        
        # No permitir desactivarse a sí mismo
        if usuario == request.user:
            return Response(
                {'error': 'No puedes desactivar tu propia cuenta.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        usuario.is_active = not usuario.is_active
        usuario.save()
        
        estado = 'activado' if usuario.is_active else 'desactivado'
        return Response({
            'message': f'Usuario {usuario.get_full_name()} {estado} correctamente.',
            'is_active': usuario.is_active
        })

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsGerente])
    def asignar_supervisor(self, request, pk=None):
        """
        Asigna un supervisor a un analista.
        POST /api/v1/core/usuarios/{id}/asignar_supervisor/
        Body: { "supervisor_id": 123 } o { "supervisor_id": null }
        """
        analista = self.get_object()
        
        # Validar que sea un analista
        if analista.tipo_usuario != TipoUsuario.ANALISTA:
            return Response(
                {'error': 'Solo se puede asignar supervisor a usuarios de tipo analista.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        supervisor_id = request.data.get('supervisor_id')
        
        if supervisor_id is None:
            # Desasignar supervisor
            analista.supervisor = None
            analista.save()
            return Response({
                'message': f'Supervisor desasignado de {analista.get_full_name()}.',
                'analista': UsuarioSerializer(analista).data
            })
        
        # Validar que el supervisor exista y sea supervisor/gerente
        try:
            supervisor = Usuario.objects.get(pk=supervisor_id)
        except Usuario.DoesNotExist:
            return Response(
                {'error': 'Supervisor no encontrado.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        if supervisor.tipo_usuario not in TipoUsuario.PUEDEN_SER_SUPERVISORES:
            return Response(
                {'error': 'El usuario seleccionado no es supervisor ni gerente.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not supervisor.is_active:
            return Response(
                {'error': 'El supervisor seleccionado no está activo.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        analista.supervisor = supervisor
        analista.save()
        
        return Response({
            'message': f'{analista.get_full_name()} asignado a {supervisor.get_full_name()}.',
            'analista': UsuarioSerializer(analista).data
        })

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated, IsGerente])
    def sin_supervisor(self, request):
        """
        Lista analistas sin supervisor asignado.
        GET /api/v1/core/usuarios/sin_supervisor/
        """
        analistas = Usuario.objects.filter(
            tipo_usuario=TipoUsuario.ANALISTA,
            supervisor__isnull=True,
            is_active=True
        ).select_related('supervisor')
        
        serializer = UsuarioSerializer(analistas, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated, IsGerente])
    def carga_supervisores(self, request):
        """
        Muestra cantidad de analistas por supervisor.
        GET /api/v1/core/usuarios/carga_supervisores/
        """
        from django.db.models import Count
        
        supervisores = Usuario.objects.filter(
            tipo_usuario__in=TipoUsuario.PUEDEN_SER_SUPERVISORES,
            is_active=True
        ).annotate(
            total_analistas=Count('analistas_supervisados', filter=models.Q(analistas_supervisados__is_active=True))
        ).order_by('-total_analistas')
        
        data = [{
            'id': s.id,
            'nombre': s.get_full_name(),
            'email': s.email,
            'tipo_usuario': s.tipo_usuario,
            'total_analistas': s.total_analistas,
            'analistas': [
                {'id': a.id, 'nombre': a.get_full_name(), 'email': a.email}
                for a in s.analistas_supervisados.filter(is_active=True)
            ]
        } for s in supervisores]
        
        return Response(data)

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated, IsGerente])
    def reasignacion_masiva(self, request):
        """
        Reasigna múltiples analistas a un nuevo supervisor.
        POST /api/v1/core/usuarios/reasignacion_masiva/
        Body: { "analista_ids": [1, 2, 3], "supervisor_id": 5 }
        """
        analista_ids = request.data.get('analista_ids', [])
        supervisor_id = request.data.get('supervisor_id')
        
        if not analista_ids:
            return Response(
                {'error': 'Debe proporcionar al menos un analista.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validar supervisor
        supervisor = None
        if supervisor_id is not None:
            try:
                supervisor = Usuario.objects.get(pk=supervisor_id)
                if supervisor.tipo_usuario not in TipoUsuario.PUEDEN_SER_SUPERVISORES:
                    return Response(
                        {'error': 'El usuario seleccionado no es supervisor ni gerente.'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            except Usuario.DoesNotExist:
                return Response(
                    {'error': 'Supervisor no encontrado.'},
                    status=status.HTTP_404_NOT_FOUND
                )
        
        # Actualizar analistas
        updated = Usuario.objects.filter(
            id__in=analista_ids,
            tipo_usuario=TipoUsuario.ANALISTA
        ).update(supervisor=supervisor)
        
        mensaje = f'{updated} analista(s) reasignado(s)'
        if supervisor:
            mensaje += f' a {supervisor.get_full_name()}'
        else:
            mensaje += ' (supervisor removido)'
        
        return Response({'message': mensaje, 'updated': updated})


class MeView(APIView):
    """
    Vista para obtener información del usuario autenticado.
    GET /api/v1/core/me/
    """
    
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        serializer = UsuarioMeSerializer(request.user)
        return Response(serializer.data)
    
    def patch(self, request):
        """Permite al usuario actualizar ciertos campos de su perfil."""
        allowed_fields = ['nombre', 'apellido', 'cargo']
        data = {k: v for k, v in request.data.items() if k in allowed_fields}
        
        serializer = UsuarioSerializer(request.user, data=data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return Response(UsuarioMeSerializer(request.user).data)
