# 📋 Plan de Ejecución: Movimientos del Mes - Talana

> **Feature:** Procesamiento de archivo Movimientos del Mes para ERP Talana  
> **Fecha:** 24 Enero 2026  
> **Estimación total:** ~4-6 horas  
> **Documentación relacionada:** [MOVIMIENTOS_MES.md](MOVIMIENTOS_MES.md)

---

## 🧠 Fase 0: Análisis y Planificación ✅

### Alcance Definido
- **Objetivo:** Procesar Excel de Movimientos del Mes de Talana (3 hojas)
- **Hojas:** "Altas y Bajas", "Ausentismos", "Vacaciones"
- **Headers:** Fila 3 (índice 2), Datos desde fila 4
- **Modelo destino:** `MovimientoMes`
- **Patrón:** Strategy (`TalanaStrategy`)

### Regla de Negocio Principal (RN-001)
> Baja + Plazo Fijo + Sin Motivo = **Ignorar** (vencimiento de contrato)

---

## 📊 Matriz de Dependencias

| # | Tarea | Depende de | Bloquea a | Tipo | Agente |
|---|-------|------------|-----------|------|--------|
| 1 | Actualizar modelo MovimientoMes | - | 2, 3 | 🟡 Bloqueante | @general-purpose |
| 2 | Actualizar TalanaStrategy | 1 | 3 | 🔴 Secuencial | @general-purpose |
| 3 | Actualizar Task procesar_erp | 1, 2 | 4, 5 | 🔴 Secuencial | @general-purpose |
| 4 | Crear ViewSet/Serializer | 1 | 6, 7, 8 | 🔴 Secuencial | @general-purpose |
| 5 | Ejecutar tests manuales | 3 | 6, 7, 8 | 🔴 Secuencial | @task |
| 6 | Architecture review | 4, 5 | 9 | 🟢 Paralelo | @se-architect |
| 7 | Security review | 4, 5 | 9 | 🟢 Paralelo | @se-security |
| 8 | Ethics review | 4, 5 | 9 | 🟢 Paralelo | @se-responsible-ai |
| 9 | Documentación final | 6, 7, 8 | - | 🔴 Secuencial | Manual |

---

## 🟡 Bloque 1: Prerequisitos (Secuencial)

### 1.1 Actualizar Modelo MovimientoMes
**Archivo:** `backend/apps/validador/models/movimiento.py`

- [ ] Agregar campo `tipo_contrato` (CharField, max_length=50, blank=True)
- [ ] Agregar campo `archivo_erp` (FK a ArchivoERP, null=True, on_delete=CASCADE)
- [ ] Agregar constante `TIPO_LICENCIA_CHOICES` para normalizar valores
- [ ] Crear migración: `python manage.py makemigrations validador`
- [ ] Aplicar migración: `python manage.py migrate`

**Campos nuevos:**
```python
tipo_contrato = models.CharField(
    max_length=50,
    blank=True,
    help_text="Plazo Fijo, Indefinido, etc."
)

archivo_erp = models.ForeignKey(
    'ArchivoERP',
    on_delete=models.CASCADE,
    null=True,
    blank=True,
    related_name='movimientos'
)
```

---

## 🔴 Bloque 2: Implementación Core (Secuencial)

### 2.1 Actualizar TalanaStrategy
**Archivo:** `backend/apps/validador/services/erp/talana.py`

- [ ] Definir constantes de mapeo para cada hoja:
  - `MAPEO_ALTAS_BAJAS`
  - `MAPEO_AUSENTISMOS`
  - `MAPEO_VACACIONES`
- [ ] Definir `MAPEO_TIPO_AUSENTISMO` (case-insensitive)
- [ ] Reescribir `_parse_movimientos_mes()` para procesar 3 hojas
- [ ] Implementar `_parse_hoja_altas_bajas(df)` con regla RN-001
- [ ] Implementar `_parse_hoja_ausentismos(df)` con mapeo de tipos
- [ ] Implementar `_parse_hoja_vacaciones(df)`
- [ ] Actualizar `get_formato_esperado('movimientos_mes')`

**Estructura de retorno:**
```python
ParseResult.ok({
    'altas_bajas': [...],      # Lista de dicts normalizados
    'ausentismos': [...],
    'vacaciones': [...],
    'hojas_encontradas': ['Altas y Bajas', ...],
    'warnings': [],
})
```

### 2.2 Actualizar Task de Procesamiento
**Archivo:** `backend/apps/validador/tasks/procesar_erp.py`

