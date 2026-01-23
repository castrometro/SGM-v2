#!/bin/bash
# Script para crear issues de arquitectura y seguridad
# Ejecutar desde la raíz del repositorio: ./scripts/create_arch_issues.sh

REPO="castrometro/SGM-v2"

echo "Creando issues de arquitectura y seguridad..."

# Issue 1: ADR
gh issue create --repo $REPO \
  --title "[CRÍTICO] Crear ADR para simplificación de AsignacionClienteUsuario" \
  --label "arquitectura,documentation" \
  --body "## Descripción
Documentar la decisión arquitectónica de eliminar el modelo \`AsignacionClienteUsuario\` y migrar a una relación directa \`Cliente.usuario_asignado\`.

## Contexto
En la migración 0004 se eliminó \`AsignacionClienteUsuario\`, pero no se documentó la razón ni los trade-offs. Esto causó bugs por referencias obsoletas.

## Tareas
- [ ] Crear directorio \`docs/architecture/\`
- [ ] Crear \`docs/architecture/ADR-template.md\`
- [ ] Crear \`docs/architecture/ADR-001-simplificar-asignacion-clientes.md\`

## Prioridad
🔴 Crítica - Deuda técnica de documentación"

# Issue 2: Rate limiting
gh issue create --repo $REPO \
  --title "[CRÍTICO] Implementar rate limiting en endpoint de procesamiento" \
  --label "security,backend" \
  --body "## Descripción
Agregar throttling al endpoint \`/api/v1/validador/archivos-analista/{id}/procesar/\` para prevenir ataques DoS.

## Riesgo
Sin rate limiting, un atacante podría saturar workers de Celery y afectar disponibilidad.

## Implementación
\`\`\`python
REST_FRAMEWORK = {
    'DEFAULT_THROTTLE_RATES': {
        'procesamiento': '10/hour',
    }
}
\`\`\`

## Prioridad
🔴 Crítica - OWASP A05:2021"

# Issue 3: Polling
gh issue create --repo $REPO \
  --title "[CRÍTICO] Agregar polling de estado en procesamiento de novedades" \
  --label "frontend,enhancement" \
  --body "## Descripción
Implementar polling en \`MapeoNovedadesModal.jsx\` para mostrar progreso del procesamiento.

## Problema
El usuario no tiene feedback después de presionar 'Procesar Novedades'.

## Solución
Usar \`useQuery\` con \`refetchInterval\` similar a \`ClasificacionLibroModal\`.

## Prioridad
🔴 Crítica - UX deficiente"

# Issue 4: Tests
gh issue create --repo $REPO \
  --title "[IMPORTANTE] Escribir tests de regresión para permisos de cliente" \
  --label "testing,backend" \
  --body "## Descripción
Crear tests para validar permisos de acceso a clientes por rol (analista, supervisor, gerente).

## Tests requeridos
- test_analista_accede_solo_clientes_propios
- test_supervisor_accede_clientes_equipo  
- test_gerente_accede_todos_clientes
- test_permission_can_access_cliente

## Prioridad
🟡 Importante"

# Issue 5: Structured logging
gh issue create --repo $REPO \
  --title "[IMPORTANTE] Implementar structured logging" \
  --label "backend,arquitectura" \
  --body "## Descripción
Refactorizar logging en \`shared/exceptions.py\` para usar formato estructurado compatible con Sentry/DataDog.

## Beneficios
- Integración con servicios de monitoreo
- Alertas configurables
- Análisis agregado

## Prioridad
🟡 Importante"

# Issue 6: Celery timeouts
gh issue create --repo $REPO \
  --title "[IMPORTANTE] Configurar timeouts en tareas Celery" \
  --label "backend,arquitectura" \
  --body "## Descripción
Agregar \`soft_time_limit\` y \`time_limit\` a tareas de procesamiento para evitar tareas zombie.

## Tareas afectadas
- procesar_archivo_erp
- procesar_archivo_analista
- extraer_headers_novedades

## Prioridad
🟡 Importante"

# Issue 7: N+1 queries
gh issue create --repo $REPO \
  --title "[MEJORA] Optimizar N+1 queries en get_clientes_supervisados" \
  --label "backend,performance" \
  --body "## Descripción
Agregar \`select_related()\` en \`get_clientes_supervisados()\`.

## Prioridad
🟢 Mejora"

# Issue 8: Admin
gh issue create --repo $REPO \
  --title "[MEJORA] Mejorar admin de RegistroNovedades" \
  --label "backend,enhancement" \
  --body "## Descripción
Mejorar configuración del admin con formato de montos, ordenamiento y permisos read-only.

## Prioridad
🟢 Mejora"

# Issue 9: Validación archivo
gh issue create --repo $REPO \
  --title "[SEGURIDAD] Agregar validación de tamaño y tipo de archivo" \
  --label "security,backend" \
  --body "## Descripción
Validar tamaño (max 50MB) y tipo MIME de archivos subidos.

## Riesgo
Sin validación, archivos maliciosos o muy grandes podrían afectar el sistema.

## Prioridad
🟡 Importante"

# Issue 10: Confirmación
gh issue create --repo $REPO \
  --title "[UX] Agregar confirmación antes de procesar novedades" \
  --label "frontend,enhancement" \
  --body "## Descripción
Mostrar modal de confirmación con resumen antes de iniciar procesamiento.

## Prioridad
🟢 Mejora"

echo "✅ Issues creados exitosamente"
