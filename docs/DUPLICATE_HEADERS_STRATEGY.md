# Estrategia de Manejo de Headers Duplicados en Libro de Remuneraciones

## Problema

Cuando los ERPs (como Talana) exportan el Libro de Remuneraciones a Excel, pueden existir **headers duplicados**. Por ejemplo:

```
RUT | NOMBRE | BONO | BONO | BONO | AFP | ...
```

Esto ocurre cuando un concepto (como "BONO") tiene múltiples columnas para diferentes tipos o períodos.

## Solución Implementada

### 1. Detección de Duplicados (Pandas)

Cuando pandas lee un archivo Excel con headers duplicados, automáticamente los renombra agregando sufijos:

```python
# Original Excel:
["RUT", "BONO", "BONO", "BONO"]

# Pandas lee como:
["RUT", "BONO", "BONO.1", "BONO.2"]
```

### 2. Modelo ConceptoLibro Actualizado

Se agregaron campos para trackear duplicados:

```python
class ConceptoLibro(models.Model):
    # Header original del Excel
    header_original = models.CharField(...)  # "BONO"
    
    # Header como lo lee pandas (con sufijo si es duplicado)
    header_pandas = models.CharField(...)    # "BONO.1"
    
    # Número de ocurrencia
    ocurrencia = models.PositiveIntegerField(default=1)  # 2
    
    # Flag de duplicado
    es_duplicado = models.BooleanField(default=False)  # True
    
    # Clasificación (puede ser diferente para cada ocurrencia)
    categoria = models.CharField(...)
```

**Constraint único**: `(cliente, erp, header_original, ocurrencia)` - permite múltiples "BONO" pero diferenciados por ocurrencia.

### 3. Proceso de Extracción de Headers

```python
# En TalanaLibroParser.extraer_headers()

1. Lee el Excel con pandas
2. Analiza las columnas detectando duplicados:
   - "BONO"   -> HeaderInfo(original="BONO", pandas_name="BONO", ocurrencia=1, es_duplicado=True)
   - "BONO.1" -> HeaderInfo(original="BONO", pandas_name="BONO.1", ocurrencia=2, es_duplicado=True)
   - "BONO.2" -> HeaderInfo(original="BONO", pandas_name="BONO.2", ocurrencia=3, es_duplicado=True)

3. Crea/actualiza ConceptoLibro para cada header:
   - Cliente X, ERP Talana, "BONO", ocurrencia=1
   - Cliente X, ERP Talana, "BONO", ocurrencia=2
   - Cliente X, ERP Talana, "BONO", ocurrencia=3
```

### 4. Clasificación de Conceptos

El analista puede clasificar cada ocurrencia de forma independiente:

```
BONO (#1) -> "Haberes Imponibles" (Bono de producción)
BONO (#2) -> "Haberes No Imponibles" (Bono de movilización)
BONO (#3) -> "Haberes Imponibles" (Bono de cumplimiento)
```

### 5. Mapeo Durante Procesamiento

Al procesar el libro, el servicio:

1. Crea un diccionario `{header_pandas: ConceptoLibro}`:
   ```python
   {
       "BONO": concepto_bono_1,
       "BONO.1": concepto_bono_2,
       "BONO.2": concepto_bono_3,
   }
   ```

2. Al parsear cada fila, usa el `header_pandas` para buscar la clasificación correcta

3. Almacena en `EmpleadoLibro.datos_json` con keys únicos:
   ```json
   {
     "haberes_imponibles": {
       "BONO (#1)": 150000,
       "BONO (#3)": 80000,
       "total": 230000
     },
     "haberes_no_imponibles": {
       "BONO (#2)": 50000,
       "total": 50000
     }
   }
   ```

## Clasificación Automática

### Sugerencias Basadas en Historial

El sistema ofrece **sugerencias automáticas** basadas en clasificaciones previas del mismo cliente/ERP:

```python
# Si previamente se clasificó:
Cliente X, Talana, "BONO" -> "haberes_imponibles" (5 veces)

# Al encontrar "BONO" nuevamente:
Sugerencia: {
    "categoria": "haberes_imponibles",
    "frecuencia": 5
}
```

### Endpoint de Clasificación Automática

```
POST /api/v1/validador/libro/{archivo_id}/clasificar-auto/
```

Este endpoint:
1. Busca conceptos sin clasificar
2. Busca en el historial clasificaciones del mismo `header_original`
3. Aplica automáticamente la clasificación más frecuente
4. Retorna cantidad de conceptos clasificados

## Flujo Completo

