# Service Layer - Guía de Implementación

## Estructura

```
backend/apps/validador/services/
├── __init__.py          # Exports públicos
├── base.py              # BaseService y ServiceResult
├── cierre_service.py    # Lógica de cierres
├── archivo_service.py   # Lógica de archivos
├── incidencia_service.py # Lógica de incidencias
└── equipo_service.py    # Lógica de equipos/supervisión
```

## Conceptos Clave

### ServiceResult

Todos los métodos de servicio retornan `ServiceResult`, un patrón que:
- Evita excepciones para flujo de control
- Proporciona mensajes de error consistentes
- Facilita el manejo en las views

```python
from apps.validador.services import CierreService, ServiceResult

result = CierreService.cambiar_estado(cierre, 'consolidado', user)

if result.success:
    cierre_actualizado = result.data
    # Continuar con éxito
else:
    error_message = result.error
    # Manejar error
```

### Crear un ServiceResult

```python
# Éxito
return ServiceResult.ok(data=cierre)

# Error simple
return ServiceResult.fail("No se puede consolidar")

# Error con múltiples campos
return ServiceResult.fail(
    error="Validación fallida",
    errors={'campo1': 'Error 1', 'campo2': 'Error 2'}
)
```

## Uso en Views

### Antes (lógica en la view)

```python
@action(detail=True, methods=['post'])
def cambiar_estado(self, request, pk=None):
    cierre = self.get_object()
    nuevo_estado = request.data.get('estado')
    
    # ❌ Lógica de negocio en la view
    estados_validos = dict(Cierre.ESTADO_CHOICES).keys()
    if nuevo_estado not in estados_validos:
        return Response({'error': '...'}, status=400)
    
    cierre.estado = nuevo_estado
    if nuevo_estado == 'consolidado':
        cierre.fecha_consolidacion = timezone.now()
    cierre.save()
    
    return Response(serializer.data)
```

### Después (usando servicio)

```python
from ..services import CierreService

@action(detail=True, methods=['post'])
def cambiar_estado(self, request, pk=None):
    cierre = self.get_object()
    nuevo_estado = request.data.get('estado')
    
    # ✅ View solo orquesta
    result = CierreService.cambiar_estado(cierre, nuevo_estado, request.user)
    
    if not result.success:
        return Response({'error': result.error}, status=400)
    
    return Response(CierreDetailSerializer(result.data).data)
```

## Servicios Disponibles

### CierreService

```python
from apps.validador.services import CierreService

# Cambiar estado con validación de transiciones
result = CierreService.cambiar_estado(cierre, 'consolidado', user)

# Consolidar (valida discrepancias = 0)
result = CierreService.consolidar(cierre, user)

# Finalizar (valida incidencias resueltas)
result = CierreService.finalizar(cierre, user)

# Cancelar
result = CierreService.cancelar(cierre, user, motivo="...")

# Obtener resumen completo
resumen = CierreService.obtener_resumen(cierre)
```

### ArchivoService

```python
from apps.validador.services import ArchivoService

# Subir archivo ERP (versionado automático)
result = ArchivoService.subir_archivo_erp(
    cierre=cierre,
    archivo=uploaded_file,
    tipo='libro_remuneraciones',
    user=request.user
)

# Subir archivo de analista
result = ArchivoService.subir_archivo_analista(
    cierre=cierre,
    archivo=uploaded_file,
    tipo='novedades',
    user=request.user
)

# Eliminar archivo (soft delete con reactivación de versión anterior)
result = ArchivoService.eliminar_archivo(archivo, user, es_erp=True)

# Obtener archivos de un cierre
archivos = ArchivoService.obtener_archivos_cierre(cierre)
```

### IncidenciaService

