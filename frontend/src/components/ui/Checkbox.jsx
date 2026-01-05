/**
 * Componente Checkbox reutilizable
 */
import { forwardRef } from 'react'
import { Check } from 'lucide-react'
import { cn } from '../../utils/cn'

const Checkbox = forwardRef(({
  className,
  label,
  error,
  helperText,
  ...props
}, ref) => {
  return (
    <div className="w-full">
      <label className="flex items-center gap-3 cursor-pointer">
        <div className="relative">
          <input
            ref={ref}
            type="checkbox"
            className="sr-only peer"
            {...props}
          />
          <div className={cn(
            'w-5 h-5 rounded border-2 transition-all duration-200',
            'border-secondary-600 bg-secondary-800',
            'peer-checked:border-primary-500 peer-checked:bg-primary-600',
            'peer-focus:ring-2 peer-focus:ring-primary-500 peer-focus:ring-offset-2 peer-focus:ring-offset-secondary-900',
            'peer-disabled:opacity-50 peer-disabled:cursor-not-allowed',
            error && 'border-red-500',
            className
          )} />
          <Check className="absolute top-0.5 left-0.5 h-4 w-4 text-white opacity-0 peer-checked:opacity-100 transition-opacity" />
        </div>
        {label && (
          <span className="text-sm text-secondary-300">
            {label}
          </span>
        )}
      </label>
      {(error || helperText) && (
        <p className={cn(
          'mt-1.5 text-sm ml-8',
          error ? 'text-red-400' : 'text-secondary-500'
        )}>
          {error || helperText}
        </p>
      )}
    </div>
  )
})

Checkbox.displayName = 'Checkbox'

export default Checkbox
