# SGM v2 - Sistema de Gestión de Nómina

Sistema integral para la gestión y validación de procesos de nómina.

## 🏗️ Arquitectura

```
┌─────────────────────────────────────────────────────────────────┐
│                        FRONTEND (React + Vite)                   │
│                         Puerto: 5173                             │
├─────────────────────────────────────────────────────────────────┤
│                        NGINX (Reverse Proxy)                     │
│                         Puerto: 80/443                           │
├─────────────────────────────────────────────────────────────────┤
│                     BACKEND (Django REST Framework)              │
│                         Puerto: 8000                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐   │
│  │     CORE     │  │  VALIDADOR   │  │     REPORTERIA       │   │
│  │  - Usuarios  │  │  - Cierres   │  │  - Dashboards        │   │
│  │  - Clientes  │  │  - Archivos  │  │  - Informes          │   │
│  │  - Servicios │  │  - Validac.  │  │  - Exportaciones     │   │
│  └──────────────┘  └──────────────┘  └──────────────────────┘   │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐                             │
│  │  PostgreSQL  │  │    Redis     │  ← Celery (tareas async)    │
│  │  Puerto:5432 │  │  Puerto:6379 │                             │
│  └──────────────┘  └──────────────┘                             │
└─────────────────────────────────────────────────────────────────┘
```

## 📁 Estructura del Proyecto

```
SGM-v2/
├── docker-compose.yml          # Orquestación de servicios
├── .env.example                 # Variables de entorno de ejemplo
│
├── backend/                     # Django REST Framework
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── manage.py
│   ├── config/                  # Configuración del proyecto Django
│   │   ├── settings/
│   │   │   ├── base.py
│   │   │   ├── development.py
│   │   │   └── production.py
│   │   ├── urls.py
│   │   └── wsgi.py
│   │
│   ├── apps/
│   │   ├── core/                # App: Usuarios, Clientes, Servicios
│   │   │   ├── models/
│   │   │   ├── serializers/
│   │   │   ├── views/
│   │   │   ├── services/
│   │   │   └── urls.py
│   │   │
│   │   ├── validador/           # App: Validación de Nómina
│   │   │   ├── models/
│   │   │   ├── serializers/
│   │   │   ├── views/
│   │   │   ├── services/
│   │   │   ├── tasks/           # Tareas Celery
│   │   │   └── urls.py
│   │   │
│   │   └── reporteria/          # App: Reportes y Dashboards
│   │       ├── models/
│   │       ├── serializers/
│   │       ├── views/
│   │       ├── services/
│   │       └── urls.py
│   │
│   └── shared/                  # Utilidades compartidas
│       ├── permissions.py
│       ├── pagination.py
│       └── exceptions.py
│
├── frontend/                    # React + Vite + TailwindCSS
│   ├── Dockerfile
│   ├── package.json
│   ├── vite.config.js
│   ├── tailwind.config.js
│   │
│   ├── public/
│   │
│   └── src/
│       ├── main.jsx
│       ├── App.jsx
│       │
│       ├── api/                 # Configuración de API (axios)
│       │
│       ├── components/          # Componentes reutilizables (UI)
│       │   ├── ui/              # Botones, Inputs, Cards, etc.
│       │   └── layout/          # Header, Sidebar, Footer
│       │
│       ├── features/            # Feature Folder Pattern
│       │   ├── auth/
│       │   │   ├── components/
│       │   │   ├── hooks/
│       │   │   ├── services/
│       │   │   └── pages/
│       │   │
│       │   ├── clientes/
│       │   │   ├── components/
│       │   │   ├── hooks/
│       │   │   ├── services/
│       │   │   └── pages/
│       │   │
│       │   ├── validador/
│       │   │   ├── components/
│       │   │   ├── hooks/
│       │   │   ├── services/
│       │   │   └── pages/
│       │   │
│       │   └── reporteria/
│       │       ├── components/
│       │       ├── hooks/
│       │       ├── services/
│       │       └── pages/
│       │
│       ├── hooks/               # Hooks globales
│       ├── contexts/            # Contextos React (Auth, Theme)
│       ├── utils/               # Utilidades
│       └── styles/              # Estilos globales
│
├── docs/                        # 📚 Documentación técnica
│   ├── README.md                # Índice de documentación
│   ├── backend/                 # Docs del backend
│   │   ├── README.md
│   │   └── SERVICE_LAYER.md     # Patrón Service Layer
│   └── frontend/                # Docs del frontend
│       ├── README.md
│       ├── ERROR_BOUNDARY.md    # Manejo de errores
│       └── CODE_SPLITTING.md    # Optimización de carga
│
└── .github/                     # Configuración de GitHub
    ├── copilot-instructions.md  # Instrucciones para Copilot
    └── react-instructions.md    # Estándares React
```

