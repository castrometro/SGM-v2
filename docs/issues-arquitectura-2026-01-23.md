# Issues de Arquitectura y Seguridad - 2026-01-23

Generados a partir de evaluación de arquitectura de cambios del día.

---

## Issue 1: [CRÍTICO] Crear ADR para simplificación de AsignacionClienteUsuario

**Labels:** `arquitectura`, `documentation`

### Descripción
Documentar la decisión arquitectónica de eliminar el modelo `AsignacionClienteUsuario` y migrar a una relación directa `Cliente.usuario_asignado`.

### Contexto
En la migración 0004 se eliminó `AsignacionClienteUsuario`, pero no se documentó la razón ni los trade-offs de esta decisión. Esto causó bugs por referencias obsoletas en:
- `apps/core/models/usuario.py` - métodos `get_clientes_asignados()` y `get_clientes_supervisados()`
- `shared/permissions.py` - clase `CanAccessCliente`

### Tareas
- [ ] Crear directorio `docs/architecture/` si no existe
- [ ] Crear `docs/architecture/ADR-template.md` con plantilla estándar
- [ ] Crear `docs/architecture/ADR-001-simplificar-asignacion-clientes.md`

### Prioridad
🔴 Crítica - Deuda técnica de documentación

---

## Issue 2: [CRÍTICO] Implementar rate limiting en endpoint de procesamiento

**Labels:** `security`, `backend`

### Descripción
Agregar throttling al endpoint `/api/v1/validador/archivos-analista/{id}/procesar/` para prevenir ataques DoS por procesamiento masivo.

### Contexto
El endpoint de procesamiento dispara tareas Celery que consumen recursos significativos. Sin rate limiting, un atacante podría:
- Saturar workers de Celery
- Consumir recursos de CPU/memoria
- Afectar disponibilidad del sistema

### Implementación sugerida
```python
# settings.py
REST_FRAMEWORK = {
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.ScopedRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'procesamiento': '10/hour',
    }
}

# En ArchivoAnalistaViewSet
@action(detail=True, methods=['post'])
def procesar(self, request, pk=None):
    ...
    
# Agregar throttle_scope = 'procesamiento' a la view
```

### Prioridad
🔴 Crítica - Vulnerabilidad de seguridad (OWASP A05:2021)

---

## Issue 3: [CRÍTICO] Agregar polling de estado en procesamiento de novedades

**Labels:** `frontend`, `enhancement`

### Descripción
Implementar polling de estado en `MapeoNovedadesModal.jsx` para mostrar progreso del procesamiento al usuario.

### Problema actual
Cuando el usuario presiona "Procesar Novedades":
1. Se dispara la tarea Celery
2. El modal se cierra
3. El usuario NO tiene feedback del progreso
4. Si hay error, el usuario no se entera inmediatamente

### Implementación sugerida
```javascript
// En MapeoNovedadesModal.jsx
const [procesando, setProcesando] = useState(false)

const { data: estadoArchivo } = useQuery({
  queryKey: ['estado-archivo', archivo?.id],
  queryFn: () => api.get(`/v1/validador/archivos-analista/${archivo.id}/`),
  refetchInterval: procesando ? 2000 : false,
  enabled: procesando && !!archivo?.id
})

// Mostrar progreso similar a ClasificacionLibroModal
{procesando && (
  <div className="mt-4">
    <ProgressBar value={estadoArchivo?.progreso || 0} />
    <p className="text-sm text-secondary-400">
      {estadoArchivo?.mensaje || 'Procesando...'}
    </p>
  </div>
)}
```

### Prioridad
🔴 Crítica - UX deficiente

---

## Issue 4: [IMPORTANTE] Escribir tests de regresión para permisos de cliente

**Labels:** `testing`, `backend`

### Descripción
Crear tests automatizados para validar que los permisos de acceso a clientes funcionan correctamente después de la simplificación del modelo.

