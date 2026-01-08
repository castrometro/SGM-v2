/**
 * Constantes centralizadas para SGM v2 Frontend
 * 
 * ⚠️ IMPORTANTE: Estas constantes deben estar sincronizadas con el backend.
 * Backend: apps/core/constants.py y apps/validador/constants.py
 * 
 * Uso:
 *   import { TIPO_USUARIO, ESTADO_CIERRE } from '@/constants'
 *   
 *   if (user.tipo_usuario === TIPO_USUARIO.GERENTE) { ... }
 *   if (cierre.estado === ESTADO_CIERRE.CONSOLIDADO) { ... }
 */

// ═══════════════════════════════════════════════════════════════════════════════
// TIPOS DE USUARIO
// ═══════════════════════════════════════════════════════════════════════════════

/**
 * Tipos de usuario del sistema SGM.
 * Jerarquía de permisos: GERENTE > SUPERVISOR > ANALISTA
 */
export const TIPO_USUARIO = Object.freeze({
  ANALISTA: 'analista',
  SUPERVISOR: 'supervisor',
  GERENTE: 'gerente',
})

/**
 * Usuarios que pueden aprobar incidencias/cierres
 */
export const PUEDEN_APROBAR = Object.freeze([
  TIPO_USUARIO.SUPERVISOR,
  TIPO_USUARIO.GERENTE,
])

/**
 * Usuarios que pueden supervisar equipos
 */
export const PUEDEN_SUPERVISAR = Object.freeze([
  TIPO_USUARIO.SUPERVISOR,
  TIPO_USUARIO.GERENTE,
])

/**
 * Usuarios que pueden administrar el sistema
 */
export const PUEDEN_ADMINISTRAR = Object.freeze([
  TIPO_USUARIO.GERENTE,
])

/**
 * Usuarios que pueden ser asignados a clientes
 */
export const PUEDEN_SER_ASIGNADOS_CLIENTE = Object.freeze([
  TIPO_USUARIO.ANALISTA,
  TIPO_USUARIO.SUPERVISOR,
])

/**
 * Usuarios que pueden ser supervisores de otros
 */
export const PUEDEN_SER_SUPERVISORES = Object.freeze([
  TIPO_USUARIO.SUPERVISOR,
  TIPO_USUARIO.GERENTE,
])

// ═══════════════════════════════════════════════════════════════════════════════
// ESTADOS DE CIERRE
// ═══════════════════════════════════════════════════════════════════════════════

/**
 * Estados del proceso de cierre de nómina.
 * 
 * Flujo principal:
 *   CARGA_ARCHIVOS → CLASIFICACION → MAPEO → COMPARACION →
 *   CON_DISCREPANCIAS (loop) → CONSOLIDADO →
 *   DETECCION_INCIDENCIAS → REVISION_INCIDENCIAS → FINALIZADO
 */
export const ESTADO_CIERRE = Object.freeze({
  CARGA_ARCHIVOS: 'carga_archivos',
  CLASIFICACION_CONCEPTOS: 'clasificacion_conceptos',
  MAPEO_ITEMS: 'mapeo_items',
  COMPARACION: 'comparacion',
  CON_DISCREPANCIAS: 'con_discrepancias',
  CONSOLIDADO: 'consolidado',
  DETECCION_INCIDENCIAS: 'deteccion_incidencias',
  REVISION_INCIDENCIAS: 'revision_incidencias',
  FINALIZADO: 'finalizado',
  CANCELADO: 'cancelado',
  ERROR: 'error',
})

/**
 * Estados activos (cierre en progreso)
 */
export const ESTADOS_CIERRE_ACTIVOS = Object.freeze([
  ESTADO_CIERRE.CARGA_ARCHIVOS,
  ESTADO_CIERRE.CLASIFICACION_CONCEPTOS,
  ESTADO_CIERRE.MAPEO_ITEMS,
  ESTADO_CIERRE.COMPARACION,
  ESTADO_CIERRE.CON_DISCREPANCIAS,
  ESTADO_CIERRE.CONSOLIDADO,
  ESTADO_CIERRE.DETECCION_INCIDENCIAS,
  ESTADO_CIERRE.REVISION_INCIDENCIAS,
])

/**
 * Estados finales (cierre terminado)
 */
