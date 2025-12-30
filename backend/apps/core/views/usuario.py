"""
Views de Usuario para SGM v2.
"""

from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from apps.core.models import Usuario
from apps.core.serializers import (
    UsuarioSerializer, 
    UsuarioCreateSerializer,
    UsuarioMeSerializer
)
from shared.permissions import IsGerente, IsSupervisor


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
        return UsuarioSerializer
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), IsGerente()]
        return [IsAuthenticated()]
    
    def get_queryset(self):
        """Filtra usuarios según el rol del solicitante."""
        user = self.request.user
        queryset = Usuario.objects.select_related('supervisor')
        
        # Gerentes ven todos
        if user.tipo_usuario == 'gerente':
            return queryset
        
        # Supervisores ven a sus analistas y a sí mismos
        if user.tipo_usuario == 'supervisor':
            from django.db.models import Q
            return queryset.filter(
                Q(id=user.id) | Q(supervisor=user)
            )
        
        # Otros solo se ven a sí mismos
        return queryset.filter(id=user.id)
    
    @action(detail=False, methods=['get'])
    def analistas(self, request):
        """Lista solo usuarios con rol de analista."""
        analistas = self.get_queryset().filter(tipo_usuario='analista', is_active=True)
        serializer = self.get_serializer(analistas, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def supervisores(self, request):
        """Lista solo usuarios con rol de supervisor."""
        supervisores = Usuario.objects.filter(tipo_usuario='supervisor', is_active=True)
        serializer = self.get_serializer(supervisores, many=True)
        return Response(serializer.data)


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
