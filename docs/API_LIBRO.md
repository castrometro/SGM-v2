# API Endpoints - Libro de Remuneraciones

Documentación de los endpoints para gestión del Libro de Remuneraciones con soporte para headers duplicados y clasificación automática.

## Base URL

```
/api/v1/validador/libro/
```

## Endpoints

### 1. Obtener Headers y Estado de Clasificación

Obtiene la lista de headers del libro con su estado de clasificación y sugerencias.

**Endpoint:** `GET /libro/{archivo_id}/headers/`

**Response:**
```json
{
  "headers_total": 45,
  "headers_clasificados": 42,
  "progreso": 93,
  "tiene_duplicados": true,
  "headers": ["RUT", "NOMBRE", "SUELDO", "BONO", "BONO.1", "..."],
  "conceptos": [
    {
      "id": 1,
      "header_original": "BONO",
      "header_pandas": "BONO",
      "ocurrencia": 1,
      "es_duplicado": true,
      "categoria": "haberes_imponibles",
      "categoria_display": "Haberes Imponibles",
      "es_identificador": false,
      "orden": 12,
      "clasificado": true,
      "sugerencia": null
    },
    {
      "id": 2,
      "header_original": "BONO",
      "header_pandas": "BONO.1",
      "ocurrencia": 2,
      "es_duplicado": true,
      "categoria": null,
      "categoria_display": null,
      "es_identificador": false,
      "orden": 13,
      "clasificado": false,
      "sugerencia": {
        "categoria": "haberes_no_imponibles",
        "es_identificador": false,
        "frecuencia": 3
      }
    }
  ]
}
```

**Campos importantes:**

- `tiene_duplicados`: Indica si hay headers duplicados en el archivo
- `sugerencia`: Presente solo en conceptos no clasificados, basada en historial
- `header_pandas`: Nombre como pandas lo lee (con .1, .2 para duplicados)
- `ocurrencia`: Número de ocurrencia si es duplicado (1, 2, 3...)

---

### 2. Obtener Conceptos Pendientes

Obtiene solo los conceptos pendientes de clasificación con sus sugerencias.

**Endpoint:** `GET /libro/{archivo_id}/pendientes/`

**Response:**
```json
{
  "count": 3,
  "conceptos": [
    {
      "id": 45,
      "header": "BONO.1",
      "header_original": "BONO",
      "header_pandas": "BONO.1",
      "ocurrencia": 2,
      "es_duplicado": true,
      "orden": 13,
      "categoria": null,
      "sugerencia": {
        "categoria": "haberes_no_imponibles",
        "es_identificador": false,
        "frecuencia": 3
      }
    },
    {
      "id": 46,
      "header": "BONO ESPECIAL",
      "header_original": "BONO ESPECIAL",
      "header_pandas": "BONO ESPECIAL",
      "ocurrencia": 1,
      "es_duplicado": false,
      "orden": 14,
      "categoria": null,
      "sugerencia": null
    }
  ]
}
```

---

### 3. Clasificar Conceptos Manualmente

Clasifica uno o más conceptos del libro.

**Endpoint:** `POST /libro/{archivo_id}/clasificar/`

**Request Body:**
```json
{
  "clasificaciones": [
    {
      "header": "BONO.1",
      "ocurrencia": 2,
      "categoria": "haberes_no_imponibles",
      "es_identificador": false
    },
    {
      "header": "AFP",
      "ocurrencia": 1,
      "categoria": "descuentos_legales",
      "es_identificador": false
    }
  ]
}
```

**Response:**
```json
{
  "clasificados": 2,
  "total": 45,
  "progreso": 96,
  "listo_para_procesar": false
}
```

**Notas:**

- `header` debe ser el `header_pandas` (con sufijo si es duplicado)
- `ocurrencia` es opcional, por defecto es 1
- Si todos los headers están clasificados, `listo_para_procesar` será `true`

---

### 4. Clasificar Automáticamente

Aplica automáticamente clasificaciones basadas en el historial del cliente/ERP.

**Endpoint:** `POST /libro/{archivo_id}/clasificar-auto/`

**Request Body:** (vacío)

**Response:**
```json
{
  "clasificados_auto": 15,
  "total_clasificados": 42,
  "total_headers": 45,
  "listo_para_procesar": false,
  "message": "Se clasificaron automáticamente 15 conceptos"
}
```

**Descripción:**

Este endpoint busca en el historial de clasificaciones del mismo cliente/ERP y aplica automáticamente las clasificaciones más frecuentes a conceptos pendientes.

**Ejemplo de lógica:**

```
Si en archivos anteriores se clasificó:
- "BONO" -> "haberes_imponibles" (10 veces)
- "BONO" -> "haberes_no_imponibles" (2 veces)

Entonces al encontrar "BONO" sin clasificar:
  -> Se clasifica automáticamente como "haberes_imponibles"
```

---

### 5. Extraer Headers (Asíncrono)

Inicia la extracción de headers del archivo (tarea asíncrona Celery).

**Endpoint:** `POST /libro/{archivo_id}/extraer/`

**Response:**
```json
{
  "task_id": "abc123-def456-...",
  "message": "Extracción de headers iniciada"
}
```

**Status Code:** `202 Accepted`

