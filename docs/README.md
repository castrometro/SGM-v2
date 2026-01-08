# Documentación Técnica - SGM v2

Documentación completa sobre arquitectura, patrones de diseño e implementaciones del proyecto SGM v2.

## 📂 Estructura de Documentación

### [Backend](./backend/)
Patrones, arquitectura y guías de implementación del backend Django.

- **[Service Layer](./backend/SERVICE_LAYER.md)** - Patrón de capa de servicios
  - ServiceResult pattern
  - Lógica de negocio centralizada
  - Ejemplos y best practices

### [Frontend](./frontend/)
Implementaciones, patrones y optimizaciones del frontend React.

- **[Error Boundary](./frontend/ERROR_BOUNDARY.md)** - Manejo robusto de errores
- **[Code Splitting](./frontend/CODE_SPLITTING.md)** - Optimización de carga

## 🏗️ Arquitectura General

```
SGM-v2/
├── backend/          # Django + DRF + Celery
│   ├── apps/
│   │   ├── core/         # Usuarios, Clientes
│   │   ├── validador/    # Cierres, Archivos, Incidencias
│   │   └── reporteria/   # Reportes
│   └── config/           # Settings Django
│
├── frontend/         # React + Vite
│   └── src/
│       ├── features/     # Módulos por funcionalidad
│       ├── components/   # Componentes reutilizables
│       ├── stores/       # Zustand stores
│       └── hooks/        # Custom hooks
│
└── docs/            # 📚 Esta documentación
```

## 📋 Guías de Referencia

### Para la IA (GitHub Copilot)
- [Copilot Instructions](../.github/copilot-instructions.md) - Instrucciones generales
- [React Instructions](../.github/react-instructions.md) - Estándares React

### Para Desarrolladores
- [Backend Docs](./backend/) - Documentación backend
- [Frontend Docs](./frontend/) - Documentación frontend

## 🎯 Patrones Implementados

### Backend
- ✅ Service Layer con ServiceResult
- ✅ Permisos por rol (analista, supervisor, senior, gerente)
- ✅ Tareas asíncronas con Celery
- ✅ API REST con DRF

### Frontend
- ✅ Error Boundaries
- ✅ Code splitting con React.lazy
- ✅ Estado global con Zustand
- ✅ Server state con React Query
- ✅ Rutas protegidas por rol

## 🚀 Próximas Implementaciones

### Alta Prioridad
- [ ] Testing (backend + frontend)
- [ ] Accessibility audit
- [ ] Performance monitoring

### Media Prioridad
- [ ] Storybook para componentes
- [ ] E2E testing
- [ ] CI/CD pipeline

### Baja Prioridad
- [ ] Migración a TypeScript (evaluar)
- [ ] Internacionalización (i18n)

## 📖 Convenciones

### Commits
```
feat: Nueva funcionalidad
fix: Corrección de bug
refactor: Refactorización
docs: Documentación
style: Formato/estilos
test: Tests
```

### Branches
- `main` - Rama principal de desarrollo
- `feature/nombre` - Nuevas funcionalidades
- `fix/nombre` - Correcciones
- `hotfix/nombre` - Correcciones urgentes

## 🔗 Enlaces Útiles

- [React Documentation](https://react.dev)
- [Django REST Framework](https://www.django-rest-framework.org)
- [TanStack Query](https://tanstack.com/query)
- [Tailwind CSS](https://tailwindcss.com)

---

**Proyecto:** Sistema de Gestión de Nómina (SGM)  
**Versión:** 2.0  
**Última actualización:** 2026-01-08
