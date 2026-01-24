# 📋 Architecture Review: Archivos del Analista

**Fecha:** 24 Enero 2026  
**Feature:** Procesamiento de Ingresos, Finiquitos, Ausentismos  
**Reviewer:** @se-architect

---

## 🎯 Estado: ⚠️ **APROBADO CON DEUDA TÉCNICA**

### Calificación: **72/100** (C+)

| Aspecto | Rating | Estado |
|---------|--------|--------|
| Seguridad | 85/100 | ✅ |
| Consistencia Arquitectónica | 60/100 | ⚠️ |
| Rendimiento | 80/100 | ✅ |
| Mantenibilidad | 65/100 | ⚠️ |
| Normalización | 70/100 | ⚠️ |

---

## ✅ Aspectos Positivos

1. **Bulk Operations** - Usa `bulk_create` correctamente (10-50x más rápido)
2. **Modelo bien diseñado** - Consistente con MovimientoMes, reutiliza TIPO_CHOICES
3. **Sanitización JSON** - `_sanitizar_datos_raw()` previene errores NaN/Inf
4. **Admin optimizado** - `list_select_related` evita N+1 queries

---

## 🔴 Deudas Técnicas Identificadas

### DT-001: Duplicación Masiva de Código (CRÍTICA)

**Problema:** 80% del código repetido en `_procesar_ingresos`, `_procesar_finiquitos`, `_procesar_asistencias`

**Impacto:**
- Bugs se multiplican (fix en una función no se propaga)
- 100+ líneas duplicadas
- Cambios requieren modificar 3 lugares

**Solución:** Extraer función genérica `_procesar_archivo_movimientos(archivo, tipo_origen, config)`

### DT-002: Normalización de RUT Inconsistente (ALTA)

**Problema:** Hack con `ERPStrategy.__new__()` para usar método de normalización

```python
# ❌ MAL: Instancia clase abstracta incorrectamente
strategy = ERPStrategy.__new__(ERPStrategy)
strategy.config = {}
rut = strategy.normalizar_rut(rut_raw)
```

**Solución:** Extraer a `apps/validador/utils/normalizacion.py`

### DT-003: Parseo de Fechas Duplicado (MEDIA)

**Problema:** `_parse_fecha_analista()` duplica `ERPStrategy.normalizar_fecha()`

### DT-004: Falta Validación Path Traversal (CRÍTICA)

**Problema:** procesar_erp.py tiene `_validar_ruta_archivo()`, procesar_analista.py NO

### DT-005: Sin Masking de PII en Logs (ALTA)

**Problema:** procesar_erp.py tiene `_mask_rut()`, procesar_analista.py NO

---

## 📊 Comparación con Patrón MovimientoMes

| Aspecto | MovimientoMes (ERP) | MovimientoAnalista | Consistencia |
|---------|---------------------|-------------------|--------------|
| Bulk Create | ✅ | ✅ | ✅ |
| Normalización RUT | ✅ Via ERPFactory | ⚠️ Hack `__new__` | ❌ |
| Parseo Fechas | ✅ Via strategy | ⚠️ Función custom | ❌ |
| Sanitización JSON | ✅ | ✅ | ✅ |
| Validación Path | ✅ | ❌ | ❌ |
| Masking PII | ✅ | ❌ | ❌ |

**Consistencia Global:** 50%

---

## 🎯 Recomendaciones Priorizadas

### Críticas (Esta semana)
1. **REC-002:** Agregar validación de seguridad (2h)
2. **REC-003:** Extraer helpers a `utils/normalizacion.py` (3h)
3. **REC-005:** Agregar masking de PII (1h)

### Altas (Este mes)
4. **REC-001:** Refactorizar a función genérica (4h)
5. **REC-004:** Agregar validaciones de negocio (6h)

### Medias (Backlog)
6. Mejorar mapeo de columnas con regex
7. Tests unitarios para helpers
8. Documentar formatos esperados

---

## 📝 ADR Propuesto

**ADR-007: Estrategia de Normalización Compartida**

- Crear `apps/validador/utils/normalizacion.py` con funciones puras
- Reutilizar entre ERP y Analista
- Facilitar testing y mantenimiento

---

**Próxima revisión:** Post-refactor
