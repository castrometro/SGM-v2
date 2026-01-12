# Sistema de Auditoría - SGM v2

> Documentación del sistema de auditoría para cumplimiento ISO 27001:2022 y Ley 21.719 Chile.

## Visión General

El sistema de auditoría captura:

1. **Task Results (Celery)**: Registro de todas las tareas asíncronas ejecutadas
2. **AuditLog (CRUD)**: Registro de acciones de creación, actualización y eliminación

### Cumplimiento

| Estándar | Controles |
|----------|-----------|
| ISO 27001:2022 | A.8.15 (Logging), A.8.16 (Monitoring) |
| ISO 27701:2019 | Privacy controls |
| Ley 21.719 Chile | Protección de datos personales |

## Arquitectura

```
┌─────────────────────────────────────────────────────────┐
│                    ViewSets                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐      │
│  │  Cierre     │  │ ArchivoERP  │  │ Incidencia  │      │
│  │  ViewSet    │  │  ViewSet    │  │  ViewSet    │      │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘      │
│         │                │                │              │
│         ▼                ▼                ▼              │
│  ┌────────────────────────────────────────────────┐     │
│  │              shared/audit.py                    │     │
│  │  audit_create() | audit_update() | audit_delete │     │
│  └──────────────────────┬─────────────────────────┘     │
│                         │                                │
│                         ▼                                │
│  ┌────────────────────────────────────────────────┐     │
│  │           AuditLog.registrar()                  │     │
│  │  - Captura usuario, IP, User-Agent              │     │
│  │  - Serializa datos antes/después                │     │
│  │  - Extrae cliente_id automáticamente            │     │
│  └──────────────────────┬─────────────────────────┘     │
│                         │                                │
│                         ▼                                │
│  ┌────────────────────────────────────────────────┐     │
│  │              PostgreSQL                         │     │
│  │  core_auditlog table                            │     │
│  └────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────┘
```

## Uso

### 1. Para ViewSets Simples (sin perform_* personalizado)

```python
from shared.audit import AuditMixin

class MiViewSet(AuditMixin, viewsets.ModelViewSet):
    # La auditoría es automática para create, update, destroy
    pass
```

### 2. Para ViewSets con Lógica Personalizada

```python
from shared.audit import audit_create, audit_update, audit_delete, modelo_a_dict

class CierreViewSet(viewsets.ModelViewSet):
    
    def perform_create(self, serializer):
        cierre = serializer.save(analista=self.request.user)
        audit_create(self.request, cierre)  # ← Agregar
        
    def perform_update(self, serializer):
        datos_anteriores = modelo_a_dict(serializer.instance)  # ← ANTES del save
        cierre = serializer.save()
        audit_update(self.request, cierre, datos_anteriores)  # ← DESPUÉS del save
        
    def perform_destroy(self, instance):
        audit_delete(self.request, instance)  # ← ANTES del delete
        instance.delete()
```

### 3. Para Acciones Custom (como resolver incidencia)

```python
@action(detail=True, methods=['post'])
def resolver(self, request, pk=None):
    incidencia = self.get_object()
    
    # Capturar estado anterior
    datos_anteriores = modelo_a_dict(incidencia)
    
    # Ejecutar lógica de negocio
    result = IncidenciaService.resolver(incidencia, ...)
    
    # Registrar en auditoría
    audit_update(request, result.data, datos_anteriores)
    
    return Response(...)
```

## Modelo AuditLog

```python
class AuditLog(models.Model):
    # Usuario que realizó la acción
    usuario = models.ForeignKey(Usuario, null=True, on_delete=models.SET_NULL)
    usuario_email = models.EmailField()  # Copia inmutable
    
    # Información del request
    ip_address = models.GenericIPAddressField(null=True)
    user_agent = models.TextField(blank=True)
    
    # Acción realizada
    accion = models.CharField(max_length=20)  # create, update, delete, etc.
    
    # Objeto afectado
    modelo = models.CharField(max_length=100)  # ej: "validador.cierre"
    objeto_id = models.PositiveIntegerField()
    objeto_repr = models.CharField(max_length=200)  # str() del objeto
    
    # Trazabilidad por cliente
    cliente_id = models.PositiveIntegerField(null=True)
    
    # Datos del cambio (JSON)
    datos_anteriores = models.JSONField(null=True)
    datos_nuevos = models.JSONField(null=True)
    
    # Request info
    endpoint = models.CharField(max_length=500, blank=True)
    metodo_http = models.CharField(max_length=10, blank=True)
    
    # Timestamp inmutable
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
```

