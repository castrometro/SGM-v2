# 🔒 Security Review: Movimientos del Mes - Talana

**Fecha:** 24 Enero 2026  
**Feature:** Procesamiento de archivo Movimientos del Mes para ERP Talana  
**Reviewer:** @se-security  
**Última actualización:** 24 Enero 2026 - Post-fix

---

## 🎯 Estado: ✅ **APROBADO PARA PRODUCCIÓN**

> Los issues críticos C-01 y C-02 fueron resueltos. H-02 queda como deuda técnica.

### Resumen de Hallazgos

| Severidad | Cantidad | Estado |
|-----------|----------|--------|
| 🔴 Crítica | 2 | ✅ Resueltos |
| 🟠 Alta | 3 | ⚠️ Prioridad 1 (H-02 deuda técnica) |
| 🟡 Media | 2 | 📋 Backlog |

---

## 🔴 Vulnerabilidades Críticas

### C-01: Path Traversal - Lectura de archivos sin validación ✅ RESUELTO

**Ubicación:** `procesar_erp.py:200`, `talana.py` (pd.read_excel)

**Riesgo:** Un atacante podría manipular la ruta para leer archivos arbitrarios del sistema.

**Solución implementada:**
```python
# procesar_erp.py - líneas 14-30
def _validar_ruta_archivo(file_path: str) -> bool:
    """
    Valida que la ruta del archivo esté dentro de MEDIA_ROOT.
    Previene ataques de path traversal (CWE-22).
    """
    try:
        media_root = Path(settings.MEDIA_ROOT).resolve()
        archivo_path = Path(file_path).resolve()
        return str(archivo_path).startswith(str(media_root))
    except Exception:
        return False

# Uso en procesar_archivo_erp()
if not _validar_ruta_archivo(archivo.archivo.path):
    raise ValueError("Ruta de archivo no válida o fuera del directorio permitido")
```

**CVSS:** 7.5 (Alto) → Mitigado  
**CWE:** CWE-22 (Path Traversal)

---

### C-02: Exposición de PII en Logs ✅ RESUELTO

**Ubicación:** `procesar_erp.py`, `talana.py`

**Riesgo:** RUTs y nombres de empleados expuestos en logs de aplicación, violando GDPR/Ley 21.719.

**Solución implementada:**

1. **Helper para enmascarar RUT:**
```python
# procesar_erp.py - líneas 33-46
def _mask_rut(rut: str) -> str:
    """Enmascara RUT para logs, mostrando solo últimos 4 caracteres."""
    if not rut or len(rut) < 5:
        return "****"
    return f"****{rut[-4:]}"
```

2. **Logs sin PII:**
```python
# Antes:
logger.info(f"Procesando archivo ERP: {archivo.nombre_original}")
warnings.append(f"Ignorando baja de {rut}: ...")

# Después:
logger.info(f"Procesando archivo ERP ID={archivo_id}, tipo={archivo.tipo}")
warnings.append(f"Ignorando baja fila {idx}: ...")
```

**CVSS:** 6.5 (Medio-Alto) → Mitigado  
**CWE:** CWE-532 (Information Exposure Through Log Files)

---

## 🟠 Vulnerabilidades Altas

### H-01: Validación Insuficiente de RUT

**Ubicación:** `base.py:142-167`, `talana.py:276`

**Problema:** Solo limpia formato, no valida dígito verificador.

```python
# Actual - Acepta cualquier cosa
rut = str(rut).replace('.', '').replace(' ', '').strip()

# Necesario - Validar DV
def validar_rut_chileno(rut: str) -> tuple[bool, str]:
    """Valida formato y dígito verificador de RUT chileno."""
    rut_limpio = rut.replace('.', '').replace('-', '').upper()
    if len(rut_limpio) < 2:
        return False, "RUT muy corto"
    
    cuerpo, dv = rut_limpio[:-1], rut_limpio[-1]
    
    # Calcular DV esperado (módulo 11)
    suma = 0
    multiplo = 2
    for c in reversed(cuerpo):
        suma += int(c) * multiplo
        multiplo = multiplo + 1 if multiplo < 7 else 2
    
    dv_esperado = 11 - (suma % 11)
    dv_esperado = 'K' if dv_esperado == 10 else '0' if dv_esperado == 11 else str(dv_esperado)
    
    if dv != dv_esperado:
        return False, f"DV inválido: esperado {dv_esperado}, recibido {dv}"
    
    return True, rut_limpio
```

---

### H-02: Sin Límite de Tamaño de Archivo 📋 DEUDA TÉCNICA

