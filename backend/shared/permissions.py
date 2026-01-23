"""
Permisos personalizados para SGM v2.

Sistema de roles con herencia:
    Gerente > Supervisor > Analista

Cada permiso de nivel superior incluye los de niveles inferiores.
"""

from rest_framework import permissions
from apps.core.constants import TipoUsuario


class IsGerente(permissions.BasePermission):
    """Permite acceso solo a usuarios con rol Gerente."""
    
    message = 'Acceso restringido a Gerentes.'
    
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.tipo_usuario == TipoUsuario.GERENTE
        )


class IsSupervisor(permissions.BasePermission):
    """Permite acceso a usuarios con rol Supervisor o superior (Gerente)."""
    
    message = 'Acceso restringido a Supervisores y Gerentes.'
    
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.tipo_usuario in TipoUsuario.PUEDEN_SUPERVISAR
        )


class IsAnalista(permissions.BasePermission):
    """Permite acceso a cualquier usuario autenticado (Analista o superior)."""
    
    message = 'Debe estar autenticado para acceder.'
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated


class IsOwnerOrSupervisor(permissions.BasePermission):
    """
    Permite acceso si el usuario es el propietario del recurso 
    o es supervisor/gerente.
    
    Busca el propietario en los atributos:
    - usuario_analista
    - usuario
    - created_by
    """
    
    message = 'No tiene permiso para acceder a este recurso.'
    
    def has_object_permission(self, request, view, obj):
        user = request.user
        
        # Gerentes tienen acceso total
        if user.tipo_usuario == TipoUsuario.GERENTE:
            return True
        
        # Supervisores pueden ver recursos de sus analistas
        if user.tipo_usuario == TipoUsuario.SUPERVISOR:
            owner = self._get_owner(obj)
            if owner:
                return owner in user.analistas_supervisados.all() or owner == user
            return True
        
        # Para analistas, verificar si es el propietario
        owner = self._get_owner(obj)
        return owner == user if owner else False
    
    def _get_owner(self, obj):
        """Obtiene el propietario del objeto."""
        for attr in ['usuario_analista', 'usuario', 'created_by']:
            if hasattr(obj, attr):
                return getattr(obj, attr)
        return None


class CanAccessCliente(permissions.BasePermission):
    """
    Verifica que el usuario tenga acceso al cliente específico.
    
    - Gerentes: Acceso a todos los clientes
    - Supervisores: Acceso a clientes de sus analistas supervisados
    - Analistas: Solo a sus clientes asignados
    """
    
    message = 'No tiene acceso a este cliente.'
    
    def has_object_permission(self, request, view, obj):
        user = request.user
        
        # Gerentes tienen acceso total
        if user.tipo_usuario == TipoUsuario.GERENTE:
            return True
        
        # Obtener el cliente del objeto
        from apps.core.models import Cliente
        cliente = getattr(obj, 'cliente', obj)
        
        # Supervisores: acceso a clientes de sus analistas + propios
        if user.tipo_usuario == TipoUsuario.SUPERVISOR:
            analistas_ids = list(user.analistas_supervisados.values_list('id', flat=True))
            analistas_ids.append(user.id)  # Incluir sus propias asignaciones
            return Cliente.objects.filter(
                pk=cliente.pk,
                usuario_asignado_id__in=analistas_ids,
                activo=True
            ).exists()
        
        # Analistas: solo sus clientes asignados
        return cliente.usuario_asignado_id == user.id


class CanAccessCierre(permissions.BasePermission):
    """
    Verifica que el usuario tenga acceso al cierre específico.
    
    - Gerentes: Acceso a todos los cierres
    - Supervisores: Acceso a cierres de sus analistas
    - Analistas: Solo a sus propios cierres
    """
    
    message = 'No tiene acceso a este cierre.'
    
    def has_object_permission(self, request, view, obj):
        user = request.user
        return user.puede_ver_cierre(obj)


class CanApproveIncidencia(permissions.BasePermission):
    """
    Verifica que el usuario pueda aprobar/rechazar incidencias.
    Solo supervisores y gerentes con acceso al cierre relacionado.
    """
    
    message = 'No tiene permiso para aprobar/rechazar incidencias.'
    
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.tipo_usuario in TipoUsuario.PUEDEN_APROBAR
        )
    
    def has_object_permission(self, request, view, obj):
        user = request.user
        return user.puede_aprobar_incidencia(obj)


class IsReadOnlyOrSupervisor(permissions.BasePermission):
    """
    Permite lectura a cualquier usuario autenticado.
    Permite escritura solo a supervisores y gerentes.
    """
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Lectura permitida para todos
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Escritura solo para supervisores y gerentes
        return request.user.tipo_usuario in TipoUsuario.PUEDEN_SUPERVISAR
