# 🔒 Security Review: Archivos del Analista

**Fecha:** 24 Enero 2026  
**Feature:** Procesamiento de Ingresos, Finiquitos, Ausentismos  
**Reviewer:** @se-security

---

## 🎯 Estado: ⛔ **REQUIERE CORRECCIONES ANTES DE PRODUCCIÓN**

### Resumen de Hallazgos

| Severidad | Cantidad | Estado |
|-----------|----------|--------|
| 🔴 Crítica | 2 | ⛔ Bloquean producción |
| 🟠 Alta | 2 | ⚠️ Prioridad 1 |
| 🟡 Media | 2 | 📋 Backlog |

---

## 🔴 Vulnerabilidades Críticas

### C-01: Path Traversal - Sin Validación de Ruta

**Ubicación:** `procesar_analista.py` líneas 394, 455, 520

**Código vulnerable:**
```python
if archivo.extension == '.csv':
    df = pd.read_csv(archivo.archivo.path)  # ❌ Sin validación
else:
    df = pd.read_excel(archivo.archivo.path)  # ❌ Sin validación
```

**Comparación con procesar_erp.py:**
```python
# ✅ procesar_erp.py tiene validación
if not _validar_ruta_archivo(archivo.archivo.path):
    raise ValueError("Ruta de archivo no válida")
```

**Fix requerido:**
```python
from apps.validador.tasks.procesar_erp import _validar_ruta_archivo

# Al inicio de cada función
if not _validar_ruta_archivo(archivo.archivo.path):
    raise ValueError("Ruta de archivo no válida o fuera del directorio permitido")
```

**CVSS:** 7.5 (Alto)  
**CWE:** CWE-22 (Path Traversal)

---

### C-02: Exposición de PII en Logs

**Ubicación:** `procesar_analista.py` (logs de warning/error)

**Problema:** RUTs pueden aparecer en mensajes de error sin enmascarar

**Comparación con procesar_erp.py:**
```python
# ✅ procesar_erp.py tiene _mask_rut()
def _mask_rut(rut: str) -> str:
    if not rut or len(rut) < 5:
        return "****"
    return f"****{rut[-4:]}"
```

**Fix requerido:** Importar y usar `_mask_rut()` en logs de error

**CVSS:** 6.5 (Medio-Alto)  
**CWE:** CWE-532 (Information Exposure Through Log Files)

---

## 🟠 Vulnerabilidades Altas

### A-01: Validación Insuficiente de RUT

**Problema:** Solo normaliza formato, no valida dígito verificador

**Riesgo:** Acepta RUTs inválidos como "00000000-0"

### A-02: Sin Validación de Rango de Fechas

**Problema:** Acepta fechas absurdas (año 1900, 2100)

**Riesgo:** Datos incorrectos, posible DoS con fechas extremas

---

## 🟡 Vulnerabilidades Medias

### M-01: Sin Transacciones Atómicas

**Problema:** Si falla a mitad del procesamiento, queda estado inconsistente

**Fix:** Envolver en `transaction.atomic()`

### M-02: Sin Límite de Tamaño de Archivo

**Problema:** Puede cargar archivos de 1GB+ en memoria

---

## ✅ Aspectos Positivos

1. **Sanitización JSON** - `_sanitizar_datos_raw()` previene NaN/Inf
2. **Uso de ORM** - Previene SQL injection
3. **Bulk create** - Operación más segura que creates individuales

---

## 📋 Plan de Remediación

### Fase 1 - BLOQUEANTE (2-3 horas)

| ID | Vulnerabilidad | Esfuerzo |
|----|---------------|----------|
| C-01 | Path Traversal | 30 min |
| C-02 | PII en Logs | 30 min |
| M-01 | Transacciones | 1h |

### Fase 2 - Alta Prioridad (1 semana)

| ID | Vulnerabilidad | Esfuerzo |
|----|---------------|----------|
| A-01 | Validación RUT | 3h |
| A-02 | Validación Fechas | 2h |
| M-02 | Límite tamaño | 1h |

---

## 🎯 Decisión

**⛔ NO DESPLEGAR A PRODUCCIÓN** sin resolver C-01 y C-02.

Estas vulnerabilidades existen y fueron corregidas en `procesar_erp.py`, deben aplicarse los mismos fixes a `procesar_analista.py`.

---

## Checklist Pre-Producción

- [ ] Agregar `_validar_ruta_archivo()` antes de pd.read_excel/csv
- [ ] Agregar masking de PII en logs de error
- [ ] Envolver procesamiento en `transaction.atomic()`
- [ ] Re-revisar código post-fix

---

**Próxima revisión:** Post-implementación de fixes
