# Documentación Frontend - SGM v2

Documentación técnica sobre implementaciones, patrones y optimizaciones del frontend React.

## 📚 Contenido

### Manejo de Errores

- **[Error Boundary](./ERROR_BOUNDARY.md)** - Implementación de Error Boundaries
  - Componente ErrorBoundary
  - Integración en App.jsx
  - Testing y verificación
  - Integración con servicios de logging

### Optimización de Performance

- **[Code Splitting](./CODE_SPLITTING.md)** - Implementación de code splitting con React.lazy
  - Lazy loading de rutas
  - Suspense fallbacks
  - Análisis de bundle size
  - Métricas de performance

## 🏗️ Arquitectura

### Stack Tecnológico
- **React 18** + Vite
- **Zustand** - Estado global
- **TanStack Query** - Server state
- **Tailwind CSS** - Estilos
- **React Router v6** - Routing

### Estructura de Features

```
frontend/src/
├── components/       # Componentes reutilizables
├── features/         # Módulos por funcionalidad
│   ├── admin/
│   ├── auth/
│   ├── clientes/
│   ├── dashboard/
│   ├── incidencias/
│   ├── supervisor/
│   └── validador/
├── hooks/           # Custom hooks
├── stores/          # Zustand stores
└── utils/           # Utilidades
```

## 🎯 Implementaciones

### ✅ Completadas
- [x] Error Boundary con UI personalizada
- [x] Code splitting con React.lazy
- [x] Rutas protegidas por rol
- [x] Estado global con Zustand
- [x] Data fetching con React Query

### 🚧 Pendientes
- [ ] Testing (Vitest + Testing Library)
- [ ] Accessibility audit
- [ ] Performance monitoring
- [ ] Storybook para componentes

## 🔗 Referencias Relacionadas

- [React Instructions](../../.github/react-instructions.md) - Estándares y best practices
- [Copilot Instructions](../../.github/copilot-instructions.md) - Convenciones generales
- [Backend Documentation](../backend/) - Documentación del backend

## 📊 Métricas de Performance

| Métrica | Target | Actual |
|---------|--------|--------|
| Bundle inicial | <250 KB | ~200 KB ✅ |
| Time to Interactive | <2.5s | ~1.5s ✅ |
| Lighthouse Score | >85 | Pendiente |

---

**Última actualización:** 2026-01-08
