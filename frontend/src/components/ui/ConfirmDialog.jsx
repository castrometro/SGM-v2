/**
 * Componente ConfirmDialog para acciones destructivas
 */
import { AlertTriangle, Trash2 } from 'lucide-react'
import Modal from './Modal'
import Button from './Button'

const ConfirmDialog = ({
  isOpen,
  onClose,
  onConfirm,
  title = '¿Estás seguro?',
  description = 'Esta acción no se puede deshacer.',
  confirmText = 'Confirmar',
  cancelText = 'Cancelar',
  variant = 'danger', // 'danger' | 'warning' | 'default'
  loading = false,
}) => {
  const icons = {
    danger: <Trash2 className="h-6 w-6 text-red-400" />,
    warning: <AlertTriangle className="h-6 w-6 text-yellow-400" />,
    default: <AlertTriangle className="h-6 w-6 text-primary-400" />,
  }

  const buttonVariants = {
    danger: 'danger',
    warning: 'primary',
    default: 'primary',
  }

  return (
    <Modal isOpen={isOpen} onClose={onClose} size="sm">
      <div className="flex flex-col items-center text-center">
        <div className="p-3 rounded-full bg-secondary-800 mb-4">
          {icons[variant]}
        </div>
        <h3 className="text-lg font-semibold text-secondary-100 mb-2">
          {title}
        </h3>
        <p className="text-secondary-400 mb-6">
          {description}
        </p>
        <div className="flex items-center gap-3 w-full">
          <Button
            variant="outline"
            className="flex-1"
            onClick={onClose}
            disabled={loading}
          >
            {cancelText}
          </Button>
          <Button
            variant={buttonVariants[variant]}
            className="flex-1"
            onClick={onConfirm}
            loading={loading}
          >
            {confirmText}
          </Button>
        </div>
      </div>
    </Modal>
  )
}

export default ConfirmDialog
