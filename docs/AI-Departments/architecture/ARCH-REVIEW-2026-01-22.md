# Architecture Review - SGM v2

**Fecha:** 2026-01-22  
**Revisor:** AI Architecture Department  
**Sistema:** SGM v2 (Sistema de Gestión de Nómina)  
**Versión:** 2.0

---

## 📋 Resumen Ejecutivo

### Calificación General: **7.5/10** ✅

| Área | Estado | Puntuación |
|------|--------|------------|
| Service Layer Pattern | ✅ Bien implementado | 8/10 |
| ERP Factory/Strategy | ⚠️ Duplicación detectada | 6/10 |
| Arquitectura Medallion | ⚠️ Capa Oro incompleta | 7/10 |
| Flujo de Estados | ✅ Bien definido | 8/10 |
| Celery Tasks | ⚠️ Falta idempotencia | 6/10 |
| Escalabilidad | ⚠️ Queries N+1 | 7/10 |

### Estado General
- **Issues Totales:** 14
- **Críticos:** 3
- **Altos:** 5
- **Medios:** 5
- **Bajos:** 1

### Recomendación Principal
Resolver issues críticos (ISSUE-005, ISSUE-009, ISSUE-014) en Sprint 1 antes de escalar a producción completa.

---

## 🔍 Análisis por Área

### 1. Service Layer Pattern ✅

**Ubicación:** `backend/apps/validador/services/`

**Fortalezas:**
- Patrón `ServiceResult` bien implementado con `success`, `data`, `error`
- Separación clara de lógica de negocio vs views
- Servicios bien nombrados: `CierreService`, `ArchivoService`, `IncidenciaService`

**Código ejemplo encontrado:**
```python
# backend/apps/validador/services/base.py
class ServiceResult:
    def __init__(self, success=True, data=None, error=None, errors=None):
        self.success = success
        self.data = data
        self.error = error
        self.errors = errors or {}
```

**Issues:**
- ISSUE-001: Falta Repository Pattern para queries complejas
- ISSUE-003: Algunos servicios tienen más de 300 líneas (monolíticos)

---

### 2. ERP Factory/Strategy Pattern ⚠️

**Ubicación:** 
- `backend/apps/validador/services/erp/` (Strategies)
- `backend/apps/validador/parsers/` (Parsers)

**Fortalezas:**
- Auto-registro con decoradores
- Soporte para múltiples ERPs: Talana, SAP, Buk
- Extensible para nuevos ERPs

**Issues Críticos:**
- **ISSUE-004 (ALTO):** Duplicación de jerarquías
  - `services/erp/` tiene strategies
  - `parsers/` tiene parsers
  - Ambos hacen parsing de archivos (confusión de responsabilidades)

**Estructura actual:**
```
services/erp/
├── base.py          # ERPStrategy base
├── factory.py       # ERPFactory
├── talana.py        # TalanaStrategy
├── sap.py           # SAPStrategy
└── buk.py           # BukStrategy

parsers/
├── base.py          # BaseLibroParser
├── factory.py       # ParserFactory
└── talana.py        # TalanaParser
```

**Recomendación:** Unificar en una sola jerarquía

---

### 3. Arquitectura Medallion (Bronce→Plata→Oro) ⚠️

**Concepto:** Procesamiento de datos en 3 capas

| Capa | Modelo | Estado | Descripción |
|------|--------|--------|-------------|
| Bronce | `RegistroLibro`, `RegistroNovedades` | ✅ | Datos crudos extraídos |
| Plata | Post-comparación | ✅ | Datos validados y comparados |
| Oro | Consolidado | ⚠️ **INCOMPLETO** | Totales para reportería |

**Issue Crítico:**
- **ISSUE-005 (CRÍTICO):** Capa Oro no implementada completamente
  - `libro_service.py` procesa hasta Plata
  - Faltan cálculos de consolidación para reportería
  - `EstadoCierre.CONSOLIDADO` existe pero no hay servicio de consolidación

