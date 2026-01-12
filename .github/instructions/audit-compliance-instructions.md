---
description: 'Auditoría, trazabilidad y cumplimiento normativo para SGM-v2'
applyTo: 'backend/**/*.py'
---

# Auditoría y Cumplimiento - SGM v2

Estándares de auditoría, trazabilidad y cumplimiento con normativas de protección de datos personales para el Sistema de Gestión de Nómina.

## Marco Normativo

### ISO 27001:2022 - Seguridad de la Información

SGM debe cumplir con los controles relevantes:

| Control | Descripción | Implementación en SGM |
|---------|-------------|----------------------|
| A.8.15 | Logging | Registro de tareas de procesamiento |
| A.8.16 | Monitoreo | Dashboard de tareas Celery |
| A.5.33 | Protección de registros | Retención configurable con limpieza automática |

### ISO 27701:2019 - Privacidad de la Información

Extensión de ISO 27001 para datos personales:

| Requisito | Descripción | Implementación en SGM |
|-----------|-------------|----------------------|
| 7.2.8 | Registros de procesamiento | TaskResult con metadata de archivos procesados |
| 7.3.6 | Acceso a datos personales | Log de quién accedió a qué cierre |
| 7.4.5 | Trazabilidad de transferencias | Log de exportaciones |

### Ley 21.719 (Chile) - Protección de Datos Personales

Vigente desde 2024. Aplica a SGM porque procesa:

| Tipo de Dato | Clasificación | Ejemplo en SGM |
|--------------|---------------|----------------|
| Dato personal | Identificable | RUT, Nombre |
| Dato personal sensible | Requiere consentimiento explícito | Sueldo, AFP, Isapre, Licencias médicas |

**Sanciones:** Hasta 20.000 UTM (~$1.400M CLP) por incumplimiento.

**Derechos ARCO que debemos soportar:**
- **A**cceso: El titular puede pedir qué datos tenemos de él
- **R**ectificación: Corregir datos incorrectos
- **C**ancelación: Eliminar datos cuando ya no son necesarios
- **O**posición: Negarse a cierto tratamiento

---

## Arquitectura de Auditoría

### Principio: Defensa en Profundidad

```
┌─────────────────────────────────────────────────────────────────┐
│                        CAPA DE AUDITORÍA                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │   Celery Tasks  │  │  Access Logs    │  │  Export Logs    │ │
│  │   (TaskResult)  │  │  (Por definir)  │  │  (Por definir)  │ │
│  └────────┬────────┘  └────────┬────────┘  └────────┬────────┘ │
│           │                    │                    │          │
│           ▼                    ▼                    ▼          │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │                    PostgreSQL (Persistente)                 ││
│  │  - django_celery_results_taskresult                         ││
│  │  - audit_accesslog (futuro)                                 ││
│  │  - audit_exportlog (futuro)                                 ││
│  └─────────────────────────────────────────────────────────────┘│
│           │                                                     │
│           ▼                                                     │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │              Celery Beat - Limpieza Programada              ││
│  │  - Retención configurable por tipo                          ││
│  │  - Diferente retención para éxitos vs errores               ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Backend Dual: Redis + PostgreSQL

**Problema:** Necesitamos velocidad (polling) Y persistencia (auditoría).

**Solución:** 

| Propósito | Backend | Tabla/Key | TTL |
|-----------|---------|-----------|-----|
| Polling progreso en tiempo real | Redis | `libro_progreso_{id}` | 1 hora |
| Auditoría de tareas ejecutadas | PostgreSQL | `django_celery_results_taskresult` | Configurable |

```python
# El flujo es:
# 1. Tarea inicia → Escribe progreso en Redis (para polling rápido)
# 2. Tarea termina → Celery escribe resultado en PostgreSQL (auditoría)
# 3. Beat limpia → Elimina registros antiguos según política
```

---

## Implementación: Celery Results en BD

### Configuración

```python
# config/settings/base.py

# Backend principal: PostgreSQL para auditoría
CELERY_RESULT_BACKEND = 'django-db'

