/**
 * Componente Card reutilizable
 */
import { cn } from '../../utils/cn'

export const Card = ({ className, children, ...props }) => (
  <div
    className={cn(
      'rounded-xl border border-secondary-800/50 bg-secondary-900/50 shadow-lg backdrop-blur-sm',
      className
    )}
    {...props}
  >
    {children}
  </div>
)

export const CardHeader = ({ className, children, ...props }) => (
  <div
    className={cn('border-b border-secondary-800/50 px-6 py-4', className)}
    {...props}
  >
    {children}
  </div>
)

export const CardTitle = ({ className, children, ...props }) => (
  <h3
    className={cn('text-lg font-semibold text-secondary-100', className)}
    {...props}
  >
    {children}
  </h3>
)

export const CardDescription = ({ className, children, ...props }) => (
  <p
    className={cn('text-sm text-secondary-400 mt-1', className)}
    {...props}
  >
    {children}
  </p>
)

export const CardContent = ({ className, children, ...props }) => (
  <div className={cn('p-6', className)} {...props}>
    {children}
  </div>
)

export const CardFooter = ({ className, children, ...props }) => (
  <div
    className={cn('border-t border-secondary-800/50 px-6 py-4', className)}
    {...props}
  >
    {children}
  </div>
)

export default Card
