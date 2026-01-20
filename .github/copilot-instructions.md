# Copilot Instructions - SGM v2

> Sistema de Gestión de Nómina: validación de cierres, comparación ERP vs archivos analista, gestión de incidencias.

## Instrucciones Específicas por Contexto

> Las siguientes instrucciones se aplican automáticamente según el archivo que estés editando:

| Instrucción | Aplica a | Contenido |
|-------------|----------|-----------|
| [react-instructions.md](.github/instructions/react-instructions.md) | `frontend/**/*.jsx, *.js, *.css` | Componentes, Zustand, React Query, Error Boundaries |
| [audit-compliance-instructions.md](.github/instructions/audit-compliance-instructions.md) | `backend/**/*.py` | ISO 27001, Ley 21.719, retención de datos |
| [libro-processing-instructions.md](.github/instructions/libro-processing-instructions.md) | Procesamiento de nómina | Arquitectura Medallion (Bronce→Plata→Oro) |

## Arquitectura

- **Backend**: Django 5 + DRF + Celery/Redis + PostgreSQL | JWT auth
- **Frontend**: React 18 + Vite + Zustand + TanStack Query + Tailwind CSS
- **Infra**: `docker compose up -d` levanta todo (db, redis, backend, celery, frontend)

```
backend/apps/
├── core/           # Usuarios, Clientes, Servicios, AuditLog
├── validador/      # Cierres, Archivos, Discrepancias, Incidencias (lógica principal)
└── reporteria/     # Dashboards y reportes

frontend/src/
├── features/       # Módulos por dominio (validador/, auth/, dashboard/)
├── stores/         # Zustand (authStore.js) - persistencia tokens
├── hooks/          # usePermissions.js - permisos calculados por backend
└── constants/      # SINCRONIZADO con backend (TipoUsuario, EstadoCierre, etc.)
```

## Patrones Críticos

### 1. Service Layer (Backend) - **OBLIGATORIO**
**NO poner lógica de negocio en views**. Usar servicios que retornan `ServiceResult`:

```python
from apps.validador.services import CierreService
from apps.validador.constants import EstadoCierre

result = CierreService.cambiar_estado(cierre, EstadoCierre.CONSOLIDADO, user)
if result.success:
    return Response(CierreSerializer(result.data).data)
return Response({'error': result.error}, status=400)
```

Servicios: `CierreService`, `ArchivoService`, `IncidenciaService`, `EquipoService`, `LibroService`

### 2. Constantes Centralizadas - **NO magic strings**
```python
# Backend: apps/core/constants.py, apps/validador/constants.py
from apps.core.constants import TipoUsuario
from apps.validador.constants import EstadoCierre

if user.tipo_usuario in TipoUsuario.PUEDEN_APROBAR:  # ['supervisor', 'gerente']
if cierre.estado == EstadoCierre.CONSOLIDADO:
```
```javascript
// Frontend: src/constants/index.js (espejo exacto del backend)
import { TIPO_USUARIO, ESTADO_CIERRE, PUEDEN_APROBAR } from '@/constants'
```

### 3. Autenticación Frontend - Context vs Store
- **Componentes React**: `useAuth()` de AuthContext
- **Axios interceptors**: `useAuthStore.getState()` (fuera de React)
- **Permisos**: `usePermissions()` - consume permisos del endpoint `/api/v1/core/me/`

### 4. Permisos - Backend es la fuente de verdad
Roles con herencia: `analista` < `supervisor` < `gerente`
```python
from shared.permissions import IsSupervisor, IsGerente, CanAccessCliente
```

### 5. Queries Optimizadas - **Siempre select_related/prefetch_related**
```python
Cierre.objects.select_related('cliente', 'analista').filter(...)
```

### 6. ERP Factory/Strategy Pattern
Para parsear archivos de diferentes ERPs (Talana, SAP, Buk):
```python
from apps.validador.services.erp import ERPFactory
strategy = ERPFactory.get_strategy('talana')  # Auto-registrados con decorador
result = strategy.parse_archivo(file, 'libro_remuneraciones')
```