### Tests requeridos
```python
# tests/core/test_usuario_cliente_access.py

def test_analista_accede_solo_clientes_propios():
    analista = crear_usuario(tipo=TipoUsuario.ANALISTA)
    cliente_propio = crear_cliente(usuario_asignado=analista)
    cliente_ajeno = crear_cliente(usuario_asignado=otro_analista)
    
    assert cliente_propio in analista.get_clientes_asignados()
    assert cliente_ajeno not in analista.get_clientes_asignados()

def test_supervisor_accede_clientes_equipo():
    supervisor = crear_usuario(tipo=TipoUsuario.SUPERVISOR)
    analista = crear_usuario(supervisor=supervisor)
    cliente = crear_cliente(usuario_asignado=analista)
    
    assert cliente in supervisor.get_clientes_supervisados()

def test_gerente_accede_todos_clientes():
    gerente = crear_usuario(tipo=TipoUsuario.GERENTE)
    clientes = crear_clientes(5)
    
    assert len(gerente.get_todos_los_clientes()) == 5

def test_permission_can_access_cliente():
    # Test de CanAccessCliente permission class
    ...
```

### Prioridad
🟡 Importante - Prevenir regresiones

---

## Issue 5: [IMPORTANTE] Implementar structured logging

**Labels:** `backend`, `arquitectura`

### Descripción
Refactorizar el logging en `shared/exceptions.py` para usar formato estructurado compatible con Sentry/DataDog.

### Implementación actual
```python
logger.error(
    f"Unhandled exception in {view_name}: {exc}\n{traceback.format_exc()}"
)
```

### Implementación sugerida
```python
logger.error(
    "Unhandled exception",
    extra={
        'view_name': view_name,
        'exception_type': type(exc).__name__,
        'exception_message': str(exc),
        'traceback': traceback.format_exc(),
        'user_id': getattr(request.user, 'id', None),
        'path': request.path,
        'method': request.method,
        'request_id': getattr(request, 'request_id', None),
    }
)
```

### Beneficios
- Integración con servicios de monitoreo
- Alertas configurables por tipo de error
- Análisis agregado de errores

### Prioridad
🟡 Importante - Observabilidad

---

## Issue 6: [IMPORTANTE] Configurar timeouts en tareas Celery

**Labels:** `backend`, `arquitectura`

### Descripción
Agregar soft_time_limit y time_limit a las tareas Celery de procesamiento para evitar tareas zombie.

### Tareas afectadas
- `procesar_archivo_erp`
- `procesar_archivo_analista`
- `extraer_headers_novedades`
- `ejecutar_comparacion`

### Implementación
```python
@shared_task(
    bind=True, 
    max_retries=3, 
    soft_time_limit=300,  # 5 minutos soft
    time_limit=360        # 6 minutos hard
)
def procesar_archivo_analista(self, archivo_id, usuario_id=None):
    try:
        ...
    except SoftTimeLimitExceeded:
        # Cleanup y notificar
        archivo.estado = 'error'
        archivo.mensaje_error = 'Timeout: procesamiento excedió tiempo límite'
        archivo.save()
        raise
```

### Prioridad
🟡 Importante - Estabilidad del sistema

---

## Issue 7: [MEJORA] Optimizar N+1 queries en get_clientes_supervisados

**Labels:** `backend`, `performance`

### Descripción
Agregar `select_related()` en el método `get_clientes_supervisados()` para evitar queries adicionales.

### Código actual
```python
def get_clientes_supervisados(self):
    analistas_ids = self.analistas_supervisados.values_list('id', flat=True)
    return list(
        Cliente.objects.filter(
            usuario_asignado_id__in=analistas_ids,
            activo=True
        )
    )
```

### Código optimizado
```python
def get_clientes_supervisados(self):
    analistas_ids = self.analistas_supervisados.values_list('id', flat=True)
    return list(
        Cliente.objects.filter(
            usuario_asignado_id__in=analistas_ids,
            activo=True
        ).select_related('usuario_asignado', 'industria')
    )
```

### Prioridad
🟢 Mejora - Performance

---

## Issue 8: [MEJORA] Mejorar admin de RegistroNovedades

**Labels:** `backend`, `enhancement`

