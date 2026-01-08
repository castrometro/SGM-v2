/**
 * Dashboards de Nómina - Post validación
 * Análisis visual de cierres procesados
 * 
 * Estructura:
 * - pages/      → Páginas de dashboard (Hub, Libro, Movimientos)
 * - components/ → Componentes compartidos (VariacionBadge)
 * - utils/      → Utilidades (formatters)
 */

// Páginas
export { default as DashboardHubPage } from './pages/DashboardHubPage'
export { default as LibroDashboardPage } from './pages/LibroDashboardPage'
export { default as MovimientosDashboardPage } from './pages/MovimientosDashboardPage'

// Componentes (para uso externo si es necesario)
export { VariacionBadge } from './components'

// Utils (para uso externo si es necesario)
export * from './utils'