# Extender información guardada
CELERY_RESULT_EXTENDED = True

# Rastrear inicio de tareas (no solo fin)
CELERY_TASK_TRACK_STARTED = True

# Expiración de resultados (será manejada por Beat, no por Celery)
CELERY_RESULT_EXPIRES = None  # No expira automáticamente
```

### Campos disponibles en TaskResult

| Campo | Descripción | Uso para auditoría |
|-------|-------------|-------------------|
| `task_id` | UUID único | Correlación con logs |
| `task_name` | Nombre de la tarea | Filtrar por tipo |
| `task_args` | Argumentos (JSON) | Qué archivo/cierre se procesó |
| `task_kwargs` | Kwargs (JSON) | Metadata adicional |
| `status` | SUCCESS/FAILURE/etc | Detectar errores |
| `result` | Resultado serializado | Detalles del procesamiento |
| `date_created` | Cuándo se creó | Auditoría temporal |
| `date_started` | Cuándo inició | Medir tiempos |
| `date_done` | Cuándo terminó | Auditoría temporal |
| `traceback` | Error completo | Debug de fallos |
| `worker` | Qué worker ejecutó | Diagnóstico |
| `periodic_task_name` | Si fue tarea programada | Identificar Beat tasks |

### Información adicional a guardar

Para auditoría completa, las tareas deben incluir en `task_kwargs`:

```python
@shared_task(bind=True)
def procesar_archivo_erp(self, archivo_id, **kwargs):
    # kwargs debe incluir (pasado por quien llama):
    # - usuario_id: Quién inició la acción
    # - cliente_id: A qué cliente pertenece
    # - cierre_id: Contexto del cierre
    # - ip_address: Desde dónde se subió (opcional)
    pass
```

---

## Implementación: Limpieza Programada

### Política de Retención

| Tipo de Registro | Retención Default | Configurable | Justificación |
|------------------|-------------------|--------------|---------------|
| Tareas exitosas | 30 días | Sí | Balance entre auditoría y espacio |
| Tareas fallidas | 90 días | Sí | Más tiempo para investigar errores |
| Tareas de archivos con datos personales | 365 días | Sí | Cumplimiento legal |

### Variables de Entorno

```bash
# .env
CELERY_RESULTS_RETENTION_SUCCESS_DAYS=30
CELERY_RESULTS_RETENTION_FAILURE_DAYS=90
CELERY_RESULTS_RETENTION_SENSITIVE_DAYS=365
```

### Tarea de Limpieza

```python
# apps/core/tasks/cleanup.py

@shared_task(name='core.cleanup_task_results')
def cleanup_task_results():
    """
    Limpia resultados de tareas según política de retención.
    
    Ejecutada por Celery Beat diariamente a las 3:00 AM.
    
    Política:
    - Éxitos: CELERY_RESULTS_RETENTION_SUCCESS_DAYS (default 30)
    - Fallos: CELERY_RESULTS_RETENTION_FAILURE_DAYS (default 90)
    """
    from django_celery_results.models import TaskResult
    from django.utils import timezone
    from datetime import timedelta
    from django.conf import settings
    
    success_days = getattr(settings, 'CELERY_RESULTS_RETENTION_SUCCESS_DAYS', 30)
    failure_days = getattr(settings, 'CELERY_RESULTS_RETENTION_FAILURE_DAYS', 90)
    
    cutoff_success = timezone.now() - timedelta(days=success_days)
    cutoff_failure = timezone.now() - timedelta(days=failure_days)
    
    # Eliminar éxitos antiguos
    deleted_success, _ = TaskResult.objects.filter(
        status='SUCCESS',
        date_done__lt=cutoff_success
    ).delete()
    
    # Eliminar fallos antiguos
    deleted_failure, _ = TaskResult.objects.filter(
        status='FAILURE',
        date_done__lt=cutoff_failure
    ).delete()
    
    return {
        'deleted_success': deleted_success,
        'deleted_failure': deleted_failure,
    }
