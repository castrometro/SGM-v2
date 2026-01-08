# Copilot Instructions - SGM v2

## Descripción del Proyecto

SGM (Sistema de Gestión de Nómina) es una aplicación web para validación y gestión de cierres de nómina. Permite a analistas subir archivos de nómina, compararlos con datos del ERP, detectar discrepancias e incidencias, y gestionar el proceso de cierre mensual.

## Stack Tecnológico

### Backend
- **Framework**: Django 5.x + Django REST Framework
- **Base de datos**: PostgreSQL
- **Tareas asíncronas**: Celery + Redis
- **Autenticación**: JWT (SimpleJWT)
- **Python**: 3.12+

### Frontend
- **Framework**: React 18 + Vite
- **Estado global**: Zustand (con persist middleware)
- **Data fetching**: TanStack Query (React Query)
- **Estilos**: Tailwind CSS
- **Routing**: React Router v6
- **Iconos**: Lucide React

### Infraestructura
- **Contenedores**: Docker + Docker Compose
- **Servidor web**: Nginx (producción)

## Estructura del Proyecto

```
SGM-v2/
├── backend/
│   ├── apps/
│   │   ├── core/           # Usuarios, Clientes, modelos base
│   │   ├── validador/      # Cierres, Archivos, Discrepancias, Incidencias
│   │   └── reporteria/     # Reportes y dashboards
│   ├── shared/             # Permisos, utilidades compartidas
│   └── sgm_backend/        # Configuración Django
├── frontend/
│   └── src/
│       ├── components/     # Componentes reutilizables
│       ├── features/       # Módulos por funcionalidad
│       ├── hooks/          # Custom hooks
│       ├── stores/         # Zustand stores
│       ├── services/       # API calls (axios)
│       └── utils/          # Utilidades
└── docs/                   # Documentación
```

## Patrones y Convenciones

### Backend

#### Service Layer
La lógica de negocio está centralizada en servicios (`apps/validador/services/`):

```python
from apps.validador.services import CierreService

# En views, usar servicios en lugar de lógica inline
result = CierreService.cambiar_estado(cierre, 'consolidado', user)
if result.success:
    return Response(serializer(result.data).data)
else:
    return Response({'error': result.error}, status=400)
```

#### ServiceResult Pattern
Todos los servicios retornan `ServiceResult`:

```python
from apps.validador.services import ServiceResult

# Éxito
return ServiceResult.ok(data=objeto)

# Error
return ServiceResult.fail("Mensaje de error")
```

#### Permisos
Usar clases de permisos de `shared/permissions.py`:

```python
from shared.permissions import IsSupervisor, IsGerente

class MiViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsSupervisor]
```

#### Modelos
- Usar `models/` como paquete (no archivo único)
- Heredar de modelos base cuando aplique
- Documentar campos con `help_text`

### Frontend

#### Estructura de Features
Cada feature tiene su propia carpeta con:
```
features/validador/
├── components/     # Componentes específicos
├── hooks/          # Hooks específicos
├── pages/          # Páginas/vistas
└── index.js        # Exports públicos
```

#### Estado Global (Zustand)
```javascript
// stores/authStore.js
import { create } from 'zustand'
import { persist } from 'zustand/middleware'

export const useAuthStore = create(
  persist(
    (set) => ({
      user: null,
      setUser: (user) => set({ user }),
    }),
    { name: 'auth-storage' }
  )
)
```

#### Data Fetching (React Query)
```javascript
// hooks/useCierres.js
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'

export const useCierres = () => {
  return useQuery({
    queryKey: ['cierres'],
    queryFn: () => cierreService.getAll(),
  })
}
```

#### Componentes
- Usar functional components con hooks
- Props destructuring en parámetros
- Documentar props complejas con JSDoc

#### Estilos (Tailwind)
- Usar `cn()` utility para clases condicionales
- Colores del tema: `primary`, `secondary`, `accent`
- Clases responsive: `sm:`, `md:`, `lg:`

## Roles de Usuario

| Rol | Permisos |
|-----|----------|
| `analista` | Ver/editar sus cierres y clientes asignados |
| `supervisor` | + Ver equipo, aprobar incidencias |
| `senior` | + Gestión extendida de equipo |
| `gerente` | Acceso total, administración |

## Flujo de Cierre

```
pendiente → en_proceso → carga_archivos → procesando → comparacion 
    → consolidado → deteccion_incidencias → revision_incidencias → finalizado
```

## Convenciones de Código

### Nombres
- **Python**: snake_case para variables/funciones, PascalCase para clases
- **JavaScript**: camelCase para variables/funciones, PascalCase para componentes
- **Archivos Python**: snake_case.py
- **Archivos React**: PascalCase.jsx para componentes, camelCase.js para utils

### Commits
Usar conventional commits:
- `feat:` Nueva funcionalidad
- `fix:` Corrección de bug
- `refactor:` Refactorización
- `docs:` Documentación
- `style:` Formato/estilos
- `test:` Tests

### Imports
```python
# Python - orden
import stdlib
import third_party
from django import ...
from apps.core import ...
from . import ...
```

```javascript
// JavaScript - orden
import React from 'react'
import { externas } from 'libreria'
import { internas } from '@/components'
import { locales } from './archivo'
```

## API Endpoints Principales

```
/api/auth/login/          POST   - Login
/api/auth/me/             GET    - Usuario actual
/api/cierres/             GET    - Lista cierres
/api/cierres/{id}/        GET    - Detalle cierre
/api/cierres/{id}/resumen/ GET   - Resumen de cierre
/api/cierres/cierres_equipo/ GET - Cierres del equipo (supervisor+)
/api/archivos-erp/        POST   - Subir archivo ERP
/api/archivos-analista/   POST   - Subir archivo analista
/api/incidencias/         GET    - Lista incidencias
/api/incidencias/{id}/resolver/ POST - Resolver incidencia
```

## Cosas a Evitar

1. **No poner lógica de negocio en views** - Usar Service Layer
2. **No duplicar lógica de permisos** - Centralizar en backend
3. **No usar magic strings** - Usar constantes (Issue #18)
4. **No mezclar Context y Zustand** - Preferir Zustand (Issue #16)
5. **No hacer queries N+1** - Usar `select_related`/`prefetch_related`
6. **No hardcodear URLs** - Usar variables de entorno

## Issues Técnicos Pendientes

- #16: Consolidar Context API vs Zustand
- #17: Centralizar lógica de permisos
- #18: Eliminar magic strings

## Comandos Útiles

```bash
# Levantar entorno
docker compose up -d

# Ver logs backend
docker compose logs -f backend

# Shell Django
docker compose exec backend python manage.py shell

# Migraciones
docker compose exec backend python manage.py makemigrations
docker compose exec backend python manage.py migrate

# Frontend dev
cd frontend && npm run dev
```

## Documentación Adicional

- `/docs/SERVICE_LAYER.md` - Guía del Service Layer
- `/docs/` - Documentación técnica variada

---

## Changelog

> Actualizar este archivo cuando se establezcan nuevos patrones, se resuelvan issues de arquitectura, o cambien convenciones importantes.

### 2026-01-08
- ✅ Creación inicial del archivo
- ✅ Documentado Service Layer (`apps/validador/services/`)
- ✅ Documentados patrones: ServiceResult, Zustand, React Query
- ✅ Issues de deuda técnica creados: #16, #17, #18
- ✅ Sidebar colapsable implementado (#15)
- ✅ Separación "Mis Cierres" vs "Cierres del Equipo"
