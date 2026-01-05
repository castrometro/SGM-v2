/**
 * Componente Input reutilizable
 */
import { forwardRef } from 'react'
import { cn } from '../../utils/cn'

const Input = forwardRef(({
  className,
  type = 'text',
  label,
  error,
  helperText,
  icon: Icon,
  ...props
}, ref) => {
  return (
    <div className="w-full">
      {label && (
        <label className="block text-sm font-medium text-secondary-300 mb-1.5">
          {label}
          {props.required && <span className="text-red-400 ml-1">*</span>}
        </label>
      )}
      <div className="relative">
        {Icon && (
          <div className="absolute left-3 top-1/2 -translate-y-1/2 text-secondary-500">
            <Icon className="h-5 w-5" />
          </div>
        )}
        <input
          ref={ref}
          type={type}
          className={cn(
            'w-full px-4 py-2.5 rounded-lg transition-all duration-200',
            'bg-secondary-800 border border-secondary-700',
            'text-secondary-100 placeholder-secondary-500',
            'focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent',
            'disabled:opacity-50 disabled:cursor-not-allowed',
            error && 'border-red-500 focus:ring-red-500',
            Icon && 'pl-10',
            className
          )}
          {...props}
        />
      </div>
      {(error || helperText) && (
        <p className={cn(
          'mt-1.5 text-sm',
          error ? 'text-red-400' : 'text-secondary-500'
        )}>
          {error || helperText}
        </p>
      )}
    </div>
  )
})

Input.displayName = 'Input'

export default Input
