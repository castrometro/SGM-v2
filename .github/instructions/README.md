# Instructions - SGM v2

Instrucciones específicas por tecnología/framework para el desarrollo en SGM v2.

## 📚 Instrucciones Disponibles

### [React Instructions](./react-instructions.md)
Estándares y best practices para desarrollo con React.

**Incluye:**
- Patrones de componentes
- State management (Zustand + React Query)
- Performance optimization
- Code splitting y lazy loading
- Error boundaries
- Testing patterns
- Accessibility guidelines

**Aplica a:** `frontend/**/*.jsx`, `frontend/**/*.js`, `frontend/**/*.css`

---

### [Audit & Compliance Instructions](./audit-compliance-instructions.md)
Estándares de auditoría, trazabilidad y cumplimiento normativo.

**Incluye:**
- Marco normativo (ISO 27001, ISO 27701, Ley 21.719)
- Arquitectura de auditoría (Celery Results + Limpieza)
- Política de retención de datos
- Queries de auditoría para reportes
- Checklist de cumplimiento
- Roadmap de implementación

**Aplica a:** `backend/**/*.py` (especialmente tareas Celery)

---

### [Documentation Guide](./DOCUMENTATION_GUIDE.md)
Guía sobre dónde y cómo documentar en el proyecto.

**Incluye:**
- Estructura de documentación
- `.github/` vs `docs/`
- Backend vs Frontend docs
- Ejemplos y anti-patrones

---

## 🎯 Propósito de esta Carpeta

Esta carpeta contiene **instrucciones específicas por tecnología** que complementan las instrucciones generales del proyecto en `copilot-instructions.md`.

### Diferencia con copilot-instructions.md

| Archivo | Propósito |
|---------|-----------|
| `../copilot-instructions.md` | Instrucciones **generales** del proyecto (stack, estructura, convenciones) |
| `instructions/react-instructions.md` | Instrucciones **específicas de React** (hooks, patterns, optimization) |
| `instructions/audit-compliance-instructions.md` | Instrucciones de **auditoría y cumplimiento** (ISO, Ley 21.719) |
| `instructions/django-instructions.md` | *(Futuro)* Instrucciones específicas de Django |
| `instructions/celery-instructions.md` | *(Futuro)* Instrucciones específicas de Celery |

---

## 📝 Agregar Nuevas Instrucciones

### Template para nueva instrucción:

```markdown
---
description: 'Breve descripción'
applyTo: 'patron/de/archivos/**/*'
---

# Tecnología Instructions - SGM v2

## Project Context
- Stack y versiones
- Librerías principales

## Development Standards
- Patrones específicos
- Best practices
- Ejemplos

## Common Patterns
- Casos de uso frecuentes
- Code snippets

## Things to Avoid
- Anti-patrones
- Errores comunes
```

### Pasos:

1. Crear archivo `{tecnologia}-instructions.md`
2. Agregar entrada en este README
3. Referenciar desde `copilot-instructions.md` si es necesario
4. Actualizar `docs/README.md` si documenta implementaciones

---

## 🔗 Referencias

- **[Instrucciones Generales](../copilot-instructions.md)** - Convenciones del proyecto
- **[Documentación Técnica](../../docs/)** - Implementaciones y arquitectura
- **[README Principal](../../README.md)** - Overview del proyecto

---

**Última actualización:** 2026-01-12