### Descripción
Mejorar la configuración del admin de `RegistroNovedades` con formato de montos, exportación y permisos.

### Mejoras sugeridas
```python
@admin.register(RegistroNovedades)
class RegistroNovedadesAdmin(admin.ModelAdmin):
    list_display = [
        'rut_empleado', 'nombre_empleado', 'nombre_item', 
        'monto_formateado', 'categoria_display', 'concepto_novedades', 'cierre'
    ]
    list_filter = [
        'cierre__cliente', 
        'cierre__periodo',
    ]
    search_fields = ['rut_empleado', 'nombre_empleado', 'nombre_item']
    raw_id_fields = ['cierre', 'concepto_novedades']
    ordering = ['-cierre__periodo', 'rut_empleado']
    list_per_page = 50
    
    def monto_formateado(self, obj):
        return f"${obj.monto:,.0f}"
    monto_formateado.short_description = 'Monto'
    
    def categoria_display(self, obj):
        return obj.categoria or '—'
    categoria_display.short_description = 'Categoría'
    
    # Solo lectura (registros se crean via API)
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser
```

### Prioridad
🟢 Mejora - UX Admin

---

## Issue 9: [SEGURIDAD] Agregar validación de tamaño de archivo

**Labels:** `security`, `backend`

### Descripción
Validar tamaño y tipo MIME de archivos subidos para prevenir ataques y uso excesivo de recursos.

### Implementación
```python
# En serializers de ArchivoERP y ArchivoAnalista

def validate_archivo(self, value):
    MAX_SIZE = 50 * 1024 * 1024  # 50MB
    
    if value.size > MAX_SIZE:
        raise serializers.ValidationError(
            f"Archivo muy grande: {value.size/1024/1024:.1f}MB. Máximo: 50MB"
        )
    
    # Validar tipo MIME
    allowed_types = [
        'application/vnd.ms-excel',
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'text/csv',
    ]
    
    # Validar magic bytes además de content_type
    import magic
    mime = magic.from_buffer(value.read(2048), mime=True)
    value.seek(0)
    
    if mime not in allowed_types:
        raise serializers.ValidationError(
            f"Tipo de archivo no permitido: {mime}"
        )
    
    return value
```

### Prioridad
🟡 Importante - Seguridad

---

## Issue 10: [UX] Agregar confirmación antes de procesar novedades

**Labels:** `frontend`, `enhancement`

### Descripción
Mostrar modal de confirmación con resumen antes de iniciar el procesamiento de novedades.

### Implementación
```javascript
const handleProcesar = () => {
  const confirmacion = window.confirm(
    `¿Procesar archivo de novedades?\n\n` +
    `• ${mapeadosCount} conceptos mapeados\n` +
    `• Este proceso puede tardar varios minutos\n` +
    `• El archivo quedará en estado "Procesado"`
  )
  
  if (confirmacion) {
    procesarMutation.mutate()
  }
}

// O mejor, usar un modal personalizado con más detalle
```

### Prioridad
🟢 Mejora - UX

---

## Resumen

| # | Título | Labels | Prioridad |
|---|--------|--------|-----------|
| 1 | Crear ADR para AsignacionClienteUsuario | arquitectura, documentation | 🔴 Crítica |
| 2 | Rate limiting en procesamiento | security, backend | 🔴 Crítica |
| 3 | Polling de estado en novedades | frontend, enhancement | 🔴 Crítica |
| 4 | Tests de permisos de cliente | testing, backend | 🟡 Importante |
| 5 | Structured logging | backend, arquitectura | 🟡 Importante |
| 6 | Timeouts en Celery | backend, arquitectura | 🟡 Importante |
| 7 | Optimizar N+1 queries | backend, performance | 🟢 Mejora |
| 8 | Mejorar admin RegistroNovedades | backend, enhancement | 🟢 Mejora |
| 9 | Validación tamaño archivo | security, backend | 🟡 Importante |
| 10 | Confirmación antes de procesar | frontend, enhancement | 🟢 Mejora |
