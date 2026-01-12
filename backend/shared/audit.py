"""
Mixin de auditoría para ViewSets.

Captura automáticamente CREATE, UPDATE, DELETE en ViewSets.

Dos modos de uso:

1. AuditMixin simple (ViewSets sin perform_* personalizado):
    from shared.audit import AuditMixin
    
    class MiViewSet(AuditMixin, viewsets.ModelViewSet):
        audit_campos = ['campo1', 'campo2']  # Opcional

2. Funciones helper (ViewSets con perform_* personalizado):
    from shared.audit import audit_create, audit_update, audit_delete
    
    def perform_create(self, serializer):
        archivo = serializer.save()
        audit_create(self.request, archivo)  # Registra auditoría
        # ... lógica adicional
"""

from apps.core.models import AuditLog
from apps.core.constants import AccionAudit


def modelo_a_dict(instancia, campos=None, excluir=None):
    """
    Convierte una instancia de modelo a dict para auditoría.
    
    Args:
        instancia: Instancia del modelo Django
        campos: Lista de campos a incluir (None = todos)
        excluir: Lista de campos a excluir
    
    Returns:
        Dict con los valores de los campos
    """
    if not instancia:
        return None
    
    excluir = excluir or ['password', 'token']
    data = {}
    opts = instancia._meta
    
    for field in opts.concrete_fields:
        if campos and field.name not in campos:
            continue
        if field.name in excluir:
            continue
        
        value = field.value_from_object(instancia)
        
        # Convertir tipos no serializables a JSON
        if hasattr(value, 'isoformat'):
            value = value.isoformat()
        elif hasattr(value, '__str__') and not isinstance(value, (str, int, float, bool, type(None), list, dict)):
            value = str(value)
        
        data[field.name] = value
    
    return data


# ============================================================================
# Funciones helper para ViewSets con perform_* personalizado
# ============================================================================

def audit_create(request, instancia, campos=None):
    """
    Registra una acción CREATE en auditoría.
    
    Uso:
        def perform_create(self, serializer):
            archivo = serializer.save()
            audit_create(self.request, archivo)
            # ... más lógica
    """
    datos_nuevos = modelo_a_dict(instancia, campos)
    AuditLog.registrar(
        request=request,
        accion=AccionAudit.CREATE,
        instancia=instancia,
        datos_nuevos=datos_nuevos,
    )


def audit_update(request, instancia, datos_anteriores, campos=None):
    """
    Registra una acción UPDATE en auditoría.
    
    Uso:
        def perform_update(self, serializer):
            # Capturar ANTES del save
            datos_ant = modelo_a_dict(serializer.instance)
            
            instancia = serializer.save()
            audit_update(self.request, instancia, datos_ant)
    """
    datos_nuevos = modelo_a_dict(instancia, campos)
    AuditLog.registrar(
        request=request,
        accion=AccionAudit.UPDATE,
        instancia=instancia,
        datos_anteriores=datos_anteriores,
        datos_nuevos=datos_nuevos,
    )


def audit_delete(request, instancia, campos=None):
    """
    Registra una acción DELETE en auditoría.
    LLAMAR ANTES de instance.delete()
    
    Uso:
        def perform_destroy(self, instance):
            audit_delete(self.request, instance)
            instance.delete()
    """
    datos_anteriores = modelo_a_dict(instancia, campos)
    AuditLog.registrar(
        request=request,
        accion=AccionAudit.DELETE,
        instancia=instancia,
        datos_anteriores=datos_anteriores,
    )


# ============================================================================
# Mixin para ViewSets simples (sin perform_* personalizado)
# ============================================================================

class AuditMixin:
    """
    Mixin para agregar auditoría automática a ViewSets.
    
    Intercepta perform_create, perform_update y perform_destroy
    para registrar las acciones en AuditLog.
    
    IMPORTANTE: Si tu ViewSet tiene perform_create/update/destroy personalizado,
    usa las funciones helper (audit_create, audit_update, audit_delete) en su lugar.
    
    Atributos de clase opcionales:
        audit_campos: Lista de campos a incluir en datos (None = todos)
        audit_excluir: Lista de campos a excluir (ej: ['password'])
    
    Uso:
        class SimpleViewSet(AuditMixin, viewsets.ModelViewSet):
            audit_campos = ['estado', 'cliente_id']
    """
    
    # Campos a incluir en auditoría (None = todos)
    audit_campos = None
    # Campos a excluir de auditoría
    audit_excluir = ['password', 'token']
    
    def perform_create(self, serializer):
        """Registra CREATE en auditoría."""
        instancia = serializer.save()
        audit_create(self.request, instancia, self.audit_campos)
        return instancia
    
    def perform_update(self, serializer):
        """Registra UPDATE en auditoría."""
        datos_anteriores = modelo_a_dict(serializer.instance, self.audit_campos)
        instancia = serializer.save()
        audit_update(self.request, instancia, datos_anteriores, self.audit_campos)
        return instancia
    
    def perform_destroy(self, instance):
        """Registra DELETE en auditoría."""
        audit_delete(self.request, instance, self.audit_campos)
        instance.delete()