```

### Programación en Beat

```python
# Se configura via Django Admin o migración de datos
# PeriodicTask: cleanup_task_results
# Schedule: CrontabSchedule(hour=3, minute=0)  # 3:00 AM diario
```

---

## Consultas de Auditoría

### ¿Qué archivos se procesaron para un cliente?

```python
from django_celery_results.models import TaskResult
import json

def get_procesamiento_cliente(cliente_id, desde, hasta):
    """Obtiene historial de procesamiento para un cliente."""
    return TaskResult.objects.filter(
        task_name__startswith='validador.',
        date_done__range=(desde, hasta),
    ).filter(
        task_kwargs__contains=f'"cliente_id": {cliente_id}'
    ).order_by('-date_done')
```

### ¿Cuántos errores hubo este mes?

```python
def get_errores_mes(año, mes):
    """Obtiene tareas fallidas del mes."""
    from django.db.models import Count
    from django.db.models.functions import TruncDate
    
    return TaskResult.objects.filter(
        status='FAILURE',
        date_done__year=año,
        date_done__month=mes,
    ).annotate(
        fecha=TruncDate('date_done')
    ).values('fecha', 'task_name').annotate(
        total=Count('id')
    ).order_by('fecha')
```

### ¿Quién procesó este archivo?

```python
def get_usuario_procesamiento(archivo_id):
    """Obtiene quién inició el procesamiento de un archivo."""
    result = TaskResult.objects.filter(
        task_args__contains=str(archivo_id),
        task_name='validador.procesar_archivo_erp'
    ).first()
    
    if result and result.task_kwargs:
        kwargs = json.loads(result.task_kwargs)
        return kwargs.get('usuario_id')
    return None
```

---

## Checklist de Cumplimiento

### Para Auditoría ISO

- [ ] TaskResult almacena todas las tareas de procesamiento
- [ ] Se incluye usuario_id en kwargs de tareas
- [ ] Política de retención documentada y configurable
- [ ] Limpieza automática funcionando (Beat)
- [ ] Queries de auditoría disponibles para reportes

### Para Ley 21.719

- [ ] Registro de qué datos personales se procesaron (via archivo_id → cierre → cliente)
- [ ] Capacidad de identificar procesamiento por RUT específico
- [ ] Eliminación de registros cuando cliente solicita (ARCO)
- [ ] Documentación de política de retención

---

## Roadmap de Auditoría

### Fase 1: Celery Results (Este PR)
- [x] Cambiar backend a `django-db`
- [ ] Agregar metadata (usuario_id) a tareas existentes
- [ ] Crear tarea de limpieza
- [ ] Programar en Beat

### Fase 2: Access Logs (Futuro)
- [ ] Modelo `AccessLog` para registrar consultas
- [ ] Middleware para capturar accesos a datos sensibles
- [ ] Reportes de acceso por usuario/cliente

### Fase 3: Export Logs (Futuro)
- [ ] Modelo `ExportLog` para registrar descargas
- [ ] Interceptar exports de Excel/PDF
- [ ] Alertas de exports masivos

### Fase 4: ARCO (Futuro)
- [ ] Endpoint para consulta de datos por RUT
- [ ] Proceso de eliminación selectiva
- [ ] Generación de reporte ARCO

---

## Referencias

- [ISO 27001:2022](https://www.iso.org/standard/27001) - Seguridad de la información
- [ISO 27701:2019](https://www.iso.org/standard/71670.html) - Gestión de privacidad
- [Ley 21.719](https://www.bcn.cl/leychile/navegar?idNorma=1177911) - Protección de datos personales (Chile)
- [django-celery-results](https://django-celery-results.readthedocs.io/) - Documentación del paquete
- [CELERY_RESULT_EXTENDED](https://docs.celeryq.dev/en/stable/userguide/configuration.html#result-extended) - Config de Celery

---

**Última actualización:** 2026-01-12
**Autor:** SGM Team
**Próxima revisión:** Antes de auditoría ISO
