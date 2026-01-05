/**
 * Componente Modal reutilizable
 */
import { Fragment, useEffect } from 'react'
import { X } from 'lucide-react'
import { cn } from '../../utils/cn'

const Modal = ({
  isOpen,
  onClose,
  title,
  description,
  children,
  size = 'md',
  className,
}) => {
  // Cerrar con Escape
  useEffect(() => {
    const handleEscape = (e) => {
      if (e.key === 'Escape') onClose()
    }
    
    if (isOpen) {
      document.addEventListener('keydown', handleEscape)
      document.body.style.overflow = 'hidden'
    }
    
    return () => {
      document.removeEventListener('keydown', handleEscape)
      document.body.style.overflow = 'unset'
    }
  }, [isOpen, onClose])

  if (!isOpen) return null

  const sizes = {
    sm: 'max-w-md',
    md: 'max-w-lg',
    lg: 'max-w-2xl',
    xl: 'max-w-4xl',
    full: 'max-w-[90vw]',
  }

  return (
    <Fragment>
      {/* Backdrop */}
      <div 
        className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 transition-opacity"
        onClick={onClose}
      />
      
      {/* Modal */}
      <div className="fixed inset-0 z-50 overflow-y-auto">
        <div className="flex min-h-full items-center justify-center p-4">
          <div 
            className={cn(
              'relative w-full transform transition-all',
              'bg-secondary-900 border border-secondary-700 rounded-xl shadow-2xl',
              sizes[size],
              className
            )}
            onClick={(e) => e.stopPropagation()}
          >
            {/* Header */}
            <div className="flex items-start justify-between p-6 border-b border-secondary-800">
              <div>
                <h2 className="text-xl font-semibold text-secondary-100">
                  {title}
                </h2>
                {description && (
                  <p className="mt-1 text-sm text-secondary-400">
                    {description}
                  </p>
                )}
              </div>
              <button
                onClick={onClose}
                className="p-2 rounded-lg text-secondary-400 hover:text-secondary-100 hover:bg-secondary-800 transition-colors"
              >
                <X className="h-5 w-5" />
              </button>
            </div>
            
            {/* Content */}
            <div className="p-6">
              {children}
            </div>
          </div>
        </div>
      </div>
    </Fragment>
  )
}

// Sub-componentes para estructura
const ModalFooter = ({ children, className }) => (
  <div className={cn(
    'flex items-center justify-end gap-3 pt-6 mt-6 border-t border-secondary-800',
    className
  )}>
    {children}
  </div>
)

Modal.Footer = ModalFooter

export default Modal
