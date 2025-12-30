/**
 * Componente Badge para estados
 */
import { cn } from '../../utils/cn'

const variants = {
  default: 'bg-secondary-700 text-secondary-200',
  primary: 'bg-primary-600/20 text-primary-400 border-primary-500/30',
  success: 'bg-green-600/20 text-green-400 border-green-500/30',
  warning: 'bg-amber-600/20 text-amber-400 border-amber-500/30',
  danger: 'bg-red-600/20 text-red-400 border-red-500/30',
  info: 'bg-blue-600/20 text-blue-400 border-blue-500/30',
}

const Badge = ({ className, variant = 'default', children, ...props }) => (
  <span
    className={cn(
      'inline-flex items-center rounded-md border px-2 py-0.5 text-xs font-medium',
      variants[variant],
      className
    )}
    {...props}
  >
    {children}
  </span>
)

export default Badge
