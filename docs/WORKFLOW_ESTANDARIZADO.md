# 🔄 Workflow Estandarizado del Proyecto REX+

**Última actualización:** 19 Enero 2026  
**Versión:** 2.0  
**Basado en:** Sprint 1 Post-Fixes + Mejoras de Paralelismo

---

## 📋 Resumen del Flujo

```
Análisis → Issues → Implementación → Reviews Paralelos → Documentación Departamental → Dashboard y Status Report
    ↓         ↓            ↓                 ↓                    ↓                             ↓
 Fase 0    GitHub     Secuencial      Arch+Sec+Ethics          CURRENT.md                 Consolidación
(planif)            (dependencias)     (paralelo)              +CHANGELOG                    + Métricas
```

---

## 🧠 Fase 0: Análisis y Planificación (CRÍTICO - Antes de Ejecutar)

> **Regla:** Nunca ejecutar sin antes analizar. 5 minutos de planificación ahorran horas de retrabajo.

### Paso 1: Entender el Alcance

**Preguntas obligatorias:**
- [ ] ¿Qué issues/tareas hay que completar?
- [ ] ¿Cuál es el objetivo final del sprint/feature?
- [ ] ¿Hay deadline o dependencias externas?
- [ ] ¿Qué archivos/módulos se van a modificar?

**Comando sugerido:**
```bash
# Ver issues del sprint actual
@se-product-manager "lista issues pendientes del sprint actual"
```

### Paso 2: Clasificar Tareas (Paralelo vs Secuencial)

| Tipo | Criterio | Cuándo Usar | Ejemplo |
|------|----------|-------------|---------|
| 🔴 **Secuencial** | Output de A es input de B | Dependencias técnicas | Implementar → Testear |
| 🟢 **Paralelo** | Sin dependencias entre sí | Tareas independientes | Security + Ethics review |
| 🟡 **Bloqueante** | Debe completarse PRIMERO | Prerequisitos | Setup estructura → Todo |

**Árbol de Decisión:**
```
¿Tarea B necesita el resultado de Tarea A?
    │
    ├─ SÍ → 🔴 SECUENCIAL (A antes que B)
    │
    └─ NO → ¿Modifican los mismos archivos?
                │
                ├─ SÍ → 🔴 SECUENCIAL (evitar conflictos)
                │
                └─ NO → 🟢 PARALELO ✅
```

### Paso 3: Crear Matriz de Dependencias

**Plantilla:**

| # | Tarea | Depende de | Bloquea a | Tipo | Agente |
|---|-------|------------|-----------|------|--------|
| 1 | Implementar código | - | 2, 3, 4, 5 | 🟡 Bloqueante | @general-purpose |
| 2 | Tests unitarios | 1 | 3, 4, 5 | 🔴 Secuencial | @task |
| 3 | Architecture review | 2 | 6 | 🟢 Paralelo | @se-architect |
| 4 | Security review | 2 | 6 | 🟢 Paralelo | @se-security |
| 5 | Ethics review | 2 | 6 | 🟢 Paralelo | @se-responsible-ai |
| 6 | Dashboard update | 3, 4, 5 | - | 🔴 Secuencial | Manual |

### Paso 4: Generar Plan de Ejecución

**Formato estándar:**

```markdown
## 📋 Plan de Ejecución: [Nombre del Feature/Sprint]

### 🟡 Bloque 1: Prerequisitos (Secuencial)
1. [ ] Tarea bloqueante 1
2. [ ] Tarea bloqueante 2

### 🔴 Bloque 2: Implementación (Secuencial)
3. [ ] Implementar código
4. [ ] Ejecutar tests

### 🟢 Bloque 3: Reviews (PARALELO)
Ejecutar simultáneamente:
- [ ] @se-architect → Architecture review
- [ ] @se-security → Security review  
- [ ] @se-responsible-ai → Ethics review

### 🔵 Bloque 4: Consolidación (Secuencial)
5. [ ] Actualizar CURRENT.md de cada área
6. [ ] Consolidar en DASHBOARD.md
7. [ ] Usuario decide commit
```

### Paso 5: Validar Plan

**Checklist antes de ejecutar:**
- [ ] ¿Todas las dependencias están identificadas?
- [ ] ¿Las tareas paralelas son realmente independientes?
- [ ] ¿El orden tiene sentido técnico?
- [ ] ¿Hay tareas que se pueden combinar?

---

