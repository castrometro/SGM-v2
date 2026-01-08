/**
 * Utilidades de formateo para dashboards de nómina
 */

/**
 * Formatea un valor como moneda CLP
 */
export const formatCurrency = (value) => {
  return new Intl.NumberFormat('es-CL', {
    style: 'currency',
    currency: 'CLP',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(value)
}

/**
 * Formatea un número con separador de miles
 */
export const formatNumber = (value) => {
  return new Intl.NumberFormat('es-CL').format(value)
}

/**
 * Calcula la variación porcentual entre dos valores
 */
export const calcVariacion = (actual, anterior) => {
  if (anterior === 0) return actual > 0 ? 100 : 0
  return ((actual - anterior) / anterior) * 100
}

/**
 * Formatea un período YYYY-MM a "Mes Año"
 */
export const formatPeriodo = (periodo) => {
  if (!periodo) return ''
  const [year, month] = periodo.split('-')
  const meses = [
    'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
    'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'
  ]
  return `${meses[parseInt(month) - 1]} ${year}`
}
