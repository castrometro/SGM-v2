"""
Permisos personalizados para SGM v2.
"""

from rest_framework import permissions


class IsGerente(permissions.BasePermission):
    """Permite acceso solo a usuarios con rol Gerente."""
    
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.tipo_usuario == 'gerente'
        )


class IsSupervisor(permissions.BasePermission):
    """Permite acceso solo a usuarios con rol Supervisor o superior."""
    
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.tipo_usuario in ['supervisor', 'gerente']
        )


class IsSenior(permissions.BasePermission):
    """Permite acceso solo a usuarios con rol Senior o superior."""
    
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.tipo_usuario in ['senior', 'supervisor', 'gerente']
        )


class IsAnalista(permissions.BasePermission):
    """Permite acceso a cualquier usuario autenticado (Analista o superior)."""
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated


class IsOwnerOrSupervisor(permissions.BasePermission):
    """
    Permite acceso si el usuario es el propietario del recurso 
    o es supervisor/gerente.
    """
    
    def has_object_permission(self, request, view, obj):
        # Supervisores y gerentes tienen acceso total
        if request.user.tipo_usuario in ['supervisor', 'gerente']:
            return True
        
        # Para otros, verificar si es el propietario
        if hasattr(obj, 'usuario_analista'):
            return obj.usuario_analista == request.user
        if hasattr(obj, 'usuario'):
            return obj.usuario == request.user
        
        return False


class CanAccessCliente(permissions.BasePermission):
    """
    Verifica que el usuario tenga acceso al cliente específico.
    - Gerentes: Acceso a todos
    - Supervisores: Acceso a clientes de sus analistas
    - Analistas: Solo a sus clientes asignados
    """
    
    def has_object_permission(self, request, view, obj):
        user = request.user
        
        # Gerentes tienen acceso total
        if user.tipo_usuario == 'gerente':
            return True
        
        # Obtener el cliente del objeto
        cliente = getattr(obj, 'cliente', obj)
        
        # Supervisores: acceso a clientes de sus analistas
        if user.tipo_usuario == 'supervisor':
            from apps.core.models import AsignacionClienteUsuario
            analistas_ids = user.analistas_supervisados.values_list('id', flat=True)
            return AsignacionClienteUsuario.objects.filter(
                cliente=cliente,
                usuario_id__in=analistas_ids
            ).exists()
        
        # Analistas: solo sus clientes asignados
        from apps.core.models import AsignacionClienteUsuario
        return AsignacionClienteUsuario.objects.filter(
            cliente=cliente,
            usuario=user
        ).exists()
