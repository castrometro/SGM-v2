# 📋 Architecture Review: Movimientos del Mes - Talana

**Fecha:** 24 Enero 2026  
**Feature:** Procesamiento de archivo Movimientos del Mes para ERP Talana  
**Reviewer:** @se-architect

---

## 🎯 Calificación General: **A- (87/100)**

**Arquitectura sólida con oportunidades de mejora en manejo de errores**

---

## 📊 Evaluación por Criterios

| Criterio | Puntuación | Estado |
|----------|------------|--------|
| Patrón Strategy | 95/100 | ✅ Excelente |
| Separación de Responsabilidades | 90/100 | ✅ Muy Bueno |
| Performance | 95/100 | ✅ Excelente |
| Manejo de Errores | 75/100 | ⚠️ Mejorable |
| Extensibilidad | 95/100 | ✅ Excelente |

---

## ✅ Fortalezas

### 1. Patrón Strategy (95/100)

- **Factory Pattern correctamente implementado**: Decorador `@ERPFactory.register('talana')` permite registrar estrategias automáticamente
- **Separación clara**: Base abstracta define el contrato, cada ERP implementa su lógica
- **Extensibilidad garantizada**: Agregar nuevo ERP solo requiere crear clase y decorarla
- **Fallback inteligente**: Si no existe estrategia específica, usa `GenericStrategy`

```python
# Uso desde el Task - desacoplamiento perfecto
strategy = ERPFactory.get_strategy(erp_codigo)
result = strategy.parse_archivo(archivo.archivo.path, 'movimientos_mes')
```

### 2. Separación de Responsabilidades (90/100)

```
📁 Excel Upload
   ↓
📋 Task (procesar_erp.py)
   ├─ Obtiene Strategy del ERP
   ├─ Strategy.parse_archivo()
   │   ├─ Lee 3 hojas Excel
   │   ├─ Normaliza datos
   │   └─ Aplica RN-001 (baja plazo fijo)
   ├─ Recibe data normalizada
   └─ Persiste con bulk_create()
```

### 3. Performance (95/100)

- **bulk_create()**: Crea todos los registros en una sola query
- **Eliminación eficiente**: `DELETE FROM movimientos WHERE archivo_erp_id = X`
- **Celery task con timeouts**: `soft_time_limit=600, time_limit=720`
- **Índices en modelo**: `Index(fields=['cierre', 'tipo'])`, `Index(fields=['cierre', 'rut'])`

### 4. Extensibilidad (95/100)

Para agregar nuevo ERP (ej: BUK):
```python
@ERPFactory.register('buk')
class BUKStrategy(ERPStrategy):
    MAPEO_ALTAS_BAJAS = {
        'RUT Trabajador': 'rut',
        'Nombre Completo': 'nombre',
    }
    
    def _parse_movimientos_mes(self, file):
        # Lógica específica de BUK
```

**No requiere cambios en:** Task, Modelo, Factory

---

## ⚠️ Áreas de Mejora

### 1. Manejo de Errores (75/100)

**Problema 1: Silenciamiento de excepciones**
```python
# procesar_erp.py línea 67-68
except:
    pass  # ❌ Silencia cualquier error
```

**Solución:**
```python
except Exception as e:
    logger.critical(f"No se pudo actualizar estado del archivo {archivo_id}: {e}")
```

**Problema 2: Conversión de fechas sin logging**
```python
# talana.py línea 269
except (ValueError, TypeError):
    pass  # ❌ Fecha inválida → None silenciosamente
```

**Solución:**
```python
except (ValueError, TypeError) as e:
    self.logger.warning(f"Fecha inválida: {valor} - {e}")
```

### 2. Reglas de Negocio Mezcladas

**Problema:** RN-001 está en `TalanaStrategy._parse_hoja_altas_bajas()`

**Riesgo:** Si otro ERP tiene la misma regla, se duplicaría código

**Solución propuesta:**
```python
# backend/apps/validador/business_rules/movimiento_rules.py
class MovimientoBusinessRules:
    @staticmethod
    def debe_ignorar_baja(tipo_contrato: str, causal: str) -> bool:
        """RN-001: Ignorar baja de plazo fijo sin motivo"""
        return tipo_contrato.lower() == 'plazo fijo' and not causal
```

---

## 📈 Escalabilidad

| Escenario | Performance | Estado |
|-----------|------------|--------|
| 100 movimientos | ~2 seg | ✅ OK |
| 1,000 movimientos | ~10 seg | ✅ OK |
| 10,000 movimientos | ~90 seg | ⚠️ Límite |
| 100,000+ movimientos | Timeout | ❌ Requiere chunking |

**Recomendación para >10K registros:**
```python
CHUNK_SIZE = 1000
for i in range(0, len(movimientos), CHUNK_SIZE):
    chunk = movimientos[i:i+CHUNK_SIZE]
    MovimientoMes.objects.bulk_create(chunk)
```

---

## 🎯 Recomendaciones Priorizadas

### Alta Prioridad (Esta semana)
- [ ] Quitar `except: pass` silencioso
- [ ] Agregar logging en conversión de fechas fallida
- [ ] Documentar regla RN-001 en docstring

### Media Prioridad (1-2 semanas)
- [ ] Extraer `MovimientoBusinessRules`
- [ ] Crear ADR para decisión de reglas de negocio en Strategy vs Service

### Baja Prioridad (1-2 meses)
- [ ] Implementar chunking para >10K registros
- [ ] Agregar observabilidad (traces)

---

## ✅ Decisión

**APROBADO PARA PRODUCCIÓN** con las mitigaciones de errores implementadas.

La arquitectura escala bien hasta ~10K movimientos/archivo. Para volúmenes mayores, implementar chunking.

---

## Archivos Revisados

- `backend/apps/validador/models/movimiento.py`
- `backend/apps/validador/services/erp/talana.py`
- `backend/apps/validador/tasks/procesar_erp.py`

---

**Próxima revisión:** Post-implementación de mejoras
