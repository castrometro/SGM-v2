# Archivo de Novedades del Cliente

> Documentación del formato, procesamiento y almacenamiento del archivo de Novedades.

## Índice
- [Contexto](#contexto)
- [Formato del Archivo](#formato-del-archivo)
- [Flujo en el Sistema](#flujo-en-el-sistema)
- [Modelos de Datos](#modelos-de-datos)
- [API Endpoints](#api-endpoints)
- [Archivos Relacionados](#archivos-relacionados)

---

## Contexto

El archivo de **Novedades** es proporcionado por el cliente y contiene los movimientos de nómina que el cliente espera ver reflejados en el Libro de Remuneraciones.

### Alcance de este Módulo

Este módulo cubre **únicamente**:
1. Carga del archivo de novedades
2. Extracción de headers (items)
3. Mapeo de items del cliente a conceptos del ERP
4. Procesamiento y creación de registros

⚠️ **La comparación Libro vs Novedades y detección de discrepancias es un módulo separado.**

### Prerequisito

El archivo de novedades solo puede cargarse **DESPUÉS** de que el Libro de Remuneraciones ha sido procesado. Esto porque:
- Se necesitan los conceptos clasificados del libro para poder mapear las novedades
- El mapeo requiere conocer los conceptos disponibles del cliente

---

## Formato del Archivo

### Estructura Esperada

El archivo de novedades es un Excel (`.xlsx`, `.xls`) o CSV (`.csv`) con la siguiente estructura:

| Columna | Tipo | Obligatorio | Descripción |
|---------|------|-------------|-------------|
| **RUT** | String | ✅ Sí | RUT del empleado (formatos: `12345678-9`, `12.345.678-9`) |
| **Nombre** | String | No | Nombre completo del empleado (para referencia) |
| **[Item 1]** | Number | - | Monto del primer concepto/novedad |
| **[Item 2]** | Number | - | Monto del segundo concepto/novedad |
| **[Item N]** | Number | - | Monto del N-ésimo concepto/novedad |

### Ejemplo de Archivo

```
| RUT           | Nombre          | Bono Colación | Horas Extra | Gratificación |
|---------------|-----------------|---------------|-------------|---------------|
| 12.345.678-9  | Juan Pérez      | 50000         | 0           | 125000        |
| 11.222.333-4  | María González  | 50000         | 75000       | 125000        |
| 15.666.777-8  | Pedro Soto      | 0             | 0           | 125000        |
```

### Detección de Columnas

El sistema detecta automáticamente:

1. **Columna RUT**: Busca columnas que contengan "rut" en el nombre (case-insensitive)
2. **Columna Nombre**: Busca columnas que contengan "nombre" (opcional)
3. **Columnas de Items**: Todas las demás columnas se consideran items de novedades

### Columnas Ignoradas (no son items)

- `rut`
- `nombre`  
- `fecha`
- `periodo`

---

## Flujo en el Sistema

> **Patrón idéntico al Libro de Remuneraciones**: Subir → Extraer Headers → Mapear → Procesar

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      FLUJO DE ARCHIVO DE NOVEDADES                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  PREREQUISITO                                                               │
│  ┌──────────────────┐                                                       │
│  │ Libro ERP        │  El libro DEBE estar procesado                       │
│  │ PROCESADO ✓      │  (conceptos clasificados disponibles)                │
│  └────────┬─────────┘                                                       │
│           │                                                                 │
│           ▼                                                                 │
│  ┌──────────────────┐                                                       │
│  │ 1. SUBIR         │  Usuario sube Excel/CSV de novedades                 │
│  │    ARCHIVO       │  → ArchivoAnalista tipo='novedades'                  │
│  │                  │  → estado = 'subido'                                 │
│  └────────┬─────────┘                                                       │
│           │                                                                 │
│           ▼                                                                 │
│  ┌──────────────────┐                                                       │
│  │ 2. EXTRAER       │  Task Celery: extraer_headers_novedades              │
│  │    HEADERS       │  → Lee primera fila del archivo                      │
│  │                  │  → Identifica columnas de items                      │
│  │                  │  → estado = 'pendiente_mapeo'                        │
│  └────────┬─────────┘                                                       │
│           │                                                                 │
│           ▼                                                                 │
│  ┌──────────────────┐                                                       │
│  │ 3. MAPEAR        │  Usuario mapea items → conceptos ERP                 │
│  │    ITEMS         │  → Busca mapeos existentes del cliente               │
│  │                  │  → Items nuevos requieren mapeo manual               │
│  │                  │  → Crea MapeoItemNovedades                           │
│  │                  │  → estado = 'listo'                                  │
│  └────────┬─────────┘                                                       │
│           │                                                                 │
│           ▼                                                                 │
│  ┌──────────────────┐                                                       │
│  │ 4. PROCESAR      │  Task Celery: procesar_novedades                     │
│  │    ARCHIVO       │  → Lee cada fila del archivo                         │
│  │                  │  → Crea RegistroNovedades por cada item              │
│  │                  │  → Solo items con monto > 0                          │
│  │                  │  → estado = 'procesado'                              │
│  └────────┬─────────┘                                                       │
│           │                                                                 │
│           ▼                                                                 │
│  ┌──────────────────┐                                                       │
│  │ NOVEDADES        │  Listo para siguiente módulo                         │
│  │ PROCESADO ✓      │  (comparación - módulo separado)                     │
│  └──────────────────┘                                                       │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Estados del Archivo de Novedades

| Estado | Descripción | Siguiente Acción |
|--------|-------------|------------------|
| `subido` | Archivo cargado | Extraer headers |
| `extrayendo_headers` | Task en ejecución | Esperar |
| `pendiente_mapeo` | Headers extraídos, items detectados | Mapear items |
| `listo` | Todos los items mapeados | Procesar |
| `procesando` | Task creando registros | Esperar |
| `procesado` | Registros creados ✓ | Siguiente módulo |
| `error` | Error en algún paso | Revisar y reintentar |

### Comparación con Flujo del Libro

| Paso | Libro de Remuneraciones | Archivo de Novedades |
|------|-------------------------|----------------------|
| 1 | Subir archivo | Subir archivo |
| 2 | Extraer headers | Extraer headers (items) |
| 3 | Clasificar conceptos | Mapear items → conceptos |
| 4 | Procesar libro | Procesar novedades |
| Resultado | EmpleadoLibro + RegistroLibro | RegistroNovedades |

---

## Modelos de Datos

### ItemNovedades (headers extraídos)

Almacena los items detectados en el archivo (similar a ConceptoLibro).

```python
class ItemNovedades(models.Model):
    """
    Un item/header detectado en el archivo de novedades.
    Permite mapear antes de procesar.
    """
    
    archivo = ForeignKey(ArchivoAnalista)      # Archivo origen
    cliente = ForeignKey(Cliente)              # Cliente dueño
    nombre_original = CharField(max_length=200) # Nombre como aparece en archivo
    orden = PositiveIntegerField()             # Orden en el archivo (columna)
    
    # Mapeo (puede ser null si es nuevo)
    mapeo = ForeignKey(MapeoItemNovedades, null=True)
    
    class Meta:
        unique_together = ['archivo', 'nombre_original']
```

### MapeoItemNovedades

Mapeo persistente entre items del cliente y conceptos del ERP.

```python
class MapeoItemNovedades(models.Model):
    """
    Mapeo 1:1 reutilizable por cliente.
    Se crea una vez y se aplica automáticamente en futuros cierres.
    """
    
    cliente = ForeignKey(Cliente)              # Cliente dueño del mapeo
    nombre_novedades = CharField()             # Nombre como aparece en archivo
    concepto_erp = ForeignKey(ConceptoCliente) # Concepto del ERP al que mapea
    mapeado_por = ForeignKey(User)             # Usuario que creó el mapeo
    fecha_mapeo = DateTimeField()              # Cuándo se creó
    notas = TextField(blank=True)              # Notas opcionales
```

**Ubicación**: [backend/apps/validador/models/concepto.py](../../backend/apps/validador/models/concepto.py)

### RegistroNovedades

Datos finales procesados (similar a RegistroLibro).

```python
class RegistroNovedades(models.Model):
    """
    Un registro por cada combinación (empleado, item, monto).
    Se crea DESPUÉS del mapeo, durante el procesamiento.
    """
    
    cierre = ForeignKey(Cierre)                # Cierre al que pertenece
    rut_empleado = CharField(max_length=12)    # RUT del empleado
    nombre_empleado = CharField(blank=True)    # Nombre (referencia)
    item = ForeignKey(ItemNovedades)           # Item del archivo
    mapeo = ForeignKey(MapeoItemNovedades)     # Mapeo al concepto ERP
    monto = DecimalField()                     # Monto informado por cliente
```

**Ubicación**: [backend/apps/validador/models/empleado.py](../../backend/apps/validador/models/empleado.py)

---

## API Endpoints

### Extraer Headers

```bash
POST /api/v1/validador/archivos-analista/{id}/extraer_headers/
```

Inicia la extracción de headers del archivo de novedades.

### Obtener Items Sin Mapear

```bash
GET /api/v1/validador/archivos-analista/{id}/items_sin_mapear/

# Response
{
  "count": 3,
  "items": [
    {"nombre_original": "Bono Colación", "orden": 2},
    {"nombre_original": "HH.EE. 50%", "orden": 3},
    {"nombre_original": "Gratificación", "orden": 4}
  ]
}
```

### Mapear Items

```bash
POST /api/v1/validador/mapeos/crear_batch/
{
  "cliente_id": 1,
  "archivo_id": 123,
  "mapeos": [
    {"nombre_novedades": "Bono Colación", "concepto_erp_id": 45},
    {"nombre_novedades": "HH.EE. 50%", "concepto_erp_id": 67}
  ]
}
```

### Procesar Archivo

```bash
POST /api/v1/validador/archivos-analista/{id}/procesar/
```

Inicia el procesamiento (solo si todos los items están mapeados).

---

## Reglas de Procesamiento

| Regla | Descripción |
|-------|-------------|
| **Montos cero** | Se ignoran (no se crean registros para monto = 0) |
| **RUT vacío** | La fila se ignora completamente |
| **Monto inválido** | Se convierte a 0 (y se ignora) |
| **Item sin mapeo** | Error - todos deben estar mapeados antes de procesar |

---

## Ejemplo Completo

### 1. Archivo Subido

```csv
RUT,Nombre,Bono Colación,Horas Extra 50%,Gratificación
12.345.678-9,Juan Pérez,50000,0,125000
11.222.333-4,María González,50000,75000,125000
```

### 2. Headers Extraídos (ItemNovedades)

```python
ItemNovedades(nombre_original='Bono Colación', orden=2, mapeo=None)
ItemNovedades(nombre_original='Horas Extra 50%', orden=3, mapeo=None)
ItemNovedades(nombre_original='Gratificación', orden=4, mapeo=None)
```

### 3. Mapeos Creados

```python
MapeoItemNovedades(cliente=cliente, nombre_novedades='Bono Colación', concepto_erp=concepto_colacion)
MapeoItemNovedades(cliente=cliente, nombre_novedades='Horas Extra 50%', concepto_erp=concepto_hh_extra)
MapeoItemNovedades(cliente=cliente, nombre_novedades='Gratificación', concepto_erp=concepto_gratif)
```

### 4. Registros Procesados (RegistroNovedades)

```python
# Juan Pérez - 2 registros (monto > 0)
RegistroNovedades(rut='12.345.678-9', item=bono_colacion, monto=50000)
RegistroNovedades(rut='12.345.678-9', item=gratificacion, monto=125000)
# Horas Extra = 0, no se crea registro

# María González - 3 registros
RegistroNovedades(rut='11.222.333-4', item=bono_colacion, monto=50000)
RegistroNovedades(rut='11.222.333-4', item=horas_extra, monto=75000)
RegistroNovedades(rut='11.222.333-4', item=gratificacion, monto=125000)
```

### 5. Estado Final

- `ArchivoAnalista.estado = 'procesado'`
- Todos los items tienen mapeo
- Registros creados listos para comparación (módulo separado)

---

## Archivos Relacionados

### Backend

| Archivo | Descripción |
|---------|-------------|
| [models/empleado.py](../../backend/apps/validador/models/empleado.py) | Modelo `RegistroNovedades` |
| [models/concepto.py](../../backend/apps/validador/models/concepto.py) | Modelos `ItemNovedades`, `MapeoItemNovedades` |
| [tasks/procesar_analista.py](../../backend/apps/validador/tasks/procesar_analista.py) | Tasks de procesamiento |
| [views/concepto.py](../../backend/apps/validador/views/concepto.py) | ViewSet de mapeos |
| [serializers/concepto.py](../../backend/apps/validador/serializers/concepto.py) | Serializers de mapeo |

### Frontend

| Archivo | Descripción |
|---------|-------------|
| [constants/index.js](../../frontend/src/constants/index.js) | `TIPO_ARCHIVO_ANALISTA.NOVEDADES` |
| [hooks/useArchivos.js](../../frontend/src/features/validador/hooks/useArchivos.js) | Hook para archivos |

### Documentación

| Archivo | Descripción |
|---------|-------------|
| [libro-processing-instructions.md](../../.github/instructions/libro-processing-instructions.md) | Flujo del libro (patrón a seguir) |
| [SERVICE_LAYER.md](./SERVICE_LAYER.md) | Patrón de servicios |