## 🎯 Fase 1: Planificación de Issues

### Sprint Planning:
1. **Revisar Sprint Goal** (PROJECT_PLAN.md)
2. **Crear Issues en GitHub** según plan
   - Issues de desarrollo (domain/services/GUI)
   - Issues de testing
   - Issues de fixes/mejoras

### Issues del Sprint 1 Completados:
- ✅ **#25:** Bank Validator - Catálogo inmutable + SHA256
- ✅ **#26:** Amount Validator - Notación científica bloqueada
- ✅ **#29:** RUT Validator - Soporte 6-8 dígitos

### Issues del Sprint 1 Pendientes:
- ⏳ **#6:** Tests unitarios de validadores (8h estimadas)

---

## 🛠️ Fase 2: Implementación

### Agente Usado: `@general-purpose` (o agente de task)

**Proceso:**
1. **Contexto completo** al agente:
   ```
   "Implementa el Issue #X según especificación.
   - Código: src/rex_parser/domain/validators/
   - Tests: tests/unit/domain/validators/
   - Sigue arquitectura DDD existente"
   ```

2. **Ejecución en paralelo** si hay múltiples issues independientes:
   - Issue #25, #26, #29 se ejecutaron en paralelo
   - Cada issue en su contexto de agente separado

3. **Output esperado:**
   - ✅ Código implementado
   - ✅ Tests pasando
   - ⚠️ **NO hacer commits automáticos**

---

## ⚠️ IMPORTANTE: Control de Versiones

### 🚫 NUNCA hacer commits automáticamente

**Regla de oro:** El usuario tiene la última palabra sobre los commits.

**Proceso correcto:**
1. ✅ Agentes implementan código y tests
2. ✅ Agentes verifican que tests pasan
3. ✅ Agentes reportan cambios realizados
4. ⏳ **Usuario revisa los cambios**
5. ⏳ **Usuario decide si hacer commit**
6. ⏳ **Usuario escribe el mensaje de commit**
7. ⏳ **Usuario ejecuta git add/commit/push**

**Razones:**
- Control total sobre el historial de Git
- Revisión manual antes de commit
- Mensajes de commit personalizados
- Evitar commits no deseados
- Workflow más seguro y controlado

**Ejemplo de output correcto del agente:**
```
✅ Cambios implementados en:
   - src/rex_parser/domain/validators/rut_validator.py
   - tests/unit/domain/validators/test_security.py

✅ Tests: 10/10 passing

⏳ SIGUIENTE PASO:
   Revisa los cambios y decide si hacer commit:
   
   git diff
   git add .
   git commit -m "fix: tu mensaje aquí"
   git push
```

---

## 🔍 Fase 3: Evaluación Tripartita (Paralelo)

### Después de implementar, ejecutar 3 agentes en paralelo:

#### 1. **@se-architect** - Architecture Review

**Comando:**
```
@se-architect revisa la arquitectura del código implementado en Sprint 1:
- Issues: #25, #26, #29
- Archivos: src/rex_parser/domain/validators/
- Genera reporte completo con:
  * Calificación global (0-100)
  * Métricas por aspecto (DDD, Patrones, Performance, etc.)
  * Deudas técnicas identificadas
  * Recomendaciones
```

**Output:**
- Archivo: `DOCS/architecture/history/sprint1-post-fixes.md` (reporte detallado)
- Actualiza: `DOCS/architecture/CURRENT.md` (snapshot actual)
- Actualiza: `DOCS/architecture/CHANGELOG.md` (resumen cambios)

---

#### 2. **@se-security** - Security/Code Review

**Comando:**
```
@se-security revisa la seguridad del código implementado:
- Valida vulnerabilidades OWASP Top 10
- Analiza fixes de Issues #25, #26
- Genera reporte con:
  * Vulnerabilidades por severidad (ALTA/MEDIA/BAJA)
  * Calificación global (0-100)
  * Recomendaciones de fixes
  * Tests de seguridad requeridos
```

**Output:**
- Archivo: `DOCS/code-review/history/sprint1-post-fixes.md`
- Actualiza: `DOCS/code-review/CURRENT.md`
- Actualiza: `DOCS/code-review/CHANGELOG.md`

---

#### 3. **@se-responsible-ai** - Ethics Review

