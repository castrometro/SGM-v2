/**
 * Badge de Variación Porcentual
 * Muestra la variación entre dos valores con color e ícono apropiado
 */
import { ArrowUpRight, ArrowDownRight, Minus } from 'lucide-react'
import { calcVariacion } from '../utils'

const VariacionBadge = ({ actual, anterior, invertColor = false }) => {
  const variacion = calcVariacion(actual, anterior)
  const isPositive = variacion > 0
  const isNeutral = Math.abs(variacion) < 0.01
  
  // invertColor: true cuando un aumento es malo (ej: finiquitos, gastos)
  const colorClass = isNeutral 
    ? 'text-secondary-400' 
    : (isPositive !== invertColor) 
      ? 'text-green-400' 
      : 'text-red-400'
  
  const Icon = isNeutral ? Minus : isPositive ? ArrowUpRight : ArrowDownRight
  
  return (
    <div className={`flex items-center gap-1 text-sm font-medium ${colorClass}`}>
      <Icon className="h-4 w-4" />
      <span>{isNeutral ? '0%' : `${variacion > 0 ? '+' : ''}${variacion.toFixed(1)}%`}</span>
    </div>
  )
}

export default VariacionBadge
