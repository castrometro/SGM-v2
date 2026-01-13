## Plan: Clasificación de Headers del Libro de Remuneraciones (Talana)

> **NOTA: Este plan ya fue implementado.** Los headers de identificación del empleado (RUT, Nombre, etc.) se detectan automáticamente por posición en el parser del ERP y se excluyen de la clasificación. Solo se clasifican conceptos monetarios (100%).

**TL;DR**: Implementar el flujo completo donde el analista clasifica los headers del Libro de Remuneraciones, con reutilización automática de clasificaciones previas del mismo Cliente+ERP, y manejo inteligente de headers duplicados.

### Decisiones de Diseño

- **Categorías**: Usar las existentes (`info_adicional` para datos informativos como "Días Trabajados")
- **Sin pre-clasificación sugerida**: El analista clasifica 100% manual la primera vez
- **Reutilización automática**: Headers ya clasificados en cierres anteriores se heredan automáticamente
- **Sin validación cruzada**: No comparar totales calculados vs totales del Excel (por ahora)

### Steps

1. **Actualizar parser Talana para renombrar duplicados explícitamente** en [backend/apps/validador/parsers/talana.py](backend/apps/validador/parsers/talana.py)
   - Detectar headers duplicados y renombrarlos como `Header (1)`, `Header (2)` en lugar del `.1` de pandas
   - Método `_renombrar_duplicados(headers: List[str]) -> List[str]`

2. **Modificar `_sincronizar_conceptos` para reutilizar clasificaciones previas** en [backend/apps/validador/services/libro_service.py](backend/apps/validador/services/libro_service.py#L113)
   - Al sincronizar headers, buscar si ya existe ConceptoLibro para ese Cliente+ERP+header_original
   - Si existe y tiene `categoria`, NO sobrescribir (ya está clasificado de cierre anterior)
   - Solo crear nuevos ConceptoLibro para headers que no existen en ese Cliente+ERP

3. **Agregar constante `CATEGORIA_CONCEPTO_LIBRO` al frontend** en [frontend/src/constants/index.js](frontend/src/constants/index.js)
   - Sincronizar categorías del backend: `haberes_imponibles`, `haberes_no_imponibles`, `descuentos_legales`, `otros_descuentos`, `aportes_patronales`, `info_adicional`, `ignorar`
   - **NOTA:** `identificador` fue eliminado - los headers de empleado se detectan automáticamente

4. **Crear hooks para gestión de headers del libro** en `frontend/src/features/validador/hooks/useLibro.js`
   - `useLibroHeaders(archivoId)` - GET headers y estado de clasificación
   - `useExtraerHeaders()` - POST para iniciar extracción async
   - `useClasificarConceptos()` - POST para guardar clasificaciones
   - `useProgresoLibro(archivoId)` - GET con polling para progreso

5. **Crear componente `ClasificacionConceptos.jsx`** en `frontend/src/features/validador/components/`
   - Tabla con todos los headers del libro (solo conceptos monetarios)
   - Dropdown para seleccionar categoría por header
   - Indicador visual: clasificados vs pendientes (heredados de cierres anteriores en verde)
   - Botón "Guardar clasificación" que envía solo los cambios

6. **Integrar en `CierreDetailPage.jsx`** en [frontend/src/features/validador/pages/CierreDetailPage.jsx](frontend/src/features/validador/pages/CierreDetailPage.jsx)
   - Cuando cierre está en `clasificacion_conceptos`, mostrar `ClasificacionConceptos`
   - Cuando todos los headers estén clasificados, habilitar botón para avanzar al siguiente estado
