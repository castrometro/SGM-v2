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
  Briefcase,
  Loader2,
  UserCog
} from 'lucide-react'
import Table from '../../../components/ui/Table'
import Badge from '../../../components/ui/Badge'
import ConfirmDialog from '../../../components/ui/ConfirmDialog'

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
  onAsignarSupervisor,
  currentUserId,
}) => {
  const [confirmDialog, setConfirmDialog] = useState({
    open: false,
    type: null,
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
        description: `¿Está seguro de eliminar al usuario "${usuario.nombre} ${usuario.apellido}"? Esta acción no se puede deshacer.`,
        variant: 'danger',
        confirmText: 'Eliminar',
      },
      toggleActive: {
        title: usuario.is_active ? 'Desactivar Usuario' : 'Activar Usuario',
        description: usuario.is_active 
          ? `¿Desea desactivar al usuario "${usuario.nombre} ${usuario.apellido}"? No podrá acceder al sistema.`
          : `¿Desea activar al usuario "${usuario.nombre} ${usuario.apellido}"?`,
        variant: usuario.is_active ? 'warning' : 'default',
        confirmText: usuario.is_active ? 'Desactivar' : 'Activar',
      },
      resetPassword: {
        title: 'Resetear Contraseña',
        description: `¿Desea resetear la contraseña de "${usuario.nombre} ${usuario.apellido}"? Se generará una nueva contraseña temporal.`,
        variant: 'warning',
        confirmText: 'Resetear',
      },
    }

    return configs[type] || {}
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="w-8 h-8 animate-spin text-primary-500" />
      </div>
    )
  }

  return (
    <>
      <Table>
        <Table.Header>
          <Table.Row hoverable={false}>
            <Table.Head>Usuario</Table.Head>
            <Table.Head>Rol</Table.Head>
            <Table.Head>Cargo</Table.Head>
            <Table.Head>Supervisor</Table.Head>
            <Table.Head>Estado</Table.Head>
            <Table.Head align="right">Acciones</Table.Head>
          </Table.Row>
        </Table.Header>
        <Table.Body>
          {usuarios.length === 0 ? (
            <Table.Empty message="No hay usuarios registrados" colSpan={6} />
          ) : (
            usuarios.map((usuario) => {
              const tipoConfig = tipoUsuarioBadge[usuario.tipo_usuario] || tipoUsuarioBadge.analista
              const TipoIcon = tipoConfig.icon
              const isCurrentUser = usuario.id === currentUserId

              return (
                <Table.Row key={usuario.id}>
                  {/* Usuario */}
                  <Table.Cell>
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
                  </Table.Cell>

                  {/* Rol */}
                  <Table.Cell>
                    <Badge variant={tipoConfig.variant} className="flex items-center gap-1 w-fit">
                      <TipoIcon className="w-3.5 h-3.5" />
                      {tipoConfig.label}
                    </Badge>
                  </Table.Cell>

                  {/* Cargo */}
                  <Table.Cell>
                    {usuario.cargo || (
                      <span className="text-secondary-500 italic">Sin cargo</span>
                    )}
                  </Table.Cell>

                  {/* Supervisor */}
                  <Table.Cell>
                    {usuario.tipo_usuario !== 'analista' ? (
                      <span className="text-secondary-500">-</span>
                    ) : usuario.supervisor_info ? (
                      <button 
                        onClick={() => onAsignarSupervisor?.(usuario)}
                        className="text-secondary-300 hover:text-primary-400 transition-colors underline-offset-2 hover:underline"
                        title="Cambiar supervisor"
                      >
                        {usuario.supervisor_info.nombre} {usuario.supervisor_info.apellido}
                      </button>
                    ) : (
                      <button 
                        onClick={() => onAsignarSupervisor?.(usuario)}
                        className="text-amber-500 hover:text-amber-400 transition-colors italic"
                        title="Asignar supervisor"
                      >
                        Sin asignar
                      </button>
                    )}
                  </Table.Cell>

                  {/* Estado */}
                  <Table.Cell>
                    <Badge 
                      variant={usuario.is_active ? 'success' : 'secondary'}
                      className="flex items-center gap-1 w-fit"
                    >
                      {usuario.is_active ? (
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
                  </Table.Cell>

                  {/* Acciones */}
                  <Table.Cell align="right">
                    <div className="flex items-center justify-end gap-1">
                      <button
                        onClick={() => onEdit?.(usuario)}
                        className="p-2 rounded-lg text-secondary-400 hover:text-white hover:bg-secondary-700 transition-colors"
                        title="Editar"
                      >
                        <Pencil className="w-4 h-4" />
                      </button>
                      
                      {/* Botón asignar supervisor - solo para analistas */}
                      {usuario.tipo_usuario === 'analista' && (
                        <button
                          onClick={() => onAsignarSupervisor?.(usuario)}
                          className="p-2 rounded-lg text-secondary-400 hover:text-primary-400 hover:bg-primary-500/10 transition-colors"
                          title="Asignar supervisor"
                        >
                          <UserCog className="w-4 h-4" />
                        </button>
                      )}
                      
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
                  </Table.Cell>
                </Table.Row>
              )
            })
          )}
        </Table.Body>
      </Table>
      
      <ConfirmDialog
        isOpen={confirmDialog.open}
        onClose={() => setConfirmDialog({ open: false, type: null, usuario: null })}
        onConfirm={handleConfirm}
        {...getConfirmDialogProps()}
      />
    </>
  )
}

export default UsuariosTable
