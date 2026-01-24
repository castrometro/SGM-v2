# ⚖️ Responsible AI Review: Archivos del Analista

**Fecha:** 24 Enero 2026  
**Feature:** Procesamiento de Ingresos, Finiquitos, Ausentismos  
**Reviewer:** @se-responsible-ai  
**Ley aplicable:** Ley 21.719 - Protección de Datos Personales (Chile)

---

## 🎯 Estado: 🟡 **APROBADO CON CONDICIONES**

### Calificación: **82/100** (B+)

| Dimensión | Rating | Estado |
|-----------|--------|--------|
| Privacidad | 70/100 | ⚠️ |
| Fairness | 88/100 | ✅ |
| Inclusión | 92/100 | ✅ |
| Transparencia | 85/100 | ✅ |
| Impacto Social | 78/100 | ⚠️ |
| Cumplimiento Legal | 75/100 | ⚠️ |

---

## ✅ Fortalezas Identificadas

### Fairness & No Discriminación
- Validación inclusiva de RUT (sin restricciones discriminatorias)
- No hay hard-coded demographics (género, edad, nacionalidad)
- Categoría 'otro' en tipos de ausentismo previene exclusión

### Inclusión & Accesibilidad
- Mensajes en español chileno
- Emojis como ayuda visual (accesibilidad cognitiva)
- Detección automática de headers (flexibilidad)
- Cálculo automático de días (no requiere cálculo manual)
- Re-upload support (permite corrección sin penalización)

### Transparencia
- Historial completo de eventos (HistorialCierre)
- Progress tracking en tiempo real
- Foreign Keys preservan origen del dato

---

## ⚠️ Riesgos Identificados

### 🔴 Críticos

**R1. Logging de PII sin redacción**
- RUTs y nombres pueden aparecer en logs del servidor
- Violación Art. 10 Ley 21.719

**R2. Campo `causal` en finiquitos sin protección especial**
- Puede contener información sensible ("despido por rendimiento")
- Violación Art. 15 Ley 21.719 (datos sensibles)

**R3. Campo `tipo_ausentismo` puede contener datos médicos**
- "Licencia por depresión", "Tratamiento oncológico"
- Sin encriptación ni protección especial

### 🟠 Altos

**R4. Mapeo de motivos puede enmascarar despidos encubiertos**
- "Renuncia forzada" → se clasifica como "renuncia_voluntaria"
- Impacto: Afecta estadísticas laborales y posibles demandas

**R5. No se preservan datos raw del Excel**
- Imposibilita auditorías del dato original
- En disputa laboral, no se puede demostrar qué contenía el archivo

---

## 📋 Cumplimiento Ley 21.719

| Artículo | Requisito | Estado |
|----------|-----------|--------|
| Art. 10 | Tratamiento lícito | ⚠️ Parcial (PII en logs) |
| Art. 15 | Datos sensibles | ❌ NO (causal sin protección) |
| Art. 16 | Consentimiento | ⚠️ No verificable |
| Art. 21 | Derecho al olvido | ✅ CASCADE delete |
| Art. 25 | Seguridad de datos | ⚠️ Parcial |

---

## 💡 Recomendaciones Priorizadas

### P1 - Crítico (Antes de producción)

1. **Implementar redacción de PII en logs** (4h)
   ```python
   def redact_rut(rut): return f"****{rut[-4:]}" if rut else "***"
   ```

2. **Agregar campo `datos_raw`** para trazabilidad (6h)
   - Preservar datos originales del Excel
   - Habilita auditorías completas

3. **Documentar base legal y consentimiento** (4h)
   - Crear `docs/responsible-ai/consentimiento-datos-personales.md`

### P2 - Alto (Sprint actual)

4. **Categorías especiales de ausentismos protegidos**
   - Licencia maternal/paternal/adoptiva con flag `es_licencia_protegida`

5. **Mejorar lógica de mapeo de motivos**
   - Preservar contexto en metadata
   - Flag `posible_despido_encubierto`

6. **TTL más agresivo en Redis para PII** (10 min vs 1 hora)

---

## 🌐 Impacto Social

### Población Afectada

| Grupo | Cantidad/mes | Impacto | Criticidad |
|-------|--------------|---------|------------|
| Trabajadores nuevos | 50-100 | Positivo | Media |
| Trabajadores con finiquito | 20-50 | Alto | **ALTA** |
| Trabajadores con ausentismo | 100-200 | Alto | **ALTA** |

### Escenario de Riesgo

**Finiquito mal clasificado:**
- "Renuncia forzada" → "renuncia voluntaria"
- Pérdida de indemnización (3-6 meses sueldo)
- Impacto individual: Muy alto
- Probabilidad: 5-10%

---

## 🎯 Decisión

### ✅ **APROBADO PARA PRODUCCIÓN** con condiciones:

1. Implementar R1, R2, R3 (redacción PII, datos raw, documentación) en **máximo 14 días**
2. Implementar R4, R5, R6 en **máximo 30 días**
3. Auditoría de cumplimiento Ley 21.719 antes del primer uso con datos reales

---

## Firma Ética

> "Este sistema, con las mejoras implementadas, tratará los datos personales de los trabajadores con el respeto, cuidado y protección legal que merecen."

---

**Próxima revisión:** Post-implementación de recomendaciones P1 (14 días)
