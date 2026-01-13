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
// ESTADOS DE ARCHIVOS
// ═══════════════════════════════════════════════════════════════════════════════

/**
 * Estados de procesamiento de archivos (ERP y Analista)
 * Sincronizado con backend: ArchivoBase.ESTADO_CHOICES
 */
export const ESTADO_ARCHIVO = Object.freeze({
  SUBIDO: 'subido',
  PROCESANDO: 'procesando',
  PROCESADO: 'procesado',
  ERROR: 'error',
})

/**
 * Estados que indican que un archivo está siendo procesado (requiere polling)
 * Incluye estados generales y específicos del libro de remuneraciones
 */
export const ESTADOS_ARCHIVO_PROCESANDO = Object.freeze([
  ESTADO_ARCHIVO.PROCESANDO,
  'extrayendo_headers', // ESTADO_ARCHIVO_LIBRO.EXTRAYENDO_HEADERS - definido después
])

// ═══════════════════════════════════════════════════════════════════════════════
// ESTADOS DE ARCHIVO LIBRO DE REMUNERACIONES
// ═══════════════════════════════════════════════════════════════════════════════

/**
 * Estados específicos para el procesamiento del Libro de Remuneraciones.
 * Sincronizado con: backend/apps/validador/constants.py - EstadoArchivoLibro
 * 
 * Flujo:
 *   SUBIDO → EXTRAYENDO_HEADERS → PENDIENTE_CLASIFICACION → 
 *   LISTO → PROCESANDO → PROCESADO
 *                                         ↓
 *                                       ERROR
 */
export const ESTADO_ARCHIVO_LIBRO = Object.freeze({
  SUBIDO: 'subido',
  EXTRAYENDO_HEADERS: 'extrayendo_headers',
  PENDIENTE_CLASIFICACION: 'pendiente_clasificacion',
  LISTO: 'listo',
  PROCESANDO: 'procesando',
  PROCESADO: 'procesado',
  ERROR: 'error',
})

/**
 * Estados que permiten clasificación de conceptos del libro
 */
export const ESTADOS_LIBRO_PUEDE_CLASIFICAR = Object.freeze([
  ESTADO_ARCHIVO_LIBRO.PENDIENTE_CLASIFICACION,
  ESTADO_ARCHIVO_LIBRO.LISTO,
])

/**
 * Estados que permiten procesar el libro
 */
export const ESTADOS_LIBRO_PUEDE_PROCESAR = Object.freeze([
  ESTADO_ARCHIVO_LIBRO.LISTO,
])

/**
 * Estados que requieren acción del usuario (clasificación)
 */
export const ESTADOS_LIBRO_REQUIERE_ACCION = Object.freeze([
  ESTADO_ARCHIVO_LIBRO.PENDIENTE_CLASIFICACION,
])

/**
 * Verifica si el estado del libro permite clasificación
 * @param {string} estado - Estado del archivo libro
 * @returns {boolean}
 */
export const puedeClasificarLibro = (estado) => ESTADOS_LIBRO_PUEDE_CLASIFICAR.includes(estado)

/**
 * Verifica si el estado del libro permite procesamiento
 * @param {string} estado - Estado del archivo libro
 * @returns {boolean}
 */
export const puedeProcesarLibro = (estado) => ESTADOS_LIBRO_PUEDE_PROCESAR.includes(estado)

/**
 * Verifica si el libro requiere acción del usuario (clasificación pendiente)
 * @param {string} estado - Estado del archivo libro
 * @returns {boolean}
 */
export const libroRequiereAccion = (estado) => ESTADOS_LIBRO_REQUIERE_ACCION.includes(estado)

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
// CONFIGURACIÓN DE POLLING / QUERIES
// ═══════════════════════════════════════════════════════════════════════════════

/**
 * Intervalos de polling para diferentes operaciones (en milisegundos)
 */
export const POLLING_INTERVALS = Object.freeze({
  /** Polling para archivos en procesamiento */
  ARCHIVO_PROCESANDO: 3000,
  /** Polling para tareas Celery en progreso */
  TAREA_CELERY: 2000,
  /** Polling rápido para operaciones críticas */
  RAPIDO: 1000,
})

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
// TIPOS DE ERP
// ═══════════════════════════════════════════════════════════════════════════════

