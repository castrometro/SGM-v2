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
└── docs/                        # Documentación
    ├── API.md
    ├── DEPLOYMENT.md
    └── ARCHITECTURE.md
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
Motor de validación de nómina:
- **Cierres**: Proceso mensual de cierre
- **Archivos**: Libro de remuneraciones, movimientos, novedades
- **Validaciones**: Reglas de validación y discrepancias
- **Incidencias**: Gestión de problemas detectados

### 3. Reportería (`apps.reporteria`)
Generación de informes y dashboards:
- **Dashboards**: Visualización de KPIs
- **Informes**: Generación de reportes
- **Exportaciones**: Excel, PDF

## 📝 Licencia

Proyecto privado - BDO Chile