## Arquitectura de Datos: Medallion

El procesamiento del libro de remuneraciones sigue arquitectura medallion:
- **Bronce**: `RegistroLibro`, `RegistroNovedades` - datos crudos extraídos
- **Plata**: Después de comparar y resolver discrepancias
- **Oro**: Consolidado con totales para reportería

Ver detalles en [libro-processing-instructions.md](.github/instructions/libro-processing-instructions.md)

## Flujo de Cierre (7 estados)

```
CARGA_ARCHIVOS → [Generar Comparación] → CON/SIN_DISCREPANCIAS
                                                ↓ (click manual)
                                          CONSOLIDADO
                                                ↓ (detectar manual)
                                      CON/SIN_INCIDENCIAS → FINALIZADO
```

**Reglas clave:**
- `CARGA_ARCHIVOS`: Hub único donde se suben archivos ERP, novedades, se clasifican conceptos y mapean headers
- `SIN_DISCREPANCIAS`: Requiere click **manual** para consolidar (nunca automático)
- Desde `CON_DISCREPANCIAS` se puede **retroceder** a `CARGA_ARCHIVOS`
- Grupos de estados en `EstadoCierre.ESTADOS_ACTIVOS`, `ESTADOS_PUEDEN_RETROCEDER`, etc.

## Tareas Celery (`apps/validador/tasks/`)

- `procesar_archivo_erp` - Procesa libro de remuneraciones
- `procesar_archivo_analista`, `extraer_headers_novedades` - Archivos del cliente
- `ejecutar_comparacion` - Compara ERP vs Novedades
- `detectar_incidencias`, `generar_consolidacion` - Post-comparación

## Auditoría (ISO 27001 / Ley 21.719)

```python
from shared.audit import audit_create, audit_update, modelo_a_dict

def perform_create(self, serializer):
    instancia = serializer.save()
    audit_create(self.request, instancia)

def perform_update(self, serializer):
    datos_ant = modelo_a_dict(serializer.instance)  # ANTES del save
    instancia = serializer.save()
    audit_update(self.request, instancia, datos_ant)
```

Ver [audit-compliance-instructions.md](.github/instructions/audit-compliance-instructions.md) para política de retención y cumplimiento normativo.

## Comandos Útiles

```bash
docker compose up -d                              # Levantar todo
docker compose logs -f backend celery_worker     # Logs backend + celery
docker compose exec backend python manage.py shell
docker compose exec backend python manage.py makemigrations
cd frontend && npm run dev                        # Frontend dev (puerto 5173)
```

## Endpoints Principales

```
POST /api/auth/token/                    - Login JWT
GET  /api/v1/core/me/                    - Usuario + permisos calculados
GET  /api/v1/validador/cierres/          - Lista cierres
POST /api/v1/validador/archivos-erp/     - Subir archivo ERP
POST /api/v1/validador/incidencias/{id}/resolver/
```

## Convenciones

- **Python**: snake_case, PascalCase clases, `models/` como paquete con `help_text`
- **JavaScript**: camelCase, PascalCase componentes `.jsx`
- **Commits**: conventional commits (`feat:`, `fix:`, `refactor:`)
- **Features frontend**: estructura `components/`, `hooks/`, `pages/`, `index.js`

## Archivos de Referencia

- [backend/apps/validador/services/__init__.py](backend/apps/validador/services/__init__.py) - Todos los servicios
- [backend/apps/validador/constants.py](backend/apps/validador/constants.py) - EstadoCierre, grupos de estados
- [backend/shared/permissions.py](backend/shared/permissions.py) - Clases de permisos DRF
- [frontend/src/constants/index.js](frontend/src/constants/index.js) - Espejo de constantes
- [docs/backend/SERVICE_LAYER.md](docs/backend/SERVICE_LAYER.md) - Guía Service Layer
- [docs/backend/FLUJO_CIERRE.md](docs/backend/FLUJO_CIERRE.md) - Diagrama completo de estados
