/**
 * Tabla de Usuarios con acciones
 */
import { useState } from 'react'
import { 
  User,
  Pencil, 
  Key, 
  Trash2,
  CheckCircle,
  XCircle,
  Shield,
  Users,
  Briefcase
} from 'lucide-react'
import { Table, Badge, ConfirmDialog } from '../../../components/ui'

// Configuración de badges por tipo de usuario
const tipoUsuarioBadge = {
  gerente: { variant: 'danger', icon: Shield, label: 'Gerente' },
  supervisor: { variant: 'warning', icon: Users, label: 'Supervisor' },
  analista: { variant: 'info', icon: Briefcase, label: 'Analista' },
}

const UsuariosTable = ({
  usuarios = [],
  isLoading = false,
  onEdit,
  onToggleActive,
  onResetPassword,
  onDelete,
  currentUserId, // ID del usuario actual para evitar auto-eliminación
}) => {
  const [confirmDialog, setConfirmDialog] = useState({
    open: false,
    type: null, // 'delete' | 'toggleActive' | 'resetPassword'
    usuario: null,
  })

  const handleAction = (type, usuario) => {
    setConfirmDialog({ open: true, type, usuario })
  }

  const handleConfirm = async () => {
    const { type, usuario } = confirmDialog
    
    switch (type) {
      case 'delete':
        await onDelete?.(usuario.id)
        break
      case 'toggleActive':
        await onToggleActive?.(usuario.id)
        break
      case 'resetPassword':
        await onResetPassword?.(usuario.id)
        break
    }
    
    setConfirmDialog({ open: false, type: null, usuario: null })
  }

  const getConfirmDialogProps = () => {
    const { type, usuario } = confirmDialog
    
    if (!usuario) return {}

    const configs = {
      delete: {
        title: 'Eliminar Usuario',
        message: `¿Está seguro de eliminar al usuario "${usuario.nombre} ${usuario.apellido}"? Esta acción no se puede deshacer.`,
        variant: 'danger',
        confirmText: 'Eliminar',
      },
      toggleActive: {
        title: usuario.is_active ? 'Desactivar Usuario' : 'Activar Usuario',
        message: usuario.is_active 
          ? `¿Desea desactivar al usuario "${usuario.nombre} ${usuario.apellido}"? No podrá acceder al sistema.`
          : `¿Desea activar al usuario "${usuario.nombre} ${usuario.apellido}"?`,
        variant: usuario.is_active ? 'warning' : 'info',
        confirmText: usuario.is_active ? 'Desactivar' : 'Activar',
      },
      resetPassword: {
        title: 'Resetear Contraseña',
        message: `¿Desea resetear la contraseña de "${usuario.nombre} ${usuario.apellido}"? Se generará una nueva contraseña temporal.`,
        variant: 'warning',
        confirmText: 'Resetear',
      },
    }

    return configs[type] || {}
  }

  const columns = [
    {
      key: 'nombre_completo',
      header: 'Usuario',
      render: (_, usuario) => (
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-full bg-gradient-to-br from-primary-500 to-primary-700 flex items-center justify-center shadow-lg">
            <User className="w-5 h-5 text-white" />
          </div>
          <div>
            <p className="font-medium text-white">
              {usuario.nombre} {usuario.apellido}
            </p>
            <p className="text-sm text-secondary-400">{usuario.email}</p>
          </div>
        </div>
      ),
    },
    {
      key: 'tipo_usuario',
      header: 'Rol',
      render: (tipo) => {
        const config = tipoUsuarioBadge[tipo] || tipoUsuarioBadge.analista
        const Icon = config.icon
        return (
          <Badge variant={config.variant} className="flex items-center gap-1 w-fit">
            <Icon className="w-3.5 h-3.5" />
            {config.label}
          </Badge>
        )
      },
    },
    {
      key: 'cargo',
      header: 'Cargo',
      render: (cargo) => cargo || (
        <span className="text-secondary-500 italic">Sin cargo</span>
      ),
    },
    {
      key: 'supervisor_info',
      header: 'Supervisor',
      render: (_, usuario) => {
        if (usuario.tipo_usuario !== 'analista') {
          return <span className="text-secondary-500">-</span>
        }
        return usuario.supervisor_info ? (
          <span className="text-secondary-300">
            {usuario.supervisor_info.nombre} {usuario.supervisor_info.apellido}
          </span>
        ) : (
          <span className="text-secondary-500 italic">Sin asignar</span>
        )
      },
    },
    {
      key: 'is_active',
      header: 'Estado',
      render: (isActive) => (
        <Badge 
          variant={isActive ? 'success' : 'secondary'}
          className="flex items-center gap-1 w-fit"
        >
          {isActive ? (
            <>
              <CheckCircle className="w-3.5 h-3.5" />
              Activo
            </>
          ) : (
            <>
              <XCircle className="w-3.5 h-3.5" />
              Inactivo
            </>
          )}
        </Badge>
      ),
    },
    {
      key: 'acciones',
      header: 'Acciones',
      render: (_, usuario) => {
        const isCurrentUser = usuario.id === currentUserId
        
        return (
          <div className="flex items-center gap-1">
            <button
              onClick={() => onEdit?.(usuario)}
              className="p-2 rounded-lg text-secondary-400 hover:text-white hover:bg-secondary-700 transition-colors"
              title="Editar"
            >
              <Pencil className="w-4 h-4" />
            </button>
            
            <button
              onClick={() => handleAction('toggleActive', usuario)}
              disabled={isCurrentUser}
              className={`p-2 rounded-lg transition-colors ${
                isCurrentUser 
                  ? 'text-secondary-600 cursor-not-allowed' 
                  : usuario.is_active
                    ? 'text-secondary-400 hover:text-warning-400 hover:bg-warning-500/10'
                    : 'text-secondary-400 hover:text-success-400 hover:bg-success-500/10'
              }`}
              title={usuario.is_active ? 'Desactivar' : 'Activar'}
            >
              {usuario.is_active ? (
                <XCircle className="w-4 h-4" />
              ) : (
                <CheckCircle className="w-4 h-4" />
              )}
            </button>
            
            <button
              onClick={() => handleAction('resetPassword', usuario)}
              className="p-2 rounded-lg text-secondary-400 hover:text-warning-400 hover:bg-warning-500/10 transition-colors"
              title="Resetear contraseña"
            >
              <Key className="w-4 h-4" />
            </button>
            
            <button
              onClick={() => handleAction('delete', usuario)}
              disabled={isCurrentUser}
              className={`p-2 rounded-lg transition-colors ${
                isCurrentUser 
                  ? 'text-secondary-600 cursor-not-allowed' 
                  : 'text-secondary-400 hover:text-danger-400 hover:bg-danger-500/10'
              }`}
              title={isCurrentUser ? 'No puede eliminar su propio usuario' : 'Eliminar'}
            >
              <Trash2 className="w-4 h-4" />
            </button>
          </div>
        )
      },
    },
  ]

  return (
    <>
      <Table
        columns={columns}
        data={usuarios}
        loading={isLoading}
        emptyMessage="No hay usuarios registrados"
      />
      
      <ConfirmDialog
        open={confirmDialog.open}
        onClose={() => setConfirmDialog({ open: false, type: null, usuario: null })}
        onConfirm={handleConfirm}
        {...getConfirmDialogProps()}
      />
    </>
  )
}

export default UsuariosTable
