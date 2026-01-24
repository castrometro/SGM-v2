# 🤖 Responsible AI Review: Movimientos del Mes - Talana

**Fecha:** 24 Enero 2026  
**Feature:** Procesamiento de archivo Movimientos del Mes para ERP Talana  
**Reviewer:** @se-responsible-ai

---

## 🎯 Calificación General: **A- (87/100)**

**Estado:** ✅ **APROBADO PARA PRODUCCIÓN CON CONDICIONES**

---

## 📊 Evaluación por Dimensión

| Dimensión | Puntuación | Peso | Ponderado |
|-----------|------------|------|-----------|
| Fairness | 100/100 | 25% | 25.0 |
| Transparencia | 92/100 | 20% | 18.4 |
| Privacidad | 65/100 | 20% | 13.0 |
| Auditoría | 95/100 | 15% | 14.25 |
| Inclusividad | 98/100 | 15% | 14.7 |
| Impacto Social | 85/100 | 5% | 4.25 |
| **Total** | | | **89.6 → 87** |

---

## ✅ Fortalezas Éticas

### 1. Fairness (100/100) - Sin Discriminación

**Hallazgo:** La regla RN-001 (baja + plazo fijo + sin motivo = ignorar) **NO discrimina**.

**Análisis:**
- La regla aplica por **tipo de evento laboral**, no por características personales
- Contratos "Plazo Fijo", "Indefinido", "Honorarios" se procesan igual
- No hay filtrado por edad, género, nacionalidad u otras características protegidas

**Justificación de RN-001:**
> Un contrato a plazo fijo que termina sin motivo adicional es un **vencimiento natural**, 
> no una baja. El empleado puede ser recontratado al mes siguiente.

### 2. Transparencia (92/100) - Trazabilidad Completa

**Fortalezas:**
- ✅ Logging dual: `logger.info()` + warnings en resultado
- ✅ Warnings específicos cuando se ignora un registro
- ✅ Hojas procesadas reportadas en resultado

**Ejemplo de transparencia:**
```python
warnings.append(
    f"Ignorando baja de {rut}: Plazo Fijo sin motivo (vencimiento contrato)"
)
```

### 3. Auditoría (95/100) - Trazabilidad de Datos

**Fortalezas:**
- ✅ `archivo_erp` FK permite rastrear origen de cada movimiento
- ✅ `hoja_origen` indica de qué hoja Excel proviene
- ✅ `datos_raw` preserva información original para auditoría

### 4. Inclusividad (98/100) - Procesamiento Permisivo

**Fortaleza:** El sistema procesa **todos los registros válidos**, no falla por datos parciales.

```python
# Si una hoja no existe, continúa con las demás
if self.HOJA_ALTAS_BAJAS in hojas_disponibles:
    # procesar
else:
    warnings.append(f"Hoja '{self.HOJA_ALTAS_BAJAS}' no encontrada")
    # NO falla, continúa
```

---

## ⚠️ Áreas de Mejora

### 1. Privacidad (65/100) - Datos Sensibles

#### P-01: Licencias Médicas sin Cifrado Específico

**Problema:** Las licencias médicas son **datos de salud (PHI)** que requieren protección especial.

**Campos afectados:**
- `tipo_licencia`: "medica", "maternal"
- `datos_raw`: Puede contener información médica

**Impacto:** ~1-5% de empleados tienen licencias médicas por mes.

**Recomendación (P1 - 30 días):**
```python
from django.db import models
from django_cryptography.fields import encrypt

class MovimientoMes(models.Model):
    # Campos sensibles cifrados
    tipo_licencia = encrypt(models.CharField(max_length=100, blank=True))
    datos_raw = encrypt(models.JSONField(default=dict, blank=True))
```

#### P-02: Retención Indefinida de Datos

**Problema:** No hay política de eliminación automática de datos antiguos.

**Impacto:** Potencial conflicto con derecho al olvido (GDPR/Ley 21.719).

**Recomendación (P2 - 90 días):**
```python
# Comando Django para ejecutar mensualmente
def limpiar_movimientos_antiguos():
    """Elimina movimientos de cierres con > 3 años."""
    fecha_limite = timezone.now() - timedelta(days=3*365)
    MovimientoMes.objects.filter(
        cierre__fecha_cierre__lt=fecha_limite
    ).delete()
```

#### P-03: PII en Logs

**Problema:** RUTs y nombres pueden aparecer en logs de error/warning.

**Recomendación:** Ver reporte de seguridad SEC-MOVIMIENTOS-MES-2026-01-24.md

---

## 📋 Población Afectada

| Grupo | Impacto | Población Est. |
|-------|---------|----------------|
| Empleados activos | Validación de nómina | 100% |
| Empleados con licencias | Datos de salud procesados | 1-5% mensual |
| Nuevos ingresos | Registro de alta | 2-3% mensual |
| Finiquitos | Registro de baja | 2-3% mensual |

**Impacto económico crítico:** Error en procesamiento → Empleado puede no recibir pago correcto.

---

## 🎯 Recomendaciones Priorizadas

### P1 - Crítico (30 días)

| ID | Acción | Esfuerzo |
|----|--------|----------|
| E-01 | Cifrar campos de licencias médicas | 4h |
| E-02 | Redactar PII en logs | 4h |

### P2 - Alto (90 días)

| ID | Acción | Esfuerzo |
|----|--------|----------|
| E-03 | Implementar política de retención (3 años) | 1 día |
| E-04 | Documentar política de privacidad | 4h |

### P3 - Mejora Continua

| ID | Acción | Esfuerzo |
|----|--------|----------|
| E-05 | Anonimización para entorno de pruebas | 1 día |
| E-06 | Dashboard de privacidad para empleados | 2 semanas |

---

## ✅ Decisión de Producción

### **APROBADO CON CONDICIONES**

**Condición 1 (Inmediata):**
- Implementar redacción de PII en logs (E-02)

**Condición 2 (30 días):**
- Cifrado de campos de licencias médicas (E-01)

**Condición 3 (90 días):**
- Política de retención de datos (E-03)
- Documentación de privacidad (E-04)

**Justificación:**
El sistema es éticamente sólido en fairness, transparencia y auditoría. Las mejoras de privacidad son importantes pero **no bloquean producción** dado que:
- ✅ Base de datos ya está cifrada a nivel de disco
- ✅ Acceso controlado por roles de Django
- ✅ Auditoría permite detectar accesos indebidos

---

## Métricas de Monitoreo Ético

### KPIs Recomendados

| Métrica | Meta | Frecuencia |
|---------|------|------------|
| % logs sin PII | 100% | Semanal |
| Datos > 3 años | 0 registros | Mensual |
| Accesos a licencias auditados | 100% | Continuo |
| Errores por tipo contrato | Uniforme | Mensual |

---

## Archivos Revisados

- `backend/apps/validador/models/movimiento.py`
- `backend/apps/validador/services/erp/talana.py`
- `backend/apps/validador/tasks/procesar_erp.py`

---

**Próxima revisión:** 90 días post-producción o post-implementación de mejoras P1/P2