---

### 4. Flujo de Estados del Cierre ✅

**Ubicación:** `backend/apps/validador/constants.py`

**7 Estados definidos:**
```
CARGA_ARCHIVOS → [Comparación] → CON/SIN_DISCREPANCIAS
                                        ↓ (click manual)
                                   CONSOLIDADO
                                        ↓ (detectar)
                                CON/SIN_INCIDENCIAS → FINALIZADO
```

**Fortalezas:**
- Máquina de estados explícita en constantes
- Grupos de estados bien definidos:
  - `ESTADOS_ACTIVOS`
  - `ESTADOS_PUEDEN_RETROCEDER`
  - `ESTADOS_REQUIEREN_ACCION_MANUAL`
- Transiciones controladas por servicios

**Issues:**
- ISSUE-006: Falta versionamiento de datos (pérdida de auditoría en retrocesos)

---

### 5. Arquitectura de Celery Tasks ⚠️

**Ubicación:** `backend/apps/validador/tasks/`

**Tasks identificadas:**
- `procesar_archivo_erp` - Procesa libro de remuneraciones
- `procesar_archivo_analista` - Archivos del cliente
- `extraer_headers_novedades` - Extracción de headers
- `ejecutar_comparacion` - Compara ERP vs Novedades
- `detectar_incidencias` - Post-comparación
- `generar_consolidacion` - Genera consolidado

**Issues Críticos:**

**ISSUE-009 (CRÍTICO):** Procesamiento síncrono dentro de tasks
```python
# Patrón detectado en tasks/libro.py
def procesar_archivo_erp(cierre_id, archivo_id):
    archivo = ArchivoERP.objects.get(id=archivo_id)
    # ⚠️ Procesamiento síncrono de archivo completo en memoria
    df = pd.read_excel(archivo.archivo.path)
    # Puede bloquear worker por minutos
```

**ISSUE-011 (ALTO):** Sin idempotencia
- Si task falla y reintenta, puede crear registros duplicados
- Falta `task_id` como clave de idempotencia

**ISSUE-014 (CRÍTICO):** Detección de incidencias no implementada
- Task `detectar_incidencias` existe pero lógica está incompleta
- Comparación con mes anterior no funcional

---

### 6. Comparación y Discrepancias ⚠️

**Ubicación:** `backend/apps/validador/tasks/comparacion.py`

**Issue:**
- **ISSUE-012 (ALTO):** Lógica monolítica de 132+ líneas
- Difícil de testear y extender

**Código problemático:**
```python
# comparacion.py - función principal muy larga
def ejecutar_comparacion(cierre_id):
    # ... 132 líneas de lógica de comparación
    # Mezcla queries, validaciones, y transformaciones
```

**Recomendación:** Extraer en:
- `ComparacionStrategy` (patrón Strategy por tipo de comparación)
- `DiscrepanciaFactory` (para crear discrepancias)
- `ComparacionValidator` (validaciones)

---

### 7. Queries y Performance ⚠️

**Issue:**
- **ISSUE-013 (ALTO):** Queries N+1 detectados

**Ubicaciones problemáticas:**
```python
# cierre_service.py
for cierre in cierres:
    archivos = cierre.archivos_erp.all()  # N+1
    incidencias = cierre.incidencias.all()  # N+1

# Solución: usar prefetch_related
cierres = Cierre.objects.prefetch_related(
    'archivos_erp',
    'incidencias'
).filter(...)
```

**Nota:** Algunas partes del código YA usan `select_related/prefetch_related` correctamente.

---

## 🚨 ISSUES DE INTERÉS

### Tabla de Issues por Severidad

