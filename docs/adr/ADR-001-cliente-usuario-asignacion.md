# ADR-001: Modelo de Asignación Cliente-Usuario

**Fecha:** 2026-01-23  
**Estado:** Aceptado  
**Autores:** Equipo SGM-v2  

## Contexto

El sistema SGM-v2 requiere gestionar la relación entre Clientes y Usuarios (analistas/supervisores) para:

1. Controlar qué usuarios pueden acceder a datos de qué clientes
2. Permitir reasignar clientes entre analistas
3. Soportar la jerarquía analista → supervisor → gerente

Inicialmente se implementó un modelo intermedio `AsignacionClienteUsuario` (Many-to-Many con metadata) que permitía:
- Historial de asignaciones (fecha_inicio, fecha_fin)
- Metadata adicional (rol en la asignación)
- Múltiples usuarios por cliente

## Decisión

**Se elimina el modelo `AsignacionClienteUsuario` y se reemplaza por una relación directa Foreign Key:**

```python
class Cliente(models.Model):
    usuario_asignado = models.ForeignKey(
        'core.Usuario',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='clientes_asignados'
    )
```

### Cambios realizados

1. **Migración 0003**: Agregó campo `usuario_asignado` a Cliente
2. **Migración 0004**: Eliminó modelo `AsignacionClienteUsuario`
3. **Código actualizado**:
   - `apps/core/models/usuario.py`: Métodos `get_clientes_asignados()`, `get_clientes_supervisados()`
   - `shared/permissions.py`: Clase `CanAccessCliente`

## Consecuencias

### Positivas

1. **Simplicidad**: Modelo más simple y fácil de entender
2. **Performance**: Menos JOINs en queries de acceso a clientes
3. **Mantenibilidad**: Menos código para mantener
4. **Consistencia**: Un solo punto de verdad para la asignación

### Negativas

1. **Sin historial**: No se mantiene historial de asignaciones previas
2. **Un usuario por cliente**: Solo un analista puede estar asignado a un cliente
3. **Sin metadata**: No hay campos adicionales en la relación

### Mitigaciones

- **Historial**: Si se requiere, usar `AuditLog` para registrar cambios de asignación
- **Múltiples usuarios**: Usar el campo `supervisor` del Usuario para acceso jerárquico
- **Metadata**: Agregar campos directamente a Cliente si se necesitan

## Alternativas Consideradas

### 1. Mantener AsignacionClienteUsuario (Rechazada)

**Pros:**
- Historial completo
- Flexibilidad para múltiples asignaciones

**Contras:**
- Complejidad innecesaria para el caso de uso actual
- Queries más complejas
- Más código para mantener

### 2. Django Many-to-Many simple (Rechazada)

**Pros:**
- Múltiples usuarios por cliente

**Contras:**
- No cumple con regla de negocio: un cliente tiene UN analista asignado
- Ambigüedad en responsabilidad

## Referencias

- Issue #33: [CRÍTICO] Crear ADR para AsignacionClienteUsuario
- Migración: `0003_cliente_usuario_asignado.py`
- Migración: `0004_remove_asignacionclienteusuario.py`