```
1. SUBIR ARCHIVO
   └─> ArchivoERP creado con estado='subido'

2. EXTRAER HEADERS (async)
   └─> Detecta duplicados
   └─> Crea ConceptoLibro para cada header (con ocurrencia)
   └─> Estado='pendiente_clasificacion'

3. CLASIFICAR CONCEPTOS
   a) Ver pendientes con sugerencias
      GET /libro/{id}/pendientes/
   
   b) Aplicar clasificación automática (opcional)
      POST /libro/{id}/clasificar-auto/
   
   c) Clasificar manualmente los restantes
      POST /libro/{id}/clasificar/
      Body: { clasificaciones: [...] }
   
   └─> Cuando todos clasificados: estado='listo'

4. PROCESAR LIBRO (async)
   └─> Lee Excel
   └─> Mapea headers usando pandas_name
   └─> Crea EmpleadoLibro para cada empleado
   └─> Estado='procesado'
```

## Interfaz de Usuario

La UI muestra:

- ✅ **Badge "Tiene duplicados"** si el archivo contiene headers duplicados
- 🔢 **Badge con número de ocurrencia** para cada header duplicado (ej: "#2")
- ✨ **Badge "Sugerencia"** para conceptos con clasificación sugerida
- 📊 **Barra de progreso** de clasificación
- 🤖 **Botón "Clasificar Automáticamente"** para aplicar todas las sugerencias

## Ejemplos de Uso

### Caso 1: Tres columnas BONO diferentes

```
Excel: RUT | BONO | BONO | BONO

Pandas: RUT | BONO | BONO.1 | BONO.2

ConceptoLibro:
- (header_original="BONO", header_pandas="BONO", ocurrencia=1, es_duplicado=True)
- (header_original="BONO", header_pandas="BONO.1", ocurrencia=2, es_duplicado=True)
- (header_original="BONO", header_pandas="BONO.2", ocurrencia=3, es_duplicado=True)

Clasificación:
- BONO (#1) -> haberes_imponibles
- BONO (#2) -> haberes_no_imponibles
- BONO (#3) -> haberes_imponibles

EmpleadoLibro.datos_json:
{
  "haberes_imponibles": {
    "BONO (#1)": 100000,
    "BONO (#3)": 50000,
    "total": 150000
  },
  "haberes_no_imponibles": {
    "BONO (#2)": 30000,
    "total": 30000
  }
}
```

### Caso 2: Headers únicos (sin duplicados)

```
# Headers originales del Excel (incluye datos de empleado)
Excel: RUT | NOMBRE | SUELDO | AFP | ISAPRE

# El parser detecta que RUT y NOMBRE son datos de empleado
# Solo se crean ConceptoLibro para conceptos monetarios:

ConceptoLibro:
- (header_original="SUELDO", header_pandas="SUELDO", ocurrencia=1, es_duplicado=False)
- (header_original="AFP", header_pandas="AFP", ocurrencia=1, es_duplicado=False)
- (header_original="ISAPRE", header_pandas="ISAPRE", ocurrencia=1, es_duplicado=False)

Clasificación (solo conceptos monetarios):
- SUELDO -> haberes_imponibles
- AFP -> descuentos_legales
- ISAPRE -> descuentos_legales

# RUT y NOMBRE se usarán posteriormente al procesar el libro
# para crear el registro EmpleadoLibro
```

## Migración

La migración `0003_conceptolibro_duplicate_headers.py`:

1. Agrega campos: `header_pandas`, `ocurrencia`, `es_duplicado`
2. Cambia constraint único a `(cliente, erp, header_original, ocurrencia)`
3. Agrega índice en `header_pandas`
4. Valores por defecto: `ocurrencia=1`, `es_duplicado=False`, `header_pandas=""`

**Compatibilidad**: Los registros existentes mantienen `ocurrencia=1` y `es_duplicado=False`, por lo que siguen funcionando sin cambios.

## Ventajas

1. **Flexibilidad**: Cada ocurrencia de un header duplicado puede tener clasificación diferente
2. **Historial**: El sistema recuerda clasificaciones previas y las sugiere
3. **Automatización**: Clasificación automática reduce trabajo manual
4. **Transparencia**: El usuario ve claramente qué headers están duplicados
5. **Sin pérdida de datos**: Cada columna duplicada se procesa correctamente

## Consideraciones

- Si un cliente tiene headers que varían frecuentemente, las sugerencias pueden ser menos útiles
- El analista debe revisar las sugerencias antes de aplicarlas automáticamente
- Los headers muy genéricos (como "BONO") requieren más atención en la clasificación