## 🚀 Quick Start

```bash
# 1. Clonar repositorio
git clone https://github.com/castrometro/SGM-v2.git
cd SGM-v2

# 2. Copiar variables de entorno
cp .env.example .env

# 3. Levantar servicios
docker-compose up -d

# 4. Ejecutar migraciones
docker-compose exec backend python manage.py migrate

# 5. Crear superusuario
docker-compose exec backend python manage.py createsuperuser
```

## 🛠️ Stack Tecnológico

| Componente | Tecnología | Versión |
|------------|------------|---------|
| Frontend | React + Vite | 18.x |
| Estilos | TailwindCSS | 3.x |
| Backend | Django REST Framework | 5.x |
| Base de datos | PostgreSQL | 16 |
| Cache/Queue | Redis | 7.x |
| Task Queue | Celery | 5.x |
| Contenedores | Docker + Docker Compose | Latest |

## 📚 Apps Django

### 1. Core (`apps.core`)
Gestión de entidades base del sistema:
- **Usuarios**: Analistas, Seniors, Supervisores, Gerentes
- **Clientes**: Empresas que contratan servicios
- **Servicios**: Catálogo de servicios ofrecidos
- **Asignaciones**: Relación usuario-cliente

### 2. Validador (`apps.validador`)
Motor de validación de nómina con flujo de 9 fases:

#### Flujo del Validador

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           FLUJO DEL VALIDADOR                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────┐     ┌───────────────────┐     ┌──────────────────┐        │
│  │ 1. CARGA DE  │────▶│ 2. CLASIFICACIÓN  │────▶│ 3. MAPEO ITEMS   │        │
│  │   ARCHIVOS   │     │    CONCEPTOS      │     │   NOVEDADES      │        │
│  └──────────────┘     └───────────────────┘     └──────────────────┘        │
│        │                    (si nuevos)               (si nuevos)            │
│        │                                                    │                │
│        ▼                                                    ▼                │
│  ┌──────────────┐     ┌───────────────────┐     ┌──────────────────┐        │
│  │  ERP Files:  │     │  Headers Libro ──▶│     │ Novedades items  │        │
│  │  - Libro     │     │  Categorías:      │     │ ──▶ Conceptos   │        │
│  │  - Movim.    │     │  • Hab. Imponib.  │     │     del ERP      │        │
│  │              │     │  • Hab. No Imp.   │     │                  │        │
│  │  Analista:   │     │  • Desc. Legales  │     │  (Mapeo 1:1)     │        │
│  │  - Novedades │     │  • Otros Desc.    │     │                  │        │
│  │  - Asistenc. │     │  • Aportes Pat.   │     │  Se guarda por   │        │
│  │  - Finiquitos│     │  • Informativos   │     │  cliente         │        │
│  │  - Ingresos  │     │                   │     │                  │        │
│  └──────────────┘     └───────────────────┘     └──────────────────┘        │
│                                                          │                   │
│                                                          ▼                   │
│  ┌──────────────────────────────────────────────────────────────────┐       │
│  │                      4. COMPARACIÓN                                │       │
│  │  ┌────────────────────────┐    ┌────────────────────────┐        │       │
│  │  │   Libro vs Novedades   │    │  Movimientos vs Anal.  │        │       │
│  │  │   (items que se        │    │  (Altas, Bajas,        │        │       │
│  │  │    comparan)           │    │   Licencias, Vac.)     │        │       │
│  │  └────────────────────────┘    └────────────────────────┘        │       │
│  │                                                                    │       │
│  │  EXCLUIDOS: Informativos, Descuentos Legales                      │       │
│  └──────────────────────────────────────────────────────────────────┘       │
│                           │                                                  │
│                           ▼                                                  │
│           ┌───────────────────────────────┐                                 │
│           │     ¿Discrepancias = 0?       │                                 │
│           └───────────────────────────────┘                                 │
│                    │              │                                          │
│                   NO             SÍ                                          │
│                    │              │                                          │
│                    ▼              ▼                                          │
│  ┌──────────────────────┐  ┌──────────────────────┐                         │
│  │ 5. CON DISCREPANCIAS │  │ 6. CONSOLIDADO       │                         │
│  │    Usuario corrige   │  │    (Solo datos ERP)  │                         │
│  │    re-subiendo       │  └──────────────────────┘                         │
│  │    archivos          │           │                                        │
│  └──────────────────────┘           │                                        │
│           │                         │                                        │
│           └────────────┬────────────┘                                        │
│                        │                                                     │
│                        ▼                                                     │
│  ┌──────────────────────────────────────────────────────────────────┐       │
│  │             7. DETECCIÓN DE INCIDENCIAS                           │       │
│  │                                                                    │       │
│  │   Compara totales por concepto con mes anterior                   │       │
│  │   Si variación > 30% → Genera INCIDENCIA                          │       │
│  │                                                                    │       │
│  │   EXCLUIDOS: Informativos, Descuentos Legales                     │       │
│  │   PRIMER CIERRE: Salta esta fase (sin mes anterior)               │       │
│  └──────────────────────────────────────────────────────────────────┘       │
│                        │                                                     │
│                        ▼                                                     │
│  ┌──────────────────────────────────────────────────────────────────┐       │
│  │          8. REVISIÓN DE INCIDENCIAS (FORO)                        │       │
│  │                                                                    │       │
│  │   Analista justifica ◀──────────▶ Supervisor revisa               │       │
│  │   cada incidencia                  y aprueba/rechaza              │       │
│  │                                                                    │       │
│  │   RECHAZO: El cierre vuelve a fase 1 (Carga de Archivos)          │       │
│  │            El usuario debe corregir y re-subir TODO               │       │
│  └──────────────────────────────────────────────────────────────────┘       │
│                        │                                                     │
│                        ▼                                                     │
│           ┌───────────────────────────────┐                                 │
│           │   ¿Todas aprobadas?           │                                 │
│           │   ¿Incidencias = 0?           │                                 │
│           └───────────────────────────────┘                                 │
│                    │              │                                          │
│                   NO             SÍ                                          │
│                    │              │                                          │
│                    │              ▼                                          │
│                    │     ┌──────────────────────┐                           │
│                    │     │ 9. FINALIZADO        │                           │
│                    └─────│    Cierre completo   │                           │
│                          └──────────────────────┘                           │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### Modelos Principales del Validador
- **Cierre**: Contenedor del proceso mensual
- **ArchivoERP / ArchivoAnalista**: Archivos subidos
- **CategoriaConcepto**: Categorías fijas del sistema
- **ConceptoCliente**: Headers clasificados por cliente
- **MapeoItemNovedades**: Mapeo 1:1 novedades → conceptos
- **Discrepancia**: Diferencias encontradas
- **Incidencia**: Variaciones >30% con mes anterior
- **ComentarioIncidencia**: Foro de discusión

### 3. Reportería (`apps.reporteria`)
Generación de informes y dashboards:
- **Dashboards**: Visualización de KPIs
- **Informes**: Generación de reportes
- **Exportaciones**: Excel, PDF

## 📝 Documentación

- **[Documentación Técnica](./docs/)** - Arquitectura, patrones y guías
  - [Backend](./docs/backend/) - Service Layer, patterns
  - [Frontend](./docs/frontend/) - Error Boundary, Code Splitting
- **[Instrucciones para Copilot](./.github/copilot-instructions.md)** - Convenciones del proyecto
- **[Estándares React](./.github/react-instructions.md)** - Best practices frontend

## 📝 Licencia

Proyecto privado - BDO Chile