/**
 * Sistemas ERP soportados por SGM.
 * 
 * Estos slugs deben coincidir con:
 * - Backend: apps/core/constants.py (TipoERP)
 * - Base de datos: tabla core_erp.slug
 * 
 * Uso:
 *   import { TIPO_ERP } from '@/constants'
 *   
 *   if (config.erp.slug === TIPO_ERP.TALANA) { ... }
 */
export const TIPO_ERP = Object.freeze({
  TALANA: 'talana',
  BUK: 'buk',
  SAP: 'sap',
  NUBOX: 'nubox',
  SOFTLAND: 'softland',
  GENERIC: 'generic',
})

/**
 * ERPs que tienen API para integración directa
 */
export const ERPS_CON_API = Object.freeze([
  TIPO_ERP.TALANA,
  TIPO_ERP.BUK,
])

/**
 * ERPs que solo soportan carga de archivos
 */
export const ERPS_SOLO_ARCHIVOS = Object.freeze([
  TIPO_ERP.SAP,
  TIPO_ERP.NUBOX,
  TIPO_ERP.SOFTLAND,
  TIPO_ERP.GENERIC,
])

/**
 * Configuración de badges para ERPs
 */
export const TIPO_ERP_BADGE = Object.freeze({
  [TIPO_ERP.TALANA]: {
    label: 'Talana',
    variant: 'primary',
    color: 'blue',
  },
  [TIPO_ERP.BUK]: {
    label: 'BUK',
    variant: 'success',
    color: 'green',
  },
  [TIPO_ERP.SAP]: {
    label: 'SAP',
    variant: 'warning',
    color: 'yellow',
  },
  [TIPO_ERP.NUBOX]: {
    label: 'Nubox',
    variant: 'info',
    color: 'cyan',
  },
  [TIPO_ERP.SOFTLAND]: {
    label: 'Softland',
    variant: 'secondary',
    color: 'gray',
  },
  [TIPO_ERP.GENERIC]: {
    label: 'Genérico',
    variant: 'secondary',
    color: 'gray',
  },
})

/**
 * Verifica si un ERP tiene API disponible
 * @param {string} erpSlug - Slug del ERP
 * @returns {boolean}
 */
export const erpTieneAPI = (erpSlug) => ERPS_CON_API.includes(erpSlug)

/**
 * Obtiene la configuración de badge para un ERP
 * @param {string} erpSlug - Slug del ERP
 * @returns {object}
 */
export const getERPBadge = (erpSlug) => TIPO_ERP_BADGE[erpSlug] || TIPO_ERP_BADGE[TIPO_ERP.GENERIC]

// ═══════════════════════════════════════════════════════════════════════════════
// CATEGORÍAS DE CONCEPTOS LIBRO
// ═══════════════════════════════════════════════════════════════════════════════

/**
 * Categorías para clasificar conceptos del Libro de Remuneraciones.
 * Sincronizado con: backend/apps/validador/constants.py - CategoriaConceptoLibro
 */
export const CATEGORIA_CONCEPTO_LIBRO = Object.freeze({
  haberes_imponibles: 'Haberes Imponibles',
  haberes_no_imponibles: 'Haberes No Imponibles',
  descuentos_legales: 'Descuentos Legales',
  otros_descuentos: 'Otros Descuentos',
  aportes_patronales: 'Aportes Patronales',
  info_adicional: 'Información Adicional',
  ignorar: 'Ignorar',
})

/**
 * Categorías monetarias (se suman para calcular totales)
 */
export const CATEGORIAS_MONETARIAS = Object.freeze([
  'haberes_imponibles',
  'haberes_no_imponibles',
  'descuentos_legales',
  'otros_descuentos',
  'aportes_patronales',
])

/**
 * Categorías no monetarias (no se procesan en cálculos)
 */
export const CATEGORIAS_NO_MONETARIAS = Object.freeze([
  'info_adicional',
  'ignorar',
])

// ═══════════════════════════════════════════════════════════════════════════════
// DEFAULT EXPORT
// ═══════════════════════════════════════════════════════════════════════════════

export default {
  TIPO_USUARIO,
  ESTADO_CIERRE,
  ESTADO_INCIDENCIA,
  TIPO_ARCHIVO_ERP,
  TIPO_ARCHIVO_ANALISTA,
  TIPO_ERP,
  CATEGORIA_CONCEPTO_LIBRO,
  ESTADO_ARCHIVO_LIBRO,
}
