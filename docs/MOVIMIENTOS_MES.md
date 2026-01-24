# 📋 Movimientos del Mes - Documentación

> Procesamiento de archivos de movimientos (altas, bajas, ausentismos, vacaciones) desde ERP.

## Índice

1. [Descripción General](#descripción-general)
2. [Formato por ERP](#formato-por-erp)
   - [Talana](#talana)
3. [Modelo de Datos](#modelo-de-datos)
4. [Flujo de Procesamiento](#flujo-de-procesamiento)
5. [Reglas de Negocio](#reglas-de-negocio)
6. [API Endpoints](#api-endpoints)

---

## Descripción General

El archivo **Movimientos del Mes** contiene información sobre cambios en la dotación y ausencias del personal durante el período de cierre:

| Tipo | Descripción |
|------|-------------|
| **Alta** | Nuevo ingreso de empleado |
| **Baja** | Desvinculación/Finiquito |
| **Licencia** | Licencia médica, maternal, etc. |
| **Vacaciones** | Días de vacaciones |
| **Permiso** | Permisos con/sin goce de sueldo |
| **Ausencia** | Ausencias no justificadas |

### Propósito en el Flujo de Cierre

1. Validar que los movimientos informados por el cliente (novedades) coincidan con los del ERP
2. Detectar discrepancias (ej: cliente informa baja pero ERP no la tiene)
3. Generar alertas para revisión manual

---

## Formato por ERP

### Talana

**Archivo:** Excel (.xlsx)  
**Headers:** Fila 3 (índice 2 en pandas)  
**Datos:** Desde fila 4 (índice 3 en pandas)

#### Hoja: "Altas y Bajas"

| Columna Excel | Campo Modelo | Tipo | Descripción |
|---------------|--------------|------|-------------|
| Nombre | `nombre` | string | Nombre completo del empleado |
| Rut | `rut` | string | RUT con formato (ej: 12.345.678-9) |
| Fecha Ingreso | `fecha_inicio` | date | Fecha de alta (solo para tipo=alta) |
| Fecha Retiro | `fecha_fin` | date | Fecha de baja (solo para tipo=baja) |
| Tipo Contrato | `tipo_contrato` | string | "Plazo Fijo" o "Indefinido" |
| Alta / Baja | `tipo` | string | "alta" o "baja" |
| Motivo | `causal` | string | Motivo de la baja (puede ser null) |

**Ejemplo de datos:**

| Nombre | Rut | Fecha Ingreso | Fecha Retiro | Tipo Contrato | Alta / Baja | Motivo |
|--------|-----|---------------|--------------|---------------|-------------|--------|
| Juan Pérez | 12.345.678-9 | 2026-01-15 | | Indefinido | alta | |
| María López | 11.222.333-4 | | 2026-01-20 | Indefinido | baja | Renuncia voluntaria |
| Pedro Soto | 10.111.222-3 | | 2026-01-31 | Plazo Fijo | baja | | 

> ⚠️ **Regla especial:** El último registro (Pedro Soto) NO se considera baja porque es "Plazo Fijo" sin motivo (vencimiento de contrato).

#### Hoja: "Ausentismos"

| Columna Excel | Campo Modelo | Tipo | Descripción |
|---------------|--------------|------|-------------|
| Nombre | `nombre` | string | Nombre completo |
| Rut | `rut` | string | RUT del empleado |
| Fecha Inicio Ausencia | `fecha_inicio` | date | Inicio del ausentismo |
| Fecha Fin Ausencia | `fecha_fin` | date | Fin del ausentismo |
| Dias | `dias` | int | Cantidad de días |
| Tipo de Ausentismo | `tipo` + `tipo_licencia` | string | Ver mapeo abajo |

**Mapeo de Tipo de Ausentismo:**

| Valor Excel (case insensitive) | `tipo` | `tipo_licencia` |
|-------------------------------|--------|-----------------|
| Permiso con goce | `permiso` | `con_goce` |
| Permiso sin goce | `permiso` | `sin_goce` |
| Licencia Medica | `licencia` | `medica` |
| Licencia Maternal | `licencia` | `maternal` |
| Ausencia NO Justificada | `ausencia` | _(vacío)_ |

**Ejemplo de datos:**

| Nombre | Rut | Fecha Inicio Ausencia | Fecha Fin Ausencia | Dias | Tipo de Ausentismo |
|--------|-----|-----------------------|--------------------|------|--------------------|
| Ana Ruiz | 13.444.555-6 | 2026-01-05 | 2026-01-10 | 6 | Licencia Medica |
| Carlos Vega | 14.555.666-7 | 2026-01-15 | 2026-01-15 | 1 | Permiso sin goce |

#### Hoja: "Vacaciones"

| Columna Excel | Campo Modelo | Tipo | Descripción |
|---------------|--------------|------|-------------|
| Nombre | `nombre` | string | Nombre completo |
| Rut | `rut` | string | RUT del empleado |
| Fecha Inicial | `fecha_inicio` | date | Inicio vacaciones |
| Fecha Fin Vacaciones | `fecha_fin` | date | Fin vacaciones |
| Cantidad de Dias | `dias` | int | Días de vacaciones |

**Tipo fijo:** `vacaciones`

**Ejemplo de datos:**

| Nombre | Rut | Fecha Inicial | Fecha Fin Vacaciones | Cantidad de Dias |
|--------|-----|---------------|----------------------|------------------|
| Luis Mora | 15.666.777-8 | 2026-01-10 | 2026-01-24 | 15 |

---

## Modelo de Datos

### MovimientoMes

```python
class MovimientoMes(models.Model):
    """Registro de movimiento del mes extraído del ERP."""
    
    TIPO_CHOICES = [
        ('alta', 'Alta/Ingreso'),
        ('baja', 'Baja/Finiquito'),
        ('licencia', 'Licencia Médica'),
        ('vacaciones', 'Vacaciones'),
        ('permiso', 'Permiso'),
        ('ausencia', 'Ausencia'),
        ('otro', 'Otro'),
    ]
    
    # Relaciones
    cierre = FK('Cierre')
    archivo_erp = FK('ArchivoERP', null=True)  # Trazabilidad
    
    # Tipo de movimiento
    tipo = CharField(choices=TIPO_CHOICES)
    
    # Datos del empleado
    rut = CharField(max_length=12)
    nombre = CharField(max_length=200)
    
    # Fechas
    fecha_inicio = DateField(null=True)  # Ingreso o inicio ausencia
    fecha_fin = DateField(null=True)     # Retiro o fin ausencia
    dias = PositiveIntegerField(null=True)
    
    # Información adicional
    tipo_contrato = CharField(max_length=50, blank=True)  # Plazo Fijo, Indefinido
    causal = CharField(max_length=200, blank=True)        # Motivo baja
    tipo_licencia = CharField(max_length=100, blank=True) # medica, maternal, con_goce, sin_goce
    
    # Metadata
    hoja_origen = CharField(max_length=100)  # Nombre de la hoja Excel
    datos_raw = JSONField(default=dict)      # Fila completa para debug
```

---

## Flujo de Procesamiento

```
┌─────────────────────────────────────────────────────────────────┐
│                    SUBIDA DE ARCHIVO                            │
│  POST /api/v1/validador/archivos-erp/                          │
│  { cierre_id, tipo: "movimientos_mes", archivo: File }         │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                 DISPARAR TAREA CELERY                           │
│  procesar_archivo_erp.delay(archivo_id)                        │
│  Estado: SUBIDO → PROCESANDO                                    │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│              OBTENER ESTRATEGIA ERP                             │
│  strategy = ERPFactory.get_strategy(cierre.cliente.erp.codigo) │
│  # Para Talana: TalanaStrategy                                  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│              PROCESAR CADA HOJA                                 │
│                                                                 │
│  1. "Altas y Bajas"                                            │
│     - Leer desde fila 3 (headers) y 4 (datos)                  │
│     - Aplicar regla: ignorar baja + plazo fijo + sin motivo    │
│     - Crear MovimientoMes por cada registro válido             │
│                                                                 │
│  2. "Ausentismos"                                              │
│     - Mapear tipo de ausentismo a tipo + tipo_licencia         │
│     - Crear MovimientoMes                                       │
│                                                                 │
│  3. "Vacaciones"                                                │
│     - Tipo fijo: "vacaciones"                                  │
│     - Crear MovimientoMes                                       │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│              ACTUALIZAR ARCHIVO Y CIERRE                        │
│  archivo.estado = PROCESADO                                     │
│  archivo.registros_procesados = count                           │
│  archivo.hojas_encontradas = ['Altas y Bajas', ...]            │
└─────────────────────────────────────────────────────────────────┘
```

### Estados del Archivo

| Estado | Descripción |
|--------|-------------|
| `subido` | Archivo recién subido, pendiente de procesar |
| `procesando` | Tarea Celery ejecutándose |
| `procesado` | Procesamiento exitoso |
| `error` | Error durante procesamiento |

---

## Reglas de Negocio

### RN-001: Vencimiento de Contrato Plazo Fijo

**Condición:** 
- `Alta / Baja` = "baja"
- `Tipo Contrato` = "Plazo Fijo"  
- `Motivo` = null o vacío

**Acción:** NO crear registro de MovimientoMes

**Justificación:** El vencimiento de un contrato a plazo fijo no es una baja propiamente tal. El empleado puede ser recontratado al mes siguiente, por lo que no debe aparecer como baja en los reportes.

```python
# Pseudo-código
if row['Alta / Baja'].lower() == 'baja':
    if row['Tipo Contrato'] == 'Plazo Fijo':
        if not row['Motivo'] or row['Motivo'].strip() == '':
            continue  # Ignorar este registro
```

### RN-002: Normalización de RUT

- Eliminar puntos y guión
- Convertir a mayúsculas
- Validar dígito verificador (warning si inválido, no bloquear)

### RN-003: Normalización de Fechas

- Soportar formatos: `DD-MM-YYYY`, `DD/MM/YYYY`, `YYYY-MM-DD`
- Fechas inválidas generan warning pero no bloquean

### RN-004: Mapeo Case-Insensitive

Los valores de "Tipo de Ausentismo" se comparan ignorando mayúsculas/minúsculas:
- "LICENCIA MEDICA" → `licencia`
- "licencia medica" → `licencia`
- "Licencia Medica" → `licencia`

---

## API Endpoints

### Subir Archivo de Movimientos

```http
POST /api/v1/validador/archivos-erp/
Content-Type: multipart/form-data

cierre_id: 123
tipo: movimientos_mes
archivo: <file.xlsx>
```

**Response (201):**
```json
{
  "id": 456,
  "cierre": 123,
  "tipo": "movimientos_mes",
  "tipo_display": "Movimientos del Mes",
  "estado": "subido",
  "archivo": "/media/archivos/2026/01/movimientos.xlsx",
  "fecha_subida": "2026-01-24T21:00:00Z",
  "task_id": "abc123..."
}
```

### Consultar Estado de Procesamiento

```http
GET /api/v1/validador/archivos-erp/{id}/
```

**Response (200):**
```json
{
  "id": 456,
  "estado": "procesado",
  "hojas_encontradas": ["Altas y Bajas", "Ausentismos", "Vacaciones"],
  "registros_procesados": 45,
  "error_mensaje": null
}
```

### Obtener Movimientos por Cierre

```http
GET /api/v1/validador/movimientos/?cierre_id=123
```

**Response (200):**
```json
{
  "count": 45,
  "results": [
    {
      "id": 1,
      "tipo": "alta",
      "tipo_display": "Alta/Ingreso",
      "rut": "12345678-9",
      "nombre": "Juan Pérez",
      "fecha_inicio": "2026-01-15",
      "fecha_fin": null,
      "dias": null,
      "tipo_contrato": "Indefinido",
      "causal": "",
      "hoja_origen": "Altas y Bajas"
    },
    {
      "id": 2,
      "tipo": "licencia",
      "tipo_display": "Licencia Médica",
      "rut": "13444555-6",
      "nombre": "Ana Ruiz",
      "fecha_inicio": "2026-01-05",
      "fecha_fin": "2026-01-10",
      "dias": 6,
      "tipo_licencia": "medica",
      "hoja_origen": "Ausentismos"
    }
  ]
}
```

### Resumen de Movimientos por Tipo

```http
GET /api/v1/validador/movimientos/resumen/?cierre_id=123
```

**Response (200):**
```json
{
  "cierre_id": 123,
  "total": 45,
  "por_tipo": {
    "alta": 5,
    "baja": 3,
    "licencia": 12,
    "vacaciones": 20,
    "permiso": 4,
    "ausencia": 1
  },
  "hojas_procesadas": ["Altas y Bajas", "Ausentismos", "Vacaciones"]
}
```

---

## Comparación con MovimientoAnalista

El modelo `MovimientoAnalista` almacena movimientos informados por el cliente (archivos del analista). La comparación entre `MovimientoMes` (ERP) y `MovimientoAnalista` permite detectar discrepancias:

| Discrepancia | Descripción |
|--------------|-------------|
| Solo en ERP | Movimiento existe en ERP pero cliente no lo informó |
| Solo en Cliente | Cliente informa movimiento que no está en ERP |
| Fechas distintas | Mismo movimiento pero con fechas diferentes |
| Días distintos | Misma licencia/vacación pero cantidad de días difiere |

Esta comparación se realiza en la tarea `ejecutar_comparacion` del flujo de cierre.