**Notas:**

- Tarea asíncrona que procesa el archivo Excel
- Detecta y registra headers duplicados
- Crea registros ConceptoLibro para cada header
- Cambiar estado del archivo de `subido` a `pendiente_clasificacion`

---

### 6. Procesar Libro (Asíncrono)

Inicia el procesamiento completo del libro (tarea asíncrona Celery).

**Endpoint:** `POST /libro/{archivo_id}/procesar/`

**Response:**
```json
{
  "task_id": "xyz789-abc123-...",
  "message": "Procesamiento del libro iniciado"
}
```

**Status Code:** `202 Accepted`

**Prerequisito:** Todos los headers deben estar clasificados.

**Error si faltan clasificaciones:**
```json
{
  "error": "Faltan 3 headers por clasificar"
}
```

**Status Code:** `400 Bad Request`

---

### 7. Obtener Progreso de Procesamiento

Obtiene el progreso del procesamiento del libro.

**Endpoint:** `GET /libro/{archivo_id}/progreso/`

**Response:**
```json
{
  "estado": "procesando",
  "progreso": 50,
  "empleados_procesados": 1234,
  "mensaje": "Procesando empleados..."
}
```

**Estados posibles:**

- `procesando`: Procesamiento en curso
- `completado`: Procesamiento finalizado exitosamente
- `error`: Error durante el procesamiento

---

### 8. Listar Empleados Procesados

Lista los empleados del libro ya procesados.

**Endpoint:** `GET /libro/{archivo_id}/empleados/`

**Query Params:**

- `page`: Número de página (default: 1)
- `page_size`: Tamaño de página (default: 100, max: 1000)

**Response:**
```json
{
  "count": 2456,
  "next": "http://api.../libro/123/empleados/?page=2",
  "previous": null,
  "results": [
    {
      "id": 1,
      "rut": "12345678-9",
      "nombre": "Juan Pérez",
      "cargo": "Analista",
      "total_haberes_imponibles": 1500000.00,
      "total_descuentos_legales": 180000.00,
      "total_liquido": 1320000.00
    }
  ]
}
```

---

## Categorías Disponibles

```python
CATEGORIAS = {
    'haberes_imponibles': 'Haberes Imponibles',
    'haberes_no_imponibles': 'Haberes No Imponibles',
    'descuentos_legales': 'Descuentos Legales',
    'otros_descuentos': 'Otros Descuentos',
    'aportes_patronales': 'Aportes Patronales',
    'info_adicional': 'Información Adicional',
    'identificador': 'Identificador (RUT, etc.)',
    'ignorar': 'Ignorar',
}
```

---

## Flujo de Trabajo Completo

```
1. POST /libro/{id}/extraer/
   └─> Retorna task_id
   └─> Archivo pasa a estado 'extrayendo_headers'
   └─> Detecta duplicados y crea ConceptoLibro
   └─> Archivo pasa a estado 'pendiente_clasificacion'

2. GET /libro/{id}/pendientes/
   └─> Obtiene conceptos sin clasificar con sugerencias

3. (Opcional) POST /libro/{id}/clasificar-auto/
   └─> Clasifica automáticamente según historial
   
   O bien
   
   POST /libro/{id}/clasificar/
   └─> Clasifica manualmente uno por uno o en lote

4. (Repetir paso 2-3 hasta clasificar todos)

5. POST /libro/{id}/procesar/
   └─> Retorna task_id
   └─> Archivo pasa a estado 'procesando'
   └─> Crea EmpleadoLibro para cada empleado
   └─> Archivo pasa a estado 'procesado'

6. GET /libro/{id}/empleados/
   └─> Lista empleados procesados con totales
```

---

## Ejemplo de Uso con cURL

### Clasificación automática

```bash
curl -X POST \
  https://api.sgm.com/v1/validador/libro/123/clasificar-auto/ \
  -H 'Authorization: Bearer {token}' \
  -H 'Content-Type: application/json'
```

### Clasificación manual

```bash
curl -X POST \
  https://api.sgm.com/v1/validador/libro/123/clasificar/ \
  -H 'Authorization: Bearer {token}' \
  -H 'Content-Type: application/json' \
  -d '{
    "clasificaciones": [
      {
        "header": "BONO.1",
        "ocurrencia": 2,
        "categoria": "haberes_no_imponibles",
        "es_identificador": false
      }
    ]
  }'
```

---

## Errores Comunes

### 400 Bad Request - Headers no clasificados

```json
{
  "error": "Faltan 3 headers por clasificar"
}
```

**Solución:** Clasificar todos los headers antes de procesar.

### 400 Bad Request - Categoría inválida

```json
{
  "error": "Categoría inválida: 'haberes_invalidos'"
}
```

**Solución:** Usar una de las categorías válidas listadas arriba.

### 400 Bad Request - Archivo no es libro

```json
{
  "error": "El archivo no es de tipo libro_remuneraciones"
}
```

**Solución:** Verificar que el tipo del ArchivoERP sea `libro_remuneraciones`.

### 400 Bad Request - Estado no permite clasificación

```json
{
  "error": "No se puede clasificar en estado 'procesado'"
}
```

**Solución:** La clasificación solo se permite en estados `pendiente_clasificacion` o `listo`.
