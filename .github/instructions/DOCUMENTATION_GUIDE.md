# Guía de Documentación - SGM v2

## 📋 Propósito de este archivo

Este documento explica **dónde colocar la documentación** en el proyecto SGM-v2.

## 🗂️ Estructura y Propósito

### 1. `.github/` - Instrucciones para IA y Colaboradores

**Propósito:** Archivos que le dicen a GitHub Copilot y otros desarrolladores **cómo trabajar** en el proyecto.

```
.github/
├── copilot-instructions.md     # Convenciones generales del proyecto
├── react-instructions.md       # Estándares y patterns de React
├── DOCUMENTATION_GUIDE.md      # Este archivo (meta-documentación)
└── ISSUE_TEMPLATE/             # Templates para issues
```

**¿Qué va aquí?**
- ✅ Convenciones de código
- ✅ Estándares y best practices
- ✅ Guías de estilo
- ✅ Instrucciones para la IA
- ❌ NO documentación de implementaciones

**Características:**
- Son **prescriptivos** ("debes hacer X")
- Definen el **"cómo"** trabajar
- Usados por la IA durante desarrollo

---

### 2. `docs/` - Documentación Técnica

**Propósito:** Documentación sobre **qué se ha implementado** y **por qué**.

```
docs/
├── README.md                   # Índice general
│
├── backend/
│   ├── README.md               # Índice backend
│   └── SERVICE_LAYER.md        # Patrón Service Layer
│
└── frontend/
    ├── README.md               # Índice frontend
    ├── ERROR_BOUNDARY.md       # Implementación Error Boundary
    └── CODE_SPLITTING.md       # Implementación Code Splitting
```

**¿Qué va aquí?**
- ✅ Arquitectura y patrones implementados
- ✅ Guías de implementación específicas
- ✅ Decisiones técnicas y justificaciones
- ✅ Tutoriales de verificación y testing
- ❌ NO estándares generales (eso va en .github/)

**Características:**
- Son **descriptivos** ("así funciona X")
- Documentan el **"qué"** y el **"por qué"**
- Referencia para entender código existente

---

### 3. `README.md` (raíz) - Overview del Proyecto

**Propósito:** Punto de entrada principal, vista general del proyecto.

**¿Qué va aquí?**
- ✅ Descripción del proyecto
- ✅ Quick start / setup inicial
- ✅ Stack tecnológico
- ✅ Enlaces a documentación detallada
- ❌ NO detalles técnicos extensos

---

## 🎯 Reglas de Oro

### Regla 1: Separar "Cómo" de "Qué"

| Pregunta | Archivo | Ubicación |
|----------|---------|-----------|
| ¿Cómo debo escribir componentes React? | `react-instructions.md` | `.github/` |
| ¿Qué es el Error Boundary que implementamos? | `ERROR_BOUNDARY.md` | `docs/frontend/` |
| ¿Cómo debo estructurar servicios? | `copilot-instructions.md` | `.github/` |
| ¿Cómo funciona el Service Layer? | `SERVICE_LAYER.md` | `docs/backend/` |

### Regla 2: Backend vs Frontend

Separar documentación por capa:
- `docs/backend/` → Todo relacionado con Django/DRF/Celery
- `docs/frontend/` → Todo relacionado con React/Vite/Tailwind

### Regla 3: README como Índice

Cada carpeta de docs debe tener un `README.md` que sirva como índice:
- `docs/README.md` → Índice general
- `docs/backend/README.md` → Índice backend
- `docs/frontend/README.md` → Índice frontend

---

## 📝 Ejemplos de Clasificación

### ✅ Ejemplo 1: Nuevo Feature - Lazy Loading

**Archivos creados:**

1. `.github/react-instructions.md` (actualizar sección)
   ```markdown
   ### Code Splitting
   - Usar React.lazy para rutas
   - Implementar Suspense con fallback
   ```

2. `docs/frontend/CODE_SPLITTING.md` (nuevo)
   ```markdown
   # Code Splitting - Implementación
   
   ## ¿Qué se implementó?
   Se agregó lazy loading con React.lazy...
   
   ## ¿Cómo probarlo?
   1. Abre DevTools...
   ```

### ✅ Ejemplo 2: Nuevo Pattern Backend - Repository Pattern

**Archivos a crear:**

1. `.github/copilot-instructions.md` (actualizar)
   ```markdown
   ### Repository Pattern
   - Usar repositorios para acceso a datos
   - Naming: `{Model}Repository`
   ```

2. `docs/backend/REPOSITORY_PATTERN.md` (nuevo)
   ```markdown
   # Repository Pattern - Implementación
   
   ## Contexto
   Implementamos el patrón Repository para...
   ```

---

## 🔄 Flujo de Creación de Docs

```
┌─────────────────────┐
│  Nueva feature o    │
│  pattern            │
└──────────┬──────────┘
           │
           ▼
    ┌──────────────┐     NO
    │ ¿Es un       │────────────┐
    │ estándar/    │            │
    │ convenció?   │            │
    └──────────────┘            │
           │ SÍ                 │
           ▼                    ▼
    ┌──────────────┐     ┌──────────────┐
    │ Actualizar   │     │ Crear doc    │
    │ .github/     │     │ en docs/     │
    │ instructions │     │ backend o    │
    │              │     │ frontend/    │
    └──────────────┘     └──────────────┘
           │                    │
           └────────┬───────────┘
                    ▼
            ┌──────────────┐
            │ Actualizar   │
            │ README.md    │
            │ principal    │
            └──────────────┘
```

---

## 🚫 Anti-Patrones (Qué NO hacer)

### ❌ NO: Documentación suelta en carpetas de código

```
❌ BAD:
frontend/
├── src/
│   └── components/
│       └── ErrorBoundary/
│           ├── ErrorBoundary.jsx
│           └── README.md          # ❌ No aquí
```

### ❌ NO: Mezclar estándares con implementaciones

```
❌ BAD:
.github/
├── copilot-instructions.md
└── ERROR_BOUNDARY_IMPLEMENTATION.md  # ❌ Esto va en docs/
```

### ❌ NO: Documentación sin índice

```
❌ BAD:
docs/
├── archivo1.md
├── archivo2.md
├── archivo3.md
└── (sin README.md)                   # ❌ Falta índice
```

---

## ✅ Checklist para Nueva Documentación

Antes de crear un nuevo documento, pregúntate:

- [ ] ¿Es un estándar/convención? → `.github/`
- [ ] ¿Es una implementación específica? → `docs/`
- [ ] ¿Es backend o frontend? → `docs/backend/` o `docs/frontend/`
- [ ] ¿Actualicé el README correspondiente?
- [ ] ¿El nombre del archivo es descriptivo?
- [ ] ¿Incluye fecha de última actualización?

---

## 📚 Referencias

- **Documentación existente:** Ver [`docs/README.md`](../docs/README.md)
- **Convenciones generales:** Ver [`copilot-instructions.md`](./copilot-instructions.md)
- **Estándares React:** Ver [`react-instructions.md`](./react-instructions.md)

---

**Última actualización:** 2026-01-08  
**Mantenido por:** Equipo de desarrollo SGM-v2
