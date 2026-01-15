# Flujo de Cierre - SGM v2

> Documentación detallada del flujo de estados del cierre de nómina.

## Índice

1. [Estados del Cierre](#estados-del-cierre)
2. [Diagrama de Flujo](#diagrama-de-flujo)
3. [Estado 1: CARGA_ARCHIVOS](#estado-1-carga_archivos)
4. [Estado 2: CON_DISCREPANCIAS](#estado-2-con_discrepancias)
5. [Estado 3: SIN_DISCREPANCIAS](#estado-3-sin_discrepancias)
6. [Estado 4: CONSOLIDADO](#estado-4-consolidado)
7. [Estado 5: CON_INCIDENCIAS](#estado-5-con_incidencias)
8. [Estado 6: SIN_INCIDENCIAS](#estado-6-sin_incidencias)
9. [Estado 7: FINALIZADO](#estado-7-finalizado)
10. [Transiciones](#transiciones)
11. [Estados de Archivos](#estados-de-archivos)

---

## Estados del Cierre

| # | Estado | Código | Descripción | Acción Requerida |
|---|--------|--------|-------------|------------------|
| 1 | Carga de Archivos | `carga_archivos` | Hub de trabajo principal | Subir archivos, clasificar, mapear |
| 2 | Con Discrepancias | `con_discrepancias` | Existen diferencias ERP vs Cliente | Resolver discrepancias |
| 3 | Sin Discrepancias | `sin_discrepancias` | 0 discrepancias | Click manual para consolidar |
| 4 | Consolidado | `consolidado` | Datos validados y confirmados | Detectar incidencias |
| 5 | Con Incidencias | `con_incidencias` | Hay incidencias detectadas | Resolver incidencias |
| 6 | Sin Incidencias | `sin_incidencias` | No hay incidencias | Finalizar |
| 7 | Finalizado | `finalizado` | Proceso completo | Ninguna |

### Estados Especiales

| Estado | Código | Descripción |
|--------|--------|-------------|
| Error | `error` | Ocurrió un error en el proceso |
| Cancelado | `cancelado` | Cierre cancelado manualmente |

---

## Diagrama de Flujo

```
                    ┌─────────────────────────────────────────────────────────┐
                    │                    CARGA_ARCHIVOS                       │
                    │                                                         │
                    │  ┌─────────────┐ ┌─────────────┐ ┌─────────────────┐   │
                    │  │ 📁 Libro    │ │ 📋 Clasif.  │ │ 📁 Novedades    │   │
                    │  │ ERP         │ │ Conceptos   │ │ Cliente         │   │
                    │  └─────────────┘ └─────────────┘ └─────────────────┘   │
                    │                                                         │
                    │  ┌─────────────────────────────────────────────────┐   │
                    │  │ 🔗 Mapeo: Headers Novedades → Conceptos Libro   │   │
                    │  └─────────────────────────────────────────────────┘   │
                    │                                                         │
                    │         [🚀 Generar Comparación] ← Habilitado cuando:  │
                    │           ✅ Libro procesado                           │
                    │           ✅ Conceptos clasificados                    │
                    │           ✅ Novedades procesadas                      │
                    │           ✅ Headers mapeados                          │
                    └─────────────────────────┬───────────────────────────────┘
                                              │
                        ┌─────────────────────┴─────────────────────┐
                        ▼                                           ▼
               ┌─────────────────┐                        ┌─────────────────┐
               │ CON_DISCREPANCIAS│                       │SIN_DISCREPANCIAS│
               │                  │                        │                 │
               │ Hay diferencias  │◄───────────────────────│ 0 diferencias   │
               │ por resolver     │  (si resuelve todas)   │                 │
               └────────┬─────────┘                        └────────┬────────┘
                        │                                           │
                        │ [↩️ Volver a Carga]                       │
                        │ (corregir archivos)                       │
                        │                                           │
                        │                                  [✅ Consolidar]
                        │                                  (acción MANUAL)
                        │                                           │
                        └──────────────────┬────────────────────────┘
                                           ▼
                                  ┌─────────────────┐
                                  │   CONSOLIDADO   │
                                  │                 │
                                  │ Datos validados │
                                  │ y confirmados   │
                                  └────────┬────────┘
                                           │
                                  [🔍 Detectar Incidencias]
                                       (acción MANUAL)
                                           │
                        ┌──────────────────┴──────────────────┐
                        ▼                                      ▼
               ┌─────────────────┐                    ┌─────────────────┐
               │ CON_INCIDENCIAS │                    │ SIN_INCIDENCIAS │
               │                 │                    │                 │
               │ Hay incidencias │                    │ No hay          │
               │ por revisar     │                    │ incidencias     │
               └────────┬────────┘                    └────────┬────────┘
                        │                                      │
               [✅ Resolver todas]                    [✅ Finalizar]
                        │                                      │
                        └──────────────────┬───────────────────┘
                                           ▼
                                  ┌─────────────────┐
                                  │   FINALIZADO    │
                                  │                 │
                                  │ Cierre completo │
                                  └─────────────────┘
```

---

## Estado 1: CARGA_ARCHIVOS

### Descripción
Es el **hub de trabajo principal**. Una sola vista donde el usuario realiza toda la preparación antes de la comparación.

### Vista UI
```
┌─────────────────────────────────────────────────────────────────────┐
│  Cierre: Cliente ABC - Diciembre 2025                    [Estado]   │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐  │
│  │ 📁 Libro ERP     │  │ 📋 Clasificación │  │ 📁 Novedades     │  │
│  │                  │  │                  │  │                  │  │
│  │ [Subir archivo]  │  │ 45/45 conceptos  │  │ [Subir archivo]  │  │
│  │ ✅ Procesado     │  │ ✅ Completo      │  │ ⏳ Pendiente     │  │
│  └──────────────────┘  └──────────────────┘  └──────────────────┘  │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ 🔗 Mapeo de Novedades                                       │   │
│  │                                                             │   │
│  │ Mapear headers del archivo novedades → conceptos del libro  │   │
│  │ 12/15 mapeados                                              │   │
│  │                                                             │   │
│  │ [Abrir Mapeo]                                               │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │              [🚀 Generar Comparación]                       │   │
│  │                     (deshabilitado)                         │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Condiciones para Avanzar

El botón **"Generar Comparación"** solo se habilita cuando:

| Requisito | Verificación |
|-----------|--------------|
| Libro ERP subido | `archivo_libro.estado == 'procesado'` |
| Conceptos clasificados | `ConceptoLibro.filter(cliente, categoria=None).count() == 0` |
| Novedades subidas | `archivo_novedades.estado == 'procesado'` |
| Headers mapeados | `ConceptoNovedades.filter(cliente, concepto_libro=None).count() == 0` |

### Acciones Disponibles

- ➕ Subir archivo Libro ERP
- ❌ Eliminar archivo Libro ERP
- 📋 Clasificar conceptos del libro
- ➕ Subir archivo Novedades
- ❌ Eliminar archivo Novedades
- 🔗 Mapear headers de novedades
- 🚀 Generar comparación (cuando todo listo)

---

## Estado 2: CON_DISCREPANCIAS

### Descripción
La comparación encontró diferencias entre el libro ERP y las novedades del cliente.

### Acciones Disponibles

- 👀 Ver lista de discrepancias
- ✏️ Resolver discrepancia individual
- ↩️ Volver a CARGA_ARCHIVOS (para corregir archivos)

### Transiciones

| Destino | Trigger | Automático |
|---------|---------|------------|
| `SIN_DISCREPANCIAS` | Cuando `discrepancias.count() == 0` | ✅ Sí |
| `CARGA_ARCHIVOS` | Botón "Volver a Carga" | ❌ No (manual) |

---

## Estado 3: SIN_DISCREPANCIAS

### Descripción
El cierre tiene **0 discrepancias**. Puede llegar aquí de dos formas:
1. La comparación inicial no encontró diferencias
2. Todas las discrepancias fueron resueltas

### ⚠️ Requiere Acción Manual
Este estado **SIEMPRE** requiere que el analista haga click explícito para pasar a CONSOLIDADO. **Nunca es automático**.

### Razón
El analista debe confirmar conscientemente que revisó los datos y están correctos antes de consolidar.

### Acciones Disponibles

- ✅ Consolidar (avanzar a CONSOLIDADO)
- ↩️ Volver a CARGA_ARCHIVOS (por si acaso)

---

## Estado 4: CONSOLIDADO

### Descripción
Los datos han sido validados y el analista confirmó que están correctos. Ahora se procede a detectar incidencias.

### Acciones Disponibles

- 🔍 Detectar incidencias (acción manual)

### Transiciones

| Destino | Trigger | Automático |
|---------|---------|------------|
| `CON_INCIDENCIAS` | Detección encuentra incidencias | ❌ No (manual trigger) |
| `SIN_INCIDENCIAS` | Detección no encuentra incidencias | ❌ No (manual trigger) |

---

## Estado 5: CON_INCIDENCIAS

### Descripción
La detección encontró incidencias que requieren revisión.

### Acciones Disponibles

- 👀 Ver lista de incidencias
- ✅ Aprobar incidencia
- ❌ Rechazar incidencia

### Transiciones

| Destino | Trigger | Automático |
|---------|---------|------------|
| `SIN_INCIDENCIAS` | Cuando todas las incidencias resueltas | ✅ Sí |

---

## Estado 6: SIN_INCIDENCIAS

### Descripción
No hay incidencias pendientes. El cierre está listo para finalizar.

### Acciones Disponibles

- ✅ Finalizar cierre

### Transiciones

| Destino | Trigger | Automático |
|---------|---------|------------|
| `FINALIZADO` | Botón "Finalizar" | ❌ No (manual) |

---

## Estado 7: FINALIZADO

### Descripción
El proceso de cierre está completo. Es un estado terminal.

### Acciones Disponibles

- 📄 Ver resumen final
- 📊 Generar reportes
- 📥 Descargar documentos

---

## Transiciones

### Matriz de Transiciones Válidas

| Desde / Hacia | CARGA | CON_DISC | SIN_DISC | CONSOL | CON_INC | SIN_INC | FINAL |
|---------------|-------|----------|----------|--------|---------|---------|-------|
| CARGA_ARCHIVOS | - | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| CON_DISCREPANCIAS | ✅ | - | ✅ | ❌ | ❌ | ❌ | ❌ |
| SIN_DISCREPANCIAS | ✅ | ❌ | - | ✅ | ❌ | ❌ | ❌ |
| CONSOLIDADO | ❌ | ❌ | ❌ | - | ✅ | ✅ | ❌ |
| CON_INCIDENCIAS | ❌ | ❌ | ❌ | ❌ | - | ✅ | ❌ |
| SIN_INCIDENCIAS | ❌ | ❌ | ❌ | ❌ | ❌ | - | ✅ |
| FINALIZADO | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | - |

### Transiciones Automáticas vs Manuales

| Transición | Tipo | Notas |
|------------|------|-------|
| CARGA → CON_DISC/SIN_DISC | Manual | Botón "Generar Comparación" |
| CON_DISC → SIN_DISC | Automático | Al resolver última discrepancia |
| CON_DISC → CARGA | Manual | Botón "Volver a Carga" |
| SIN_DISC → CONSOLIDADO | **Manual** | ⚠️ Siempre requiere click |
| CONSOLIDADO → CON/SIN_INC | Manual | Botón "Detectar Incidencias" |
| CON_INC → SIN_INC | Automático | Al resolver última incidencia |
| SIN_INC → FINALIZADO | Manual | Botón "Finalizar" |

---

## Estados de Archivos

Los archivos (libro y novedades) tienen su propio ciclo de vida independiente.

### EstadoArchivoLibro

```
SUBIDO → EXTRAYENDO_HEADERS → PENDIENTE_CLASIFICACION → LISTO → PROCESANDO → PROCESADO
                                                                      ↓
                                                                    ERROR
```

| Estado | Descripción |
|--------|-------------|
| `subido` | Archivo recién subido |
| `extrayendo_headers` | Tarea Celery extrayendo columnas |
| `pendiente_clasificacion` | Headers extraídos, esperando clasificación |
| `listo` | Conceptos clasificados, listo para procesar |
| `procesando` | Tarea Celery procesando datos |
| `procesado` | ✅ Datos procesados correctamente |
| `error` | ❌ Error en algún paso |

### EstadoArchivoNovedades

```
SUBIDO → EXTRAYENDO_HEADERS → PENDIENTE_MAPEO → LISTO → PROCESANDO → PROCESADO
                                                              ↓
                                                            ERROR
```

| Estado | Descripción |
|--------|-------------|
| `subido` | Archivo recién subido |
| `extrayendo_headers` | Tarea Celery extrayendo columnas |
| `pendiente_mapeo` | Headers extraídos, esperando mapeo |
| `listo` | Headers mapeados, listo para procesar |
| `procesando` | Tarea Celery procesando datos |
| `procesado` | ✅ Datos procesados correctamente |
| `error` | ❌ Error en algún paso |

---

## Implementación Backend

### Constantes

```python
# apps/validador/constants.py

class EstadoCierre:
    CARGA_ARCHIVOS = 'carga_archivos'
    CON_DISCREPANCIAS = 'con_discrepancias'
    SIN_DISCREPANCIAS = 'sin_discrepancias'
    CONSOLIDADO = 'consolidado'
    CON_INCIDENCIAS = 'con_incidencias'
    SIN_INCIDENCIAS = 'sin_incidencias'
    FINALIZADO = 'finalizado'
    ERROR = 'error'
    CANCELADO = 'cancelado'
    
    CHOICES = [
        (CARGA_ARCHIVOS, 'Carga de Archivos'),
        (CON_DISCREPANCIAS, 'Con Discrepancias'),
        (SIN_DISCREPANCIAS, 'Sin Discrepancias'),
        (CONSOLIDADO, 'Consolidado'),
        (CON_INCIDENCIAS, 'Con Incidencias'),
        (SIN_INCIDENCIAS, 'Sin Incidencias'),
        (FINALIZADO, 'Finalizado'),
        (ERROR, 'Error'),
        (CANCELADO, 'Cancelado'),
    ]
```

### Service Layer

```python
# apps/validador/services/cierre_service.py

class CierreService:
    
    TRANSICIONES_VALIDAS = {
        EstadoCierre.CARGA_ARCHIVOS: [EstadoCierre.CON_DISCREPANCIAS, EstadoCierre.SIN_DISCREPANCIAS],
        EstadoCierre.CON_DISCREPANCIAS: [EstadoCierre.SIN_DISCREPANCIAS, EstadoCierre.CARGA_ARCHIVOS],
        EstadoCierre.SIN_DISCREPANCIAS: [EstadoCierre.CONSOLIDADO, EstadoCierre.CARGA_ARCHIVOS],
        EstadoCierre.CONSOLIDADO: [EstadoCierre.CON_INCIDENCIAS, EstadoCierre.SIN_INCIDENCIAS],
        EstadoCierre.CON_INCIDENCIAS: [EstadoCierre.SIN_INCIDENCIAS],
        EstadoCierre.SIN_INCIDENCIAS: [EstadoCierre.FINALIZADO],
    }
    
    @classmethod
    def puede_generar_comparacion(cls, cierre):
        """Verifica si el cierre tiene todo listo para comparar."""
        # Verificar libro procesado
        # Verificar conceptos clasificados
        # Verificar novedades procesadas
        # Verificar headers mapeados
        pass
    
    @classmethod
    def generar_comparacion(cls, cierre, usuario):
        """Ejecuta la comparación y cambia estado."""
        pass
    
    @classmethod
    def consolidar(cls, cierre, usuario):
        """Cambia de SIN_DISCREPANCIAS a CONSOLIDADO."""
        pass
```

---

## Changelog

| Fecha | Cambio |
|-------|--------|
| 2026-01-15 | Simplificación de estados: 7 estados principales |
| 2026-01-15 | CARGA_ARCHIVOS como hub único de preparación |
| 2026-01-15 | SIN_DISCREPANCIAS requiere acción manual |
