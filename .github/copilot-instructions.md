# Copilot Instructions - SGM v2

> Sistema de Gestión de Nómina: validación de cierres, comparación ERP vs archivos analista, gestión de incidencias.

## Arquitectura

- **Backend**: Django 5 + DRF + Celery/Redis (tareas async) + PostgreSQL | JWT auth
- **Frontend**: React 18 + Vite + Zustand + TanStack Query + Tailwind CSS
- **Infra**: Docker Compose (ver `docker-compose.yml`)

```
backend/apps/
├── core/           # Usuarios, Clientes, Servicios
├── validador/      # Cierres, Archivos, Discrepancias, Incidencias (lógica principal)
└── reporteria/     # Dashboards y reportes

frontend/src/
├── features/       # Módulos por dominio (validador/, auth/, dashboard/)
├── stores/         # Zustand (authStore.js)
├── hooks/          # usePermissions.js, custom hooks
└── constants/      # Espejo de constantes backend
```

## Patrones Críticos

### 1. Service Layer (Backend)
**NO poner lógica de negocio en views**. Usar servicios en `apps/validador/services/`:

```python
from apps.validador.services import CierreService, ServiceResult

result = CierreService.cambiar_estado(cierre, 'consolidado', user)
if result.success:
    return Response(CierreSerializer(result.data).data)
return Response({'error': result.error}, status=400)
```

Servicios disponibles: `CierreService`, `ArchivoService`, `IncidenciaService`, `EquipoService`

### 2. Constantes Centralizadas
**NO usar magic strings**. Backend y frontend sincronizados:

```python
# Backend: apps/core/constants.py, apps/validador/constants.py
from apps.core.constants import TipoUsuario
from apps.validador.constants import EstadoCierre

if user.tipo_usuario in TipoUsuario.PUEDEN_APROBAR:
if cierre.estado == EstadoCierre.CONSOLIDADO:
```

```javascript
// Frontend: src/constants/index.js
import { TIPO_USUARIO, ESTADO_CIERRE, PUEDEN_APROBAR } from '@/constants'
```

### 3. Autenticación Frontend
**En componentes React**: usar `useAuth()` (AuthContext)
**En axios interceptors**: usar `useAuthStore.getState()` (ver `src/api/axios.js`)
**Para permisos**: usar `usePermissions()` - consume permisos calculados por backend

```javascript
const { user, isAuthenticated, login, logout } = useAuth()
const { canApproveIncidencia, canManageUsers } = usePermissions()
```

### 4. Permisos Backend
Los permisos se calculan en backend y se envían en `/api/v1/core/me/`. Usar clases de `shared/permissions.py`:

```python
from shared.permissions import IsSupervisor, IsGerente, CanAccessCliente
```

Roles: `analista` < `supervisor` < `gerente` (herencia de permisos)

### 5. Queries Optimizadas
**NO hacer N+1**. Siempre usar `select_related`/`prefetch_related`:

```python
Cierre.objects.select_related('cliente', 'analista').filter(...)
```

## Flujo de Cierre

El flujo del cierre tiene dos fases de carga de archivos:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  FASE 1: LIBRO ERP              FASE 2: NOVEDADES CLIENTE                   │
│  ──────────────────             ─────────────────────────                   │
│  carga_archivos (ERP) ──────→ clasificacion_conceptos ──────→              │
│                                                                             │
│  carga_novedades (cliente) ──→ mapeo_items ──→ comparacion ──→             │
│                                                                             │
│  con_discrepancias (loop) ──→ consolidado ──→ deteccion_incidencias ──→    │
│                                                                             │
│  revision_incidencias ──→ finalizado                                        │
└─────────────────────────────────────────────────────────────────────────────┘
```

**IMPORTANTE**: Las novedades se cargan DESPUÉS del libro porque:
- Necesitamos los conceptos clasificados para mapear items
- La comparación requiere ambos procesados

Estados definidos en `EstadoCierre.CHOICES`. Ver `apps/validador/constants.py` para grupos de estados.

## Tareas Celery

<!-- TODO: Documentar tareas async disponibles -->

Tareas en `apps/validador/tasks/`:
- `procesar_erp.py` - Procesamiento de archivos ERP
- `procesar_analista.py` - Procesamiento de archivos del analista
- `comparacion.py` - Comparación ERP vs Analista

## Comandos

```bash
docker compose up -d                    # Levantar todo
docker compose logs -f backend          # Logs backend
docker compose exec backend python manage.py shell
docker compose exec backend python manage.py makemigrations
cd frontend && npm run dev              # Frontend dev server
```

## Endpoints Principales

```
POST /api/auth/token/              - Login (JWT)
GET  /api/v1/core/me/              - Usuario + permisos
GET  /api/v1/core/audit-logs/      - Logs de auditoría (solo gerentes)
GET  /api/v1/validador/cierres/    - Lista cierres
GET  /api/v1/validador/cierres/{id}/resumen/  - Resumen cierre
POST /api/v1/validador/archivos-erp/          - Subir archivo ERP
POST /api/v1/validador/incidencias/{id}/resolver/  - Resolver incidencia
```

## Auditoría

Para cumplimiento ISO 27001 y Ley 21.719, usar funciones de `shared/audit.py`:

```python
from shared.audit import audit_create, audit_update, audit_delete, modelo_a_dict

# En perform_create
def perform_create(self, serializer):
    instancia = serializer.save()
    audit_create(self.request, instancia)

# En perform_update
def perform_update(self, serializer):
    datos_ant = modelo_a_dict(serializer.instance)  # ANTES del save
    instancia = serializer.save()
    audit_update(self.request, instancia, datos_ant)
```

Ver [docs/backend/AUDIT_SYSTEM.md](docs/backend/AUDIT_SYSTEM.md) para documentación completa.

## Convenciones

- **Python**: snake_case (variables), PascalCase (clases)
- **JavaScript**: camelCase (variables), PascalCase (componentes .jsx)
- **Commits**: conventional commits (`feat:`, `fix:`, `refactor:`)
- **Modelos**: usar `models/` como paquete, documentar con `help_text`
- **Features frontend**: estructura `components/`, `hooks/`, `pages/`, `index.js`

## Archivos Clave

- [backend/apps/validador/services/__init__.py](backend/apps/validador/services/__init__.py) - Service Layer exports
- [backend/shared/permissions.py](backend/shared/permissions.py) - Clases de permisos DRF
- [backend/shared/audit.py](backend/shared/audit.py) - Funciones de auditoría
- [frontend/src/constants/index.js](frontend/src/constants/index.js) - Constantes frontend
- [frontend/src/hooks/usePermissions.js](frontend/src/hooks/usePermissions.js) - Hook de permisos
- [frontend/src/contexts/AuthContext.jsx](frontend/src/contexts/AuthContext.jsx) - Auth provider
- [docs/backend/SERVICE_LAYER.md](docs/backend/SERVICE_LAYER.md) - Guía detallada del Service Layer
- [docs/backend/AUDIT_SYSTEM.md](docs/backend/AUDIT_SYSTEM.md) - Sistema de auditoría
- [docs/backend/NOVEDADES.md](docs/backend/NOVEDADES.md) - Archivo de novedades del cliente
- [docs/backend/AUDIT_SYSTEM.md](docs/backend/AUDIT_SYSTEM.md) - Sistema de auditoría