| ID | Severidad | Área | Título | Impacto | Esfuerzo |
|----|-----------|------|--------|---------|----------|
| **ISSUE-005** | 🔴 CRÍTICO | Medallion | Cálculos de consolidación (Oro) no implementados | Reportería no funcional | 5d |
| **ISSUE-009** | 🔴 CRÍTICO | Celery | Procesamiento síncrono bloquea workers | Timeouts, caídas | 3d |
| **ISSUE-014** | 🔴 CRÍTICO | Feature | Detección de incidencias no implementada | Feature core rota | 5d |
| **ISSUE-004** | 🟠 ALTO | ERP | Parsers y Strategies duplicados | Confusión, bugs | 3d |
| **ISSUE-006** | 🟠 ALTO | Auditoría | Falta versionamiento de datos | Pérdida de histórico | 5d |
| **ISSUE-011** | 🟠 ALTO | Celery | Sin idempotencia en tasks | Datos duplicados | 2d |
| **ISSUE-012** | 🟠 ALTO | Code | Lógica de comparación monolítica (132 líneas) | Difícil mantener | 3d |
| **ISSUE-013** | 🟠 ALTO | Performance | Queries N+1 en servicios | Lentitud | 2d |
| **ISSUE-001** | 🟡 MEDIO | Architecture | Falta Repository Pattern | Queries dispersas | 5d |
| **ISSUE-003** | 🟡 MEDIO | Code | Servicios monolíticos (>300 líneas) | Difícil testear | 3d |
| **ISSUE-007** | 🟡 MEDIO | Celery | Sin monitoreo de tasks largas | Invisibilidad | 2d |
| **ISSUE-008** | 🟡 MEDIO | Code | Falta validación de archivos antes de parsing | Errores crípticos | 2d |
| **ISSUE-010** | 🟡 MEDIO | Reliability | Sin retry estratégico en tasks | Fallos silenciosos | 2d |
| **ISSUE-002** | 🟢 BAJO | Docs | Inconsistencia en docstrings | DX pobre | 3d |

**Total:** 14 Issues | **Esfuerzo estimado:** 45 días-persona

---

### Detalle de Issues Críticos

#### ISSUE-005: Capa Oro Incompleta
```
Severidad: 🔴 CRÍTICO
Ubicación: backend/apps/validador/services/libro_service.py
Impacto: Reportería y consolidación no funcionan
Esfuerzo: 5 días

Descripción:
La arquitectura Medallion define 3 capas, pero la capa Oro (consolidación)
no tiene implementación. LibroService procesa hasta capa Plata.

Código faltante:
- Servicio de consolidación
- Modelo ConsolidadoCierre o similar
- Task de consolidación

Recomendación:
1. Crear ConsolidacionService
2. Implementar modelos de capa Oro
3. Crear task generar_consolidacion_completa
```

#### ISSUE-009: Workers Bloqueados
```
Severidad: 🔴 CRÍTICO
Ubicación: backend/apps/validador/tasks/libro.py
Impacto: Celery workers bloqueados, timeouts
Esfuerzo: 3 días

Descripción:
Tasks procesan archivos completos en memoria (pandas read_excel).
Archivos grandes (>10MB) bloquean workers por minutos.

Código problemático:
  df = pd.read_excel(archivo.archivo.path)  # Bloquea

Solución:
1. Implementar procesamiento por chunks
2. Usar streaming para archivos grandes
3. Configurar soft_time_limit en tasks
```

#### ISSUE-014: Detección de Incidencias
```
Severidad: 🔴 CRÍTICO
Ubicación: backend/apps/validador/tasks/incidencias.py
Impacto: Feature core no funciona
Esfuerzo: 5 días

Descripción:
La detección de incidencias (variación >30% vs mes anterior) es una
feature core pero está incompleta.

Faltante:
- Query de mes anterior
- Cálculo de variación porcentual
- Generación de incidencias automáticas
- Manejo de primer cierre (sin mes anterior)
```

---

## 💡 Recomendaciones

### Arquitectura