```python
from apps.validador.services import IncidenciaService

# Resolver incidencia
result = IncidenciaService.resolver(
    incidencia=incidencia,
    accion='aprobar',  # o 'rechazar'
    user=supervisor,
    motivo="Justificación válida"
)

# Agregar comentario
result = IncidenciaService.agregar_comentario(
    incidencia=incidencia,
    texto="Mi comentario",
    user=request.user
)

# Estadísticas de un cierre
stats = IncidenciaService.obtener_estadisticas_cierre(cierre)

# Incidencias del equipo (para supervisores)
data = IncidenciaService.obtener_incidencias_equipo(
    supervisor=user,
    solo_pendientes=True
)
```

### EquipoService

```python
from apps.validador.services import EquipoService

# Obtener analistas del supervisor
analistas = EquipoService.obtener_analistas(supervisor)

# Obtener cierres del equipo
result = EquipoService.obtener_cierres_equipo(
    supervisor=user,
    solo_activos=True
)

# Estadísticas completas del equipo
stats = EquipoService.obtener_estadisticas_equipo(supervisor)

# Asignar analista a supervisor
result = EquipoService.asignar_analista_a_supervisor(
    analista=analista,
    supervisor=nuevo_supervisor,
    user=request.user
)
```

## Crear un Nuevo Servicio

### 1. Crear el archivo

```python
# apps/validador/services/nuevo_service.py

from django.db import transaction
from typing import Dict, Any

from .base import BaseService, ServiceResult
from ..models import MiModelo


class NuevoService(BaseService):
    """
    Servicio para [descripción].
    """
    
    @classmethod
    def mi_operacion(cls, parametro, user=None) -> ServiceResult:
        """
        Descripción de la operación.
        
        Args:
            parametro: Qué es
            user: Usuario que ejecuta
            
        Returns:
            ServiceResult con el resultado
        """
        logger = cls.get_logger()
        
        # Validaciones
        if not parametro:
            return ServiceResult.fail("Parámetro requerido")
        
        try:
            with transaction.atomic():
                # Lógica de negocio
                resultado = hacer_algo(parametro)
                
                # Logging de auditoría
                cls.log_action(
                    action='mi_operacion',
                    entity_type='mi_modelo',
                    entity_id=resultado.id,
                    user=user
                )
                
                return ServiceResult.ok(resultado)
                
        except Exception as e:
            logger.error(f"Error en mi_operacion: {str(e)}")
            return ServiceResult.fail(f"Error: {str(e)}")
```

### 2. Exportar en __init__.py

```python
# apps/validador/services/__init__.py

from .nuevo_service import NuevoService

__all__ = [
    # ... existentes
    'NuevoService',
]
```

## Logging y Auditoría

El `BaseService` proporciona `log_action()` para auditoría:

```python
cls.log_action(
    action='crear',           # Tipo de acción
    entity_type='cierre',     # Entidad afectada
    entity_id=123,            # ID de la entidad
    user=request.user,        # Usuario que ejecuta
    extra={                   # Datos adicionales
        'campo': 'valor'
    }
)
```

## Testing

```python
from django.test import TestCase
from apps.validador.services import CierreService

class CierreServiceTest(TestCase):
    def test_cambiar_estado_valido(self):
        cierre = CierreFactory(estado='comparacion')
        
        result = CierreService.cambiar_estado(cierre, 'consolidado')
        
        self.assertTrue(result.success)
        self.assertEqual(result.data.estado, 'consolidado')
    
    def test_cambiar_estado_invalido(self):
        cierre = CierreFactory(estado='pendiente')
        
        result = CierreService.cambiar_estado(cierre, 'finalizado')
        
        self.assertFalse(result.success)
        self.assertIn('No se puede cambiar', result.error)
```

## Mejores Prácticas

1. **Views delgadas**: Las views solo deben:
   - Extraer datos del request
   - Llamar al servicio
   - Serializar la respuesta

2. **Servicios sin estado**: Usar `@classmethod`, no almacenar estado

3. **Transacciones**: Usar `with transaction.atomic()` para operaciones múltiples

4. **Logging**: Siempre loggear acciones importantes

5. **Validaciones**: Hacer validaciones antes de operaciones costosas

6. **Errores descriptivos**: Retornar mensajes claros para el usuario