**Ubicación:** `procesar_erp.py` (task completa)

**Riesgo:** DoS por carga de archivos masivos que agoten memoria/CPU.

**Decisión:** Diferido como deuda técnica. Empresas grandes pueden tener archivos de tamaño considerable y se requiere análisis de casos de uso reales para definir límite apropiado.

**Ticket de seguimiento:** Crear issue para analizar tamaños reales de archivos en producción y definir límite.

**Solución futura:**
```python
import os

MAX_FILE_SIZE = XX * 1024 * 1024  # A definir con datos reales

def _procesar_movimientos_mes(archivo):
    file_size = os.path.getsize(archivo.archivo.path)
    if file_size > MAX_FILE_SIZE:
        raise ValueError(f"Archivo excede tamaño máximo permitido")
```

---

### H-03: Datos Raw sin Sanitizar

**Ubicación:** `procesar_erp.py:278-281`

**Problema:** `datos_raw` almacena datos del Excel sin sanitización.

```python
# Actual - Guarda todo
datos_raw = registro.get('datos_raw', {})

# Mejorar - Sanitizar y limitar campos
CAMPOS_PERMITIDOS_RAW = ['tipo_contrato', 'motivo', 'tipo_ausentismo']

def sanitizar_datos_raw(data: dict) -> dict:
    """Sanitiza datos raw para almacenamiento seguro."""
    resultado = {}
    for k, v in data.items():
        if k.lower() in CAMPOS_PERMITIDOS_RAW:
            # Sanitizar valor
            if isinstance(v, str):
                v = bleach.clean(v, tags=[], strip=True)[:500]
            resultado[k] = v
    return resultado
```

---

## 🟡 Vulnerabilidades Medias

### M-01: Sin Rate Limiting en Task

**Riesgo:** Usuario podría saturar cola Celery con múltiples archivos.

**Solución:** Implementar throttling por usuario en endpoint de subida.

### M-02: Sin Validación de MIME Type

**Riesgo:** Archivos maliciosos renombrados como .xlsx.

**Solución:**
```python
import magic

def validar_mime_type(archivo_path: str) -> bool:
    """Valida que el archivo sea realmente un Excel."""
    mime = magic.from_file(archivo_path, mime=True)
    ALLOWED_MIMES = [
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'application/vnd.ms-excel',
    ]
    return mime in ALLOWED_MIMES
```

---

## ✅ Aspectos Positivos

1. **Uso de ORM Django:** Previene SQL injection
2. **Celery con timeouts:** Previene procesos colgados
3. **Bulk create:** Operación atómica, menos superficie de ataque
4. **Normalización centralizada:** Funciones `normalizar_rut`, `normalizar_monto`

---

## 📋 Plan de Remediación

### Fase 1 - BLOQUEANTE ✅ COMPLETADA

| ID | Vulnerabilidad | Esfuerzo | Estado |
|----|---------------|----------|--------|
| C-01 | Path Traversal | 2h | ✅ Resuelto |
| C-02 | PII en Logs | 4h | ✅ Resuelto |
| H-02 | Límite tamaño | 1h | 📋 Deuda técnica |

### Fase 2 - Alta Prioridad (1 semana)

| ID | Vulnerabilidad | Esfuerzo |
|----|---------------|----------|
| H-01 | Validación RUT | 3h |
| H-03 | Sanitizar datos_raw | 2h |

### Fase 3 - Media Prioridad (Sprint 2)

| ID | Vulnerabilidad | Esfuerzo |
|----|---------------|----------|
| M-01 | Rate limiting | 4h |
| M-02 | Validación MIME | 2h |

---

## 🎯 Decisión

**✅ APROBADO PARA PRODUCCIÓN**

Las vulnerabilidades críticas C-01 y C-02 han sido resueltas:
- Path traversal: Validación de ruta implementada
- PII en logs: RUT y datos sensibles removidos de mensajes de log

H-02 (límite de tamaño) queda como deuda técnica pendiente de análisis.

---

## Checklist Pre-Producción

- [x] Implementar validación de path (C-01)
- [x] Redactar PII en logs (C-02)
- [ ] Agregar límite de tamaño (H-02) - Deuda técnica
- [x] Re-revisar código post-fix
- [ ] Test de penetración básico

---

## Archivos Revisados

- `backend/apps/validador/services/erp/talana.py`
- `backend/apps/validador/tasks/procesar_erp.py`
- `backend/apps/validador/services/erp/base.py`

---

**Próxima revisión:** Post-implementación de fixes Fase 1