1. **Unificar ERP Parsers/Strategies** (ISSUE-004)
   - Mover todo a `services/erp/`
   - Parser es responsabilidad de Strategy
   - Eliminar `parsers/` como paquete separado

2. **Implementar Repository Pattern** (ISSUE-001)
   - Crear `CierreRepository`, `ArchivoRepository`
   - Encapsular queries complejas
   - Facilitar testing con mocks

3. **Event Sourcing para Estados** (Future)
   - Guardar transiciones como eventos
   - Reconstruir estado desde eventos
   - Auditoría completa

### Celery

4. **Procesamiento por Chunks** (ISSUE-009)
```python
# Recomendación
def procesar_archivo_erp(cierre_id, archivo_id):
    for chunk in pd.read_excel(path, chunksize=1000):
        procesar_chunk.delay(cierre_id, chunk.to_dict())
```

5. **Idempotencia** (ISSUE-011)
```python
@celery_app.task(bind=True)
def procesar_archivo(self, cierre_id, archivo_id):
    lock_key = f"proceso:{cierre_id}:{archivo_id}"
    if cache.get(lock_key):
        return  # Ya procesado
    cache.set(lock_key, True, timeout=3600)
    # ... procesar
```

### Performance

6. **Optimizar Queries** (ISSUE-013)
```python
# Siempre usar prefetch_related para relaciones
Cierre.objects.select_related(
    'cliente', 'analista'
).prefetch_related(
    'archivos_erp',
    'archivos_analista', 
    'incidencias',
    'discrepancias'
).filter(...)
```

---

## 📝 ADRs Sugeridos

| # | Título | Prioridad |
|---|--------|-----------|
| ADR-001 | Implementar Repository Pattern | ALTA |
| ADR-002 | Migrar a procesamiento por chunks (Celery) | CRÍTICA |
| ADR-003 | Event Sourcing para estados de cierre | MEDIA |
| ADR-004 | Unificar parsers y strategies ERP | ALTA |
| ADR-005 | Implementar CQRS para reportería | BAJA |

---

## 📅 Plan de Acción (4 Sprints)

### Sprint 1 (Semanas 1-2): Issues Críticos
- [ ] ISSUE-014: Implementar detección de incidencias
- [ ] ISSUE-005: Completar capa Oro (consolidación)
- [ ] ISSUE-009: Refactorizar tasks a chunks

### Sprint 2 (Semanas 3-4): Issues Altos
- [ ] ISSUE-004: Unificar ERP parsers/strategies
- [ ] ISSUE-006: Implementar versionamiento de datos
- [ ] ISSUE-011: Agregar idempotencia a tasks
- [ ] ISSUE-013: Optimizar queries N+1

### Sprint 3 (Semanas 5-6): Mejoras Arquitectónicas
- [ ] ISSUE-001: Repository Pattern
- [ ] ISSUE-012: Refactorizar lógica de comparación
- [ ] Crear ADRs documentando decisiones

### Sprint 4 (Semanas 7-8): Calidad y Seguridad
- [ ] ISSUE-003: Dividir servicios monolíticos
- [ ] ISSUE-008: Validación de archivos pre-parsing
- [ ] ISSUE-010: Retry estratégico en tasks
- [ ] Implementar tests de integración

---

## 📊 Métricas de Éxito

| Métrica | Actual | Objetivo |
|---------|--------|----------|
| Issues Críticos | 3 | 0 |
| Cobertura de tests | ~0% | 70% |
| Queries N+1 | Múltiples | 0 |
| Tasks con idempotencia | 0% | 100% |
| ADRs documentados | 0 | 5+ |

---

## ✅ Sign-off

**Revisado por:** AI Architecture Department  
**Fecha:** 2026-01-22  
**Próxima Revisión:** Post-Sprint 2 (2026-02-05)

**Estado:** 📋 Pendiente revisión de Tech Lead

---

*Este documento fue generado como parte del análisis multi-departamental SGM v2.*
