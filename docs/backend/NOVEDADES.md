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

El archivo de novedades es un **Excel** (`.xlsx`, `.xls`). También se acepta CSV como alternativa.

| Columna | Tipo | Obligatorio | Descripción |
|---------|------|-------------|-------------|
| **rut** | String | ✅ Sí | RUT del empleado (formatos: `12345678-9`, `12.345.678-9`) |
| **[Item 1]** | Number | - | Monto del primer concepto/novedad |
| **[Item 2]** | Number | - | Monto del segundo concepto/novedad |
| **[Item N]** | Number | - | Monto del N-ésimo concepto/novedad |

### Características del Formato

| Característica | Valor |
|----------------|-------|
| **Formato principal** | Excel (`.xlsx`, `.xls`) |
| **Formato alternativo** | CSV (`;` como separador) |
| **Primera fila** | Headers (nombres de items) |
| **Columna RUT** | Primera columna, nombre `rut` |
| **Montos vacíos** | Se interpretan como 0 |

### Ejemplo de Estructura (Excel)

| rut | Anticipo Manual | Dcto. Convenio FALP | Dcto. No Sindicalizado | Bono Colación | Horas Extra (M) |
|-----|-----------------|---------------------|------------------------|---------------|-----------------|
| 10000186-1 | | | | 50000 | |
| 10045847-0 | | 8800 | 20000 | 50000 | 75000 |
| 12408696-5 | 1253952 | 8800 | | | 12 |

### Items Comunes (ejemplos reales)

Los nombres de items varían según el cliente. Ejemplos típicos:

**Haberes:**
- `Anticipo Manual`, `Anticipo Bono Vacaciones`
- `Bono Colación`, `Bono Zona`, `Bono Especial`
- `Horas Extra (M)`, `Hora Producción Asegurada`
- `Comisión Venta`, `Comisiones Usados`
- `Incentivo Mensual`, `Incentivo Trimestral`
- `Gratificación`, `Semana Corrida (M)`

**Descuentos:**
- `Dcto. Convenio FALP`, `Dcto. No Sindicalizado`
- `Descuento Préstamo Empresa`, `Dcto. Varios`
- `Descuento Crédito Personal CCAF`
- `Descuento Seguro Salud`
- `Descuento por Leasing o Ahorro CCAF`

**Otros:**
- `Subsidio Licencia medica sobre tope`
- `Días Festivo y Domingo`
- `Cantidad Produccion Horas Mec.`

### Detección de Columnas

El sistema detecta automáticamente:

1. **Columna RUT**: Primera columna o columna que contenga "rut" en el nombre (case-insensitive)
2. **Columnas de Items**: Todas las demás columnas se consideran items de novedades

### Columnas Ignoradas (no son items)

```python
COLUMNAS_IGNORADAS = ['rut', 'nombre', 'fecha', 'periodo', 'observacion', 'observaciones']
```

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
rut;Anticipo Manual;Dcto. Convenio FALP;Descuento Préstamo Empresa;Bono Colación;Horas Extra (M)
10000186-1;;;;50000;
10045847-0;;8800;;50000;75000
12408696-5;1253952;8800;;;12
```

### 2. Headers Extraídos (ItemNovedades)

```python
ItemNovedades(nombre_original='Anticipo Manual', orden=1, mapeo=None)
ItemNovedades(nombre_original='Dcto. Convenio FALP', orden=2, mapeo=None)
ItemNovedades(nombre_original='Descuento Préstamo Empresa', orden=3, mapeo=None)
ItemNovedades(nombre_original='Bono Colación', orden=4, mapeo=None)
ItemNovedades(nombre_original='Horas Extra (M)', orden=5, mapeo=None)
```

### 3. Mapeos Creados

```python
# El usuario mapea cada nombre del cliente a un concepto del ERP
MapeoItemNovedades(cliente=cliente, nombre_novedades='Anticipo Manual', concepto_erp=concepto_anticipo)
MapeoItemNovedades(cliente=cliente, nombre_novedades='Dcto. Convenio FALP', concepto_erp=concepto_dcto_salud)
MapeoItemNovedades(cliente=cliente, nombre_novedades='Descuento Préstamo Empresa', concepto_erp=concepto_prestamo)
MapeoItemNovedades(cliente=cliente, nombre_novedades='Bono Colación', concepto_erp=concepto_colacion)
MapeoItemNovedades(cliente=cliente, nombre_novedades='Horas Extra (M)', concepto_erp=concepto_hh_extra)
```

### 4. Registros Procesados (RegistroNovedades)

```python
# 10000186-1 - 1 registro (solo Bono Colación tiene monto > 0)
RegistroNovedades(rut='10000186-1', item=bono_colacion, monto=50000)

# 10045847-0 - 3 registros
RegistroNovedades(rut='10045847-0', item=dcto_convenio, monto=8800)
RegistroNovedades(rut='10045847-0', item=bono_colacion, monto=50000)
RegistroNovedades(rut='10045847-0', item=horas_extra, monto=75000)

# 12408696-5 - 3 registros
RegistroNovedades(rut='12408696-5', item=anticipo_manual, monto=1253952)
RegistroNovedades(rut='12408696-5', item=dcto_convenio, monto=8800)
RegistroNovedades(rut='12408696-5', item=horas_extra, monto=12)
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