export const ESTADOS_CIERRE_FINALES = Object.freeze([
  ESTADO_CIERRE.FINALIZADO,
  ESTADO_CIERRE.CANCELADO,
])

/**
 * Estados que permiten edición de archivos
 */
export const ESTADOS_CIERRE_EDITABLES = Object.freeze([
  ESTADO_CIERRE.CARGA_ARCHIVOS,
  ESTADO_CIERRE.CON_DISCREPANCIAS,
])

/**
 * Estados donde se puede finalizar el cierre
 */
export const ESTADOS_PUEDEN_FINALIZAR = Object.freeze([
  ESTADO_CIERRE.CONSOLIDADO,
  ESTADO_CIERRE.REVISION_INCIDENCIAS,
  ESTADO_CIERRE.DETECCION_INCIDENCIAS,
])

// ═══════════════════════════════════════════════════════════════════════════════
// ESTADOS DE INCIDENCIA
// ═══════════════════════════════════════════════════════════════════════════════

/**
 * Estados de una incidencia detectada.
 * Flujo: PENDIENTE → EN_REVISION → APROBADA/RECHAZADA
 */
export const ESTADO_INCIDENCIA = Object.freeze({
  PENDIENTE: 'pendiente',
  EN_REVISION: 'en_revision',
  APROBADA: 'aprobada',
  RECHAZADA: 'rechazada',
})

/**
 * Incidencias abiertas (sin resolver)
 */
export const ESTADOS_INCIDENCIA_ABIERTOS = Object.freeze([
  ESTADO_INCIDENCIA.PENDIENTE,
  ESTADO_INCIDENCIA.EN_REVISION,
])

/**
 * Incidencias resueltas
 */
export const ESTADOS_INCIDENCIA_RESUELTOS = Object.freeze([
  ESTADO_INCIDENCIA.APROBADA,
  ESTADO_INCIDENCIA.RECHAZADA,
])

// ═══════════════════════════════════════════════════════════════════════════════
// TIPOS DE ARCHIVOS
// ═══════════════════════════════════════════════════════════════════════════════

/**
 * Tipos de archivos provenientes del ERP
 */
export const TIPO_ARCHIVO_ERP = Object.freeze({
  LIBRO_REMUNERACIONES: 'libro_remuneraciones',
  MOVIMIENTOS_MES: 'movimientos_mes',
})

/**
 * Tipos de archivos cargados por el analista
 */
export const TIPO_ARCHIVO_ANALISTA = Object.freeze({
  NOVEDADES: 'novedades',
  ASISTENCIAS: 'asistencias',
  FINIQUITOS: 'finiquitos',
  INGRESOS: 'ingresos',
})

/**
 * Archivos del analista requeridos
 */
export const ARCHIVOS_ANALISTA_REQUERIDOS = Object.freeze([
  TIPO_ARCHIVO_ANALISTA.NOVEDADES,
])

// ═══════════════════════════════════════════════════════════════════════════════
// CONFIGURACIÓN DE UI
// ═══════════════════════════════════════════════════════════════════════════════

/**
 * Configuración de badges para tipos de usuario
 */
export const TIPO_USUARIO_BADGE = Object.freeze({
  [TIPO_USUARIO.ANALISTA]: {
    label: 'Analista',
    variant: 'secondary',
    icon: 'User',
  },
  [TIPO_USUARIO.SUPERVISOR]: {
    label: 'Supervisor',
    variant: 'primary',
    icon: 'UserCheck',
  },
  [TIPO_USUARIO.GERENTE]: {
    label: 'Gerente',
    variant: 'success',
    icon: 'Shield',
  },
})

/**
 * Configuración de badges para estados de cierre
 */
