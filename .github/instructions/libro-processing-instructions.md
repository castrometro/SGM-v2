# Procesamiento del Libro de Remuneraciones

> Guía técnica para el procesamiento y almacenamiento de datos del Libro de Remuneraciones.

## Arquitectura Medallion

El sistema usa una arquitectura de datos en capas (medallion) para procesar la información:

```
📥 BRONCE (Raw)              📊 PLATA (Validado)           🏆 ORO (Consolidado)
─────────────────────        ─────────────────────        ─────────────────────
RegistroLibro                Después de comparar          Modelo final con
RegistroNovedades            y resolver discrepancias     totales y resumen
```

### Capa Bronce: Datos Crudos
- `RegistroLibro`: Items extraídos del Libro de Remuneraciones
- `RegistroNovedades`: Items del archivo de Novedades del cliente
- Sin transformaciones, solo validación básica

### Capa Plata: Datos Validados
- Comparación Libro vs Novedades
- Resolución de discrepancias
- Datos verificados y aprobados

### Capa Oro: Datos Consolidados
- Totales por empleado
- Resúmenes por categoría
- Datos listos para reportería

---

## Modelos de Datos

### `EmpleadoLibro`
Almacena la identificación básica de cada empleado encontrado en el libro.

```python
class EmpleadoLibro(models.Model):
    cierre = FK(Cierre)
    archivo_erp = FK(ArchivoERP)
    rut = CharField()       # Obligatorio
    nombre = CharField()    # Obligatorio
```

**Notas:**
- Solo campos de identificación
- Sin totales (se calculan en capa Oro)
- Sin datos opcionales como cargo, centro_costo, área (pueden agregarse a futuro)

### `RegistroLibro`
Un registro por cada concepto-valor de cada empleado.

```python
class RegistroLibro(models.Model):
    cierre = FK(Cierre)
    empleado = FK(EmpleadoLibro)
    concepto = FK(ConceptoLibro)
    monto = DecimalField()
```

**Notas:**
- Solo se crean registros si `monto > 0`
- Estructura espejo de `RegistroNovedades` para facilitar comparación

---

## Categorías y Qué se Guarda

### ✅ Se guardan en `RegistroLibro`:
| Categoría | Descripción |
|-----------|-------------|
| `haberes_imponibles` | Sueldo base, bonos imponibles, etc. |
| `haberes_no_imponibles` | Colación, movilización, etc. |
| `descuentos_legales` | AFP, Salud, Seguro Cesantía |
| `otros_descuentos` | Anticipos, préstamos, etc. |
| `aportes_patronales` | Mutual, SIS, etc. |

### ❌ NO se guardan:
| Categoría | Razón |
|-----------|-------|
| `info_adicional` | Datos del empleado (año, mes, días trabajados) - no son montos |
| `ignorar` | Items que no participan en validación |

---

## Flujo de Procesamiento

```
1. SUBIR ARCHIVO
   └── ArchivoERP creado con estado 'subido'

2. EXTRAER HEADERS (Task Celery: extraer_headers_libro)
   └── Parser lee Excel
   └── Detecta headers (incluye duplicados con sufijos .1, .2)
   └── Crea/reutiliza ConceptoLibro por cliente/ERP
   └── Auto-clasifica primeras 8 columnas como 'info_adicional' (Talana)
   └── Estado → 'pendiente_clasificacion'

3. CLASIFICAR CONCEPTOS (UI: ClasificacionLibroV2)
   └── Usuario asigna categoría a cada concepto pendiente
   └── Puede reclasificar conceptos ya clasificados
   └── Estado → 'listo' (cuando todos clasificados)

4. PROCESAR LIBRO (Task Celery: procesar_libro_remuneraciones)
   └── Parser lee Excel completo
   └── Por cada fila (empleado):
       └── Extraer RUT y nombre
       └── Crear EmpleadoLibro
       └── Por cada concepto clasificado (no info_adicional, no ignorar):
           └── Si monto > 0: Crear RegistroLibro
   └── Estado → 'procesado'
```

---

## Ejemplo Práctico

### Excel de entrada (fila de un empleado):

| Año | Mes | RUT Empresa | RUT Trabajador | Nombre | ... | SUELDO BASE | BONO | AFP | COLACIÓN |
|-----|-----|-------------|----------------|--------|-----|-------------|------|-----|----------|
| 2025 | 08 | 76.xxx.xxx-x | 12.345.678-9 | Juan Pérez | ... | 1.500.000 | 0 | 150.000 | 50.000 |

### Clasificación de conceptos:
- Columnas 0-7: `info_adicional` (auto-clasificadas)
- SUELDO BASE: `haberes_imponibles`
- BONO: `haberes_imponibles`
- AFP: `descuentos_legales`
- COLACIÓN: `haberes_no_imponibles`

### Datos guardados:

```python
# EmpleadoLibro
{
    "rut": "12.345.678-9",
    "nombre": "Juan Pérez"
}

# RegistroLibro (solo monto > 0)
[
    {"concepto": "SUELDO BASE", "monto": 1500000},
    {"concepto": "AFP", "monto": 150000},
    {"concepto": "COLACIÓN", "monto": 50000}
]
# Nota: BONO no se guarda porque monto = 0
```

---

## Comparación con Novedades

La estructura de `RegistroLibro` permite comparación SQL directa:

```sql
-- Encontrar discrepancias
SELECT 
    libro.rut,
    concepto.header_original,
    libro.monto as monto_libro,
    novedades.monto as monto_novedades,
    ABS(libro.monto - novedades.monto) as diferencia
FROM registro_libro libro
JOIN concepto_libro concepto ON libro.concepto_id = concepto.id
JOIN mapeo_item_novedades mapeo ON mapeo.concepto_libro_id = concepto.id
JOIN registro_novedades novedades 
    ON novedades.rut_empleado = libro.rut 
    AND novedades.mapeo_id = mapeo.id
WHERE libro.monto != novedades.monto
```

---

## Archivos Relacionados

### Backend
- `apps/validador/models/empleado_libro.py` - Modelo EmpleadoLibro
- `apps/validador/models/registro_libro.py` - Modelo RegistroLibro (nuevo)
- `apps/validador/services/libro_service.py` - Lógica de procesamiento
- `apps/validador/tasks/libro.py` - Tasks Celery
- `apps/validador/parsers/talana.py` - Parser específico de Talana

### Frontend
- `features/validador/components/ClasificacionLibroV2.jsx` - UI de clasificación
- `features/validador/components/ClasificacionLibroModal.jsx` - Modal contenedor

### Documentación
- `docs/API_LIBRO.md` - Endpoints del API
- `docs/DUPLICATE_HEADERS_STRATEGY.md` - Manejo de headers duplicados
