/**
 * Componente Select reutilizable
 */
import { forwardRef } from 'react'
import { ChevronDown } from 'lucide-react'
import { cn } from '../../utils/cn'

const Select = forwardRef(({
  className,
  label,
  error,
  helperText,
  options = [],
  placeholder = 'Seleccione una opción',
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
        <select
          ref={ref}
          className={cn(
            'w-full px-4 py-2.5 rounded-lg transition-all duration-200 appearance-none',
            'bg-secondary-800 border border-secondary-700',
            'text-secondary-100',
            'focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent',
            'disabled:opacity-50 disabled:cursor-not-allowed',
            error && 'border-red-500 focus:ring-red-500',
            className
          )}
          {...props}
        >
          <option value="" className="text-secondary-500">
            {placeholder}
          </option>
          {options.map((option) => (
            <option 
              key={option.value} 
              value={option.value}
              className="bg-secondary-800"
            >
              {option.label}
            </option>
          ))}
        </select>
        <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 h-5 w-5 text-secondary-500 pointer-events-none" />
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

Select.displayName = 'Select'

export default Select