export const ESTADO_CIERRE_BADGE = Object.freeze({
  [ESTADO_CIERRE.CARGA_ARCHIVOS]: {
    label: 'Carga de Archivos',
    variant: 'secondary',
    color: 'gray',
  },
  [ESTADO_CIERRE.CLASIFICACION_CONCEPTOS]: {
    label: 'Clasificación',
    variant: 'warning',
    color: 'yellow',
  },
  [ESTADO_CIERRE.MAPEO_ITEMS]: {
    label: 'Mapeo',
    variant: 'warning',
    color: 'yellow',
  },
  [ESTADO_CIERRE.COMPARACION]: {
    label: 'Comparando',
    variant: 'info',
    color: 'blue',
  },
  [ESTADO_CIERRE.CON_DISCREPANCIAS]: {
    label: 'Con Discrepancias',
    variant: 'danger',
    color: 'red',
  },
  [ESTADO_CIERRE.CONSOLIDADO]: {
    label: 'Consolidado',
    variant: 'success',
    color: 'green',
  },
  [ESTADO_CIERRE.DETECCION_INCIDENCIAS]: {
    label: 'Detectando Incidencias',
    variant: 'info',
    color: 'blue',
  },
  [ESTADO_CIERRE.REVISION_INCIDENCIAS]: {
    label: 'Revisión Incidencias',
    variant: 'warning',
    color: 'orange',
  },
  [ESTADO_CIERRE.FINALIZADO]: {
    label: 'Finalizado',
    variant: 'success',
    color: 'green',
  },
  [ESTADO_CIERRE.CANCELADO]: {
    label: 'Cancelado',
    variant: 'secondary',
    color: 'gray',
  },
  [ESTADO_CIERRE.ERROR]: {
    label: 'Error',
    variant: 'danger',
    color: 'red',
  },
})

/**
 * Configuración de badges para estados de incidencia
 */
export const ESTADO_INCIDENCIA_BADGE = Object.freeze({
  [ESTADO_INCIDENCIA.PENDIENTE]: {
    label: 'Pendiente',
    variant: 'warning',
    color: 'yellow',
  },
  [ESTADO_INCIDENCIA.EN_REVISION]: {
    label: 'En Revisión',
    variant: 'info',
    color: 'blue',
  },
  [ESTADO_INCIDENCIA.APROBADA]: {
    label: 'Aprobada',
    variant: 'success',
    color: 'green',
  },
  [ESTADO_INCIDENCIA.RECHAZADA]: {
    label: 'Rechazada',
    variant: 'danger',
    color: 'red',
  },
})

// ═══════════════════════════════════════════════════════════════════════════════
// HELPERS
// ═══════════════════════════════════════════════════════════════════════════════

/**
 * Verifica si un tipo de usuario puede aprobar
 * @param {string} tipo - Tipo de usuario
 * @returns {boolean}
 */
export const puedeAprobar = (tipo) => PUEDEN_APROBAR.includes(tipo)

/**
 * Verifica si un tipo de usuario puede supervisar
 * @param {string} tipo - Tipo de usuario
 * @returns {boolean}
 */
export const puedeSupervisar = (tipo) => PUEDEN_SUPERVISAR.includes(tipo)

/**
 * Verifica si un tipo de usuario puede administrar
 * @param {string} tipo - Tipo de usuario
 * @returns {boolean}
 */
export const puedeAdministrar = (tipo) => PUEDEN_ADMINISTRAR.includes(tipo)

/**
 * Verifica si un estado de cierre está activo
 * @param {string} estado - Estado del cierre
 * @returns {boolean}
 */
export const esCierreActivo = (estado) => ESTADOS_CIERRE_ACTIVOS.includes(estado)

/**
 * Verifica si un estado de cierre es final
 * @param {string} estado - Estado del cierre
 * @returns {boolean}
 */
export const esCierreFinal = (estado) => ESTADOS_CIERRE_FINALES.includes(estado)

/**
 * Verifica si un estado de cierre permite edición
 * @param {string} estado - Estado del cierre
 * @returns {boolean}
 */
export const esCierreEditable = (estado) => ESTADOS_CIERRE_EDITABLES.includes(estado)

/**
 * Verifica si una incidencia está abierta
 * @param {string} estado - Estado de la incidencia
 * @returns {boolean}
 */
export const esIncidenciaAbierta = (estado) => ESTADOS_INCIDENCIA_ABIERTOS.includes(estado)

/**
 * Verifica si una incidencia está resuelta
 * @param {string} estado - Estado de la incidencia
 * @returns {boolean}
 */
export const esIncidenciaResuelta = (estado) => ESTADOS_INCIDENCIA_RESUELTOS.includes(estado)

// ═══════════════════════════════════════════════════════════════════════════════
// DEFAULT EXPORT
// ═══════════════════════════════════════════════════════════════════════════════

export default {
  TIPO_USUARIO,
  ESTADO_CIERRE,
  ESTADO_INCIDENCIA,
  TIPO_ARCHIVO_ERP,
  TIPO_ARCHIVO_ANALISTA,
}