**Comando:**
```
@se-responsible-ai revisa los aspectos éticos del código:
- Evalúa inclusión y fairness (Issue #29 - RUT 6-9 dígitos)
- Analiza impacto social (adultos mayores, migrantes)
- Genera reporte con:
  * Calificación por dimensión (Fairness, Privacy, Accessibility, etc.)
  * Impacto cuantificado (personas afectadas)
  * Recomendaciones éticas
```

**Output:**
- Archivo: `DOCS/responsible-ai/history/sprint1-post-fixes.md`
- Actualiza: `DOCS/responsible-ai/CURRENT.md`
- Actualiza: `DOCS/responsible-ai/CHANGELOG.md`

---

## 📊 Fase 4: Consolidación en Dashboard

### Después de las 3 reviews, actualizar `DOCS/DASHBOARD.md`:

**Proceso manual:**
1. **Extraer métricas** de los 3 CURRENT.md:
   - Security: B (82/100)
   - Architecture: A (93/100)
   - Responsible AI: A- (90/100)

2. **Calcular calificación global:**
   ```
   Global = (Security × 0.35) + (Architecture × 0.40) + (Ethics × 0.25)
   Global = (82 × 0.35) + (93 × 0.40) + (90 × 0.25) = 88/100 = A-
   ```

3. **Actualizar secciones:**
   - 🎯 Estado General del Proyecto
   - 📊 Métricas por Área
   - 🎯 Vulnerabilidades
   - 📈 Tendencias Sprint X
   - 🏆 Logros del Sprint X
   - ⚠️ Trabajo Pendiente
   - 🚀 Decisión de Deploy

4. **Actualizar metadatos:**
   ```markdown
   **Última actualización:** [fecha]
   **Milestone actual:** [versión]
   ```

---

## 📝 Patrón de Documentación

### Estructura de cada área (Architecture, Security, Ethics):

```
DOCS/[area]/
├── CURRENT.md              # Estado actual (se SOBRESCRIBE cada sprint)
├── CHANGELOG.md            # Historial resumido (se ACUMULA)
└── history/
    ├── sprint1-initial.md       # Reporte inicial detallado (opcional)
    └── sprint1-post-fixes.md    # Reporte post-fixes detallado
```

### Plantilla CURRENT.md:

```markdown
# [Emoji] [Área] Report - Estado Actual

**Última actualización:** [Fecha] - Sprint X [Estado]
**Calificación:** [A+/A/A-/B+/B/...] ([XX]/100) [⬆️/⬇️/=] ([+/-X] desde inicial)
**Estado:** [✅ Listo / ⚠️ Condicional / ❌ No listo]

---

## 📊 Resumen Ejecutivo

### Calificación por Aspecto:

| Aspecto | Rating | Tendencia | Estado |
|---------|--------|-----------|--------|
| **[Aspecto 1]** | [X]/100 | [⬆️/⬇️/=] | [✅/⚠️/❌] |
| **[Aspecto 2]** | [X]/100 | [⬆️/⬇️/=] | [✅/⚠️/❌] |

---

## 🏆 Mejoras Implementadas

### **Issue #X: [Título]**
- [Descripción del fix]
- [Impacto]
- **Evaluación:** [Calificación]

---

## ⚠️ Deudas Técnicas / Vulnerabilidades / Brechas

### **[ID]: [Título]**
- **Prioridad:** [CRÍTICA/ALTA/MEDIA/BAJA]
- **Tiempo estimado:** [Xh]
- **Sprint recomendado:** Sprint X
- **Impacto:** [Descripción]

---

## 🎯 Decisión de [Área]

### [✅/⚠️/❌] **[DECISIÓN FINAL]**

**Criterios cumplidos:** [lista]
**Bloqueantes:** [lista o "Ninguno"]

---

## 📈 Evolución de Métricas

### Comparativa Sprint X:

| Métrica | Inicial | Post-Fixes | Mejora |
|---------|---------|------------|--------|
| **Global** | [X] | [Y] | [+/-Z] |

---

## 📚 Documentación

- **Reporte completo:** [history/sprintX-xxx.md]
- **Historial:** [CHANGELOG.md]
- **Dashboard:** [../DASHBOARD.md]

---

## 👥 Aprobaciones

- [ ] ✅ **[Rol]:** [Estado]
- [ ] ⏳ **[Rol]:** Pendiente

---

**Próxima revisión:** [Fecha/Evento]
**Contacto:** [Team Name]
```

### Plantilla CHANGELOG.md:

```markdown
# 📅 [Área] Reviews - Changelog

Historia completa de revisiones.

---

## Sprint X - [Estado] ([Fecha])

### 🎯 Calificación: [Grade] ([XX]/100) [⬆️/⬇️] ([+/-X] puntos)

**Issues implementados:**
- [✅/⏳/❌] **#XX** - [Título] ([Calificación])

**Mejoras [del área]:**
- [⬆️/⬇️/=] [Aspecto]: [Antes] → [Después] = [+/-X] puntos

**Deudas técnicas:** X nuevas ([estado])

**Estado:** [✅/⚠️/❌] [Descripción]

**Reporte completo:** [history/sprintX-xxx.md]

---

## Resumen de Tendencias

\```
Sprint X:    [Grade] ([XX]) ████████████░░░░░░░░░░░░░░
Sprint Y:    [Grade] ([YY]) ████████████████░░░░░░░░░░ [⬆️/⬇️] [+/-X]
\```

**Evolución por aspecto:** [lista]

---

## 🏆 Logros Destacados

### **[Título del Logro]**
- [Descripción]
- **Lección:** [Learning]

---

**Última actualización:** [Fecha]
**Ver estado actual:** [CURRENT.md]
**Dashboard:** [../DASHBOARD.md]
```

---

## 🔄 Ciclo Completo del Workflow

### Sprint N:

```mermaid
graph TD
    A[Sprint Planning] --> B[Crear Issues en GitHub]
    B --> C{Issues de Desarrollo}
    B --> D{Issues de Testing}
    
    C --> E[Implementar con @general-purpose]
    E --> F[Código + Tests]
    
    F --> G[@se-architect Review]
    F --> H[@se-security Review]
    F --> I[@se-responsible-ai Review]
    
    G --> J[history/sprintN-xxx.md]
    H --> K[history/sprintN-xxx.md]
    I --> L[history/sprintN-xxx.md]
    
    J --> M[Actualizar CURRENT.md]
    K --> N[Actualizar CURRENT.md]
    L --> O[Actualizar CURRENT.md]
    
    M --> P[Consolidar en DASHBOARD.md]
    N --> P
    O --> P
    
    P --> Q{¿Listo para Producción?}
    Q -->|Sí| R[Continuar con Testing]
    Q -->|No| S[Crear Issues de Fixes]
    
    S --> C
    
    D --> T[Tests E2E]
    R --> T
    T --> U[Deploy / Release]
```

---

## ⚙️ Ejecución con Agentes (Recomendado)

### Método: Invocación Directa de Agentes

> **No usamos scripts de automatización.** Los agentes se invocan directamente para mayor flexibilidad y paralelismo real.

### Ejecución Paralela Real:

```bash
# En lugar de scripts, invocar agentes directamente:

# Reviews en paralelo (3 ventanas/sesiones simultáneas):
@se-architect "revisa arquitectura de [componente]"
@se-security "revisa seguridad de [componente]"
@se-responsible-ai "evalúa impacto ético de [componente]"

# O usar el tool task para paralelismo:
task @se-architect + task @se-security + task @se-responsible-ai
```

### Ventajas vs Scripts:

| Aspecto | Scripts | Agentes Directos |
|---------|---------|------------------|
| Paralelismo | ❌ Falso (secuencial) | ✅ Real |
| Flexibilidad | ❌ Rígido | ✅ Total |
| Mantenimiento | ❌ Código extra | ✅ Cero |
| Context window | ❌ Limitado | ✅ Completo |

### Reglas de Ejecución:

- ✅ Invocar agentes con contexto completo
- ✅ Especificar archivos/issues a revisar
- ✅ Pedir output en formato estándar
- 🚫 **NUNCA** pedir commits automáticos
- ⏳ Usuario revisa y hace commit manualmente

---

## 📞 Contactos del Workflow

**Architecture Reviews:** Architecture Team  
**Security Reviews:** Security Team  
**Ethics Reviews:** Responsible AI Team  
**Project Lead:** @castrometro

---

## 📚 Referencias

- **Project Plan:** [DOCS/PROJECT_PLAN.md](PROJECT_PLAN.md)
- **Dashboard:** [DOCS/DASHBOARD.md](DASHBOARD.md)
- **Agentes:** [.github/agents/](.github/agents/)
- **Mapeo de Agentes:** [DOCS/AGENTS_MAPPING.md](AGENTS_MAPPING.md)

---

**Última actualización:** 19 Enero 2026  
**Versión:** 2.0  
**Mantenido por:** Documentation Team
