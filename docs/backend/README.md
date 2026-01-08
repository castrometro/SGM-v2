# Documentación Backend - SGM v2

Documentación técnica sobre patrones, arquitectura y guías de implementación del backend.

## 📚 Contenido

### Patrones de Arquitectura

- **[Service Layer](./SERVICE_LAYER.md)** - Guía completa sobre el patrón Service Layer
  - ServiceResult pattern
  - Estructura de servicios
  - Ejemplos de uso en views
  - Best practices

## 📁 Estructura de Servicios

```
backend/apps/validador/services/
├── __init__.py
├── base.py              # BaseService, ServiceResult
├── cierre_service.py
├── archivo_service.py
├── incidencia_service.py
└── equipo_service.py
```

## 🔗 Referencias Relacionadas

- [Copilot Instructions](../../.github/copilot-instructions.md) - Convenciones generales
- [Frontend Architecture](../frontend/) - Documentación del frontend

---

**Última actualización:** 2026-01-08