## API Endpoint

### GET `/api/v1/core/audit-logs/`

**Permisos**: Solo gerentes (`IsGerente`)

**Filtros disponibles**:

| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| `fecha_desde` | date | Fecha mínima (YYYY-MM-DD) |
| `fecha_hasta` | date | Fecha máxima (YYYY-MM-DD) |
| `usuario_email` | string | Email del usuario (búsqueda parcial) |
| `modelo` | string | Modelo afectado (ej: `validador.cierre`) |
| `accion` | string | Tipo de acción (`create`, `update`, `delete`) |
| `cliente_id` | integer | ID del cliente |

**Ejemplo**:

```bash
GET /api/v1/core/audit-logs/?accion=update&modelo=validador.cierre&fecha_desde=2026-01-01
```

**Respuesta**:

```json
{
  "count": 42,
  "next": "http://...",
  "results": [
    {
      "id": 1,
      "timestamp": "2026-01-12T13:55:11.123456Z",
      "usuario_email": "analista@bdo.cl",
      "accion": "update",
      "modelo": "validador.cierre",
      "objeto_id": 1,
      "objeto_repr": "Empresa X - 202501",
      "cliente_id": 5,
      "ip_address": "192.168.1.100"
    }
  ]
}
```

### GET `/api/v1/core/audit-logs/{id}/`

Detalle completo incluyendo `datos_anteriores` y `datos_nuevos`.

## Constantes

```python
from apps.core.constants import AccionAudit

AccionAudit.CREATE   # "create"
AccionAudit.UPDATE   # "update"  
AccionAudit.DELETE   # "delete"
AccionAudit.LOGIN    # "login"
AccionAudit.LOGOUT   # "logout"
AccionAudit.EXPORT   # "export"
```

## Retención de Datos

| Tipo | Retención | Justificación |
|------|-----------|---------------|
| AuditLog | 365 días | Requisito legal Ley 21.719 |
| TaskResult (Celery) | 90 días | Operacional |

### Tareas de Limpieza

```python
# Celery tasks (ejecutadas automáticamente)
cleanup_task_results   # Cada 24h, elimina TaskResults > 90 días
cleanup_audit_logs     # Cada 24h, elimina AuditLogs > 365 días
```

## Admin Django

El modelo `AuditLog` está registrado en el admin de Django:

- **Vista**: Solo lectura
- **Filtros**: Por acción, modelo, fecha
- **Búsqueda**: Por email, IP, objeto
- **Permisos**: Solo superusuarios pueden eliminar (para compliance)

URL: `/admin/core/auditlog/`

## ViewSets Auditados

| ViewSet | CREATE | UPDATE | DELETE |
|---------|--------|--------|--------|
| UsuarioViewSet | ✅ | ✅ | ✅ |
| ClienteViewSet | ✅ | ✅ | ✅ |
| CierreViewSet | ✅ | ✅ | ✅ |
| ArchivoERPViewSet | ✅ | - | ✅ |
| ArchivoAnalistaViewSet | ✅ | - | ✅ |
| IncidenciaViewSet | - | ✅ (resolver) | - |

## Extracción Automática de cliente_id

El sistema extrae automáticamente el `cliente_id` de los objetos para facilitar auditorías por cliente:

1. Directamente del objeto si tiene atributo `cliente_id`
2. Del atributo `cliente` si existe
3. Del atributo `cierre.cliente_id` si existe (para archivos, incidencias, etc.)

## Archivos Clave

| Archivo | Descripción |
|---------|-------------|
| `backend/apps/core/models/audit.py` | Modelo AuditLog |
| `backend/shared/audit.py` | Mixin y funciones helper |
| `backend/apps/core/constants.py` | AccionAudit |
| `backend/apps/core/views/audit.py` | AuditLogViewSet |
| `backend/apps/core/serializers/audit.py` | Serializers |
| `backend/apps/core/tasks/cleanup.py` | Tareas de limpieza |

## Consideraciones de Seguridad

1. **Inmutabilidad**: Los registros de auditoría no se pueden modificar desde la API
2. **Eliminación**: Solo superusuarios pueden eliminar desde el admin
3. **Datos sensibles**: Excluye automáticamente campos como `password`, `token`
4. **IP Real**: Soporta `X-Forwarded-For` para detectar IP detrás de proxy/LB