- [ ] Reescribir `_procesar_movimientos_mes(archivo)`:
  - Obtener strategy via ERPFactory
  - Llamar `strategy.parse_archivo(file, 'movimientos_mes')`
  - Crear registros MovimientoMes en bulk
- [ ] Implementar `_crear_movimientos_desde_datos(cierre, archivo, datos, hoja)`
- [ ] Actualizar `archivo.hojas_encontradas` con hojas procesadas
- [ ] Actualizar `archivo.registros_procesados` con conteo total
- [ ] Manejar errores y actualizar `archivo.error_mensaje`

### 2.3 Crear/Actualizar Serializers y ViewSet (Opcional)
**Archivos:** 
- `backend/apps/validador/serializers/movimiento.py` (crear si no existe)
- `backend/apps/validador/views/movimiento.py` (crear si no existe)
- `backend/apps/validador/urls.py`

- [ ] Crear `MovimientoMesSerializer` con campos relevantes
- [ ] Crear `MovimientoMesViewSet` con:
  - Filtro por cierre_id
  - Filtro por tipo
  - Action `resumen` para estadísticas
- [ ] Registrar en router de urls.py

---

## ✅ Bloque 3: Verificación (Secuencial)

### 3.1 Tests Manuales
- [ ] Subir archivo Excel de prueba via API
- [ ] Verificar que task Celery se ejecute
- [ ] Verificar registros creados en MovimientoMes
- [ ] Verificar regla RN-001 (baja plazo fijo sin motivo ignorada)
- [ ] Verificar mapeo correcto de tipos de ausentismo

### 3.2 Tests Automatizados (Opcional para MVP)
**Archivo:** `backend/apps/validador/tests/test_movimientos_talana.py`

- [ ] Test parsing TalanaStrategy con Excel mock
- [ ] Test regla RN-001
- [ ] Test mapeo case-insensitive de ausentismos
- [ ] Test task completa con archivo real

---

## 🟢 Bloque 4: Reviews (PARALELO)

> Ejecutar simultáneamente después de verificación:

- [ ] **@se-architect** → Revisar arquitectura de la implementación
  - Uso correcto del patrón Strategy
  - Separación de responsabilidades (Strategy vs Task)
  - Performance del bulk create
  
- [ ] **@se-security** → Revisar seguridad
  - Validación de datos de entrada
  - Manejo de archivos subidos
  - Sanitización de datos Excel
  
- [ ] **@se-responsible-ai** → Revisar aspectos éticos
  - Manejo de datos personales (RUT, nombres)
  - Logging apropiado sin exponer PII

---

## 🔵 Bloque 5: Consolidación (Secuencial)

- [ ] Actualizar `docs/MOVIMIENTOS_MES.md` con cambios finales
- [ ] Marcar tareas completadas en este plan
- [ ] Reportar cambios al usuario para decisión de commit

---

## 📁 Archivos a Modificar/Crear

```
backend/apps/validador/
├── models/
│   └── movimiento.py              # MODIFICAR ✏️
├── services/erp/
│   └── talana.py                  # MODIFICAR ✏️
├── tasks/
│   └── procesar_erp.py            # MODIFICAR ✏️
├── serializers/
│   └── movimiento.py              # CREAR (opcional) 📄
├── views/
│   └── movimiento.py              # CREAR (opcional) 📄
├── urls.py                        # MODIFICAR (si ViewSet) ✏️
└── migrations/
    └── 00XX_movimiento_campos.py  # CREAR (auto) 📄
```

---

## ⚠️ Recordatorios

- 🚫 **NO hacer commits automáticos** - Usuario decide
- ✅ Usar `bulk_create` para performance
- ✅ Normalizar RUTs antes de guardar
- ✅ Manejar fechas en múltiples formatos
- ✅ Case-insensitive para tipos de ausentismo

---

## 🎯 Criterios de Aceptación

1. ✅ Archivo Excel de Talana se procesa correctamente
2. ✅ Las 3 hojas se leen con headers en fila 3
3. ✅ Regla RN-001 funciona (baja plazo fijo sin motivo = ignorar)
4. ✅ Tipos de ausentismo se mapean correctamente
5. ✅ MovimientoMes tiene trazabilidad a ArchivoERP
6. ✅ Sin regresiones en procesamiento de Libro de Remuneraciones

---

## 🚫 Fuera de Alcance (esta iteración)

- Procesamiento para otros ERPs (BUK, SAP)
- UI específica en frontend
- Comparación automática con MovimientoAnalista (ya existe en flujo cierre)
