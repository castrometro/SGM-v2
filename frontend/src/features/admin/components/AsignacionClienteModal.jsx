/**
 * Modal simplificado para asignar UN usuario a un cliente
 * Issue #7: Un cliente = Un usuario asignado
 */
import { useState, useEffect } from 'react'
import { 
  Building2, 
  User, 
  UserCheck,
  UserX,
  X, 
  Loader2,
  AlertTriangle,
  ShieldCheck
} from 'lucide-react'
import Modal from '../../../components/ui/Modal'
import Button from '../../../components/ui/Button'
import { Badge, Select } from '../../../components/ui'
import { useInfoAsignacion, useAsignarUsuario, useDesasignarUsuario } from '../hooks'
import { useUsuarios } from '../hooks'
import { TIPO_USUARIO, PUEDEN_SER_ASIGNADOS_CLIENTE } from '../../../constants'
import toast from 'react-hot-toast'

const AsignacionClienteModal = ({ 
  isOpen, 
  onClose, 
  cliente // { id, nombre_display, rut }
}) => {
  const [selectedUsuario, setSelectedUsuario] = useState('')
  
  // Queries
  const { data: infoAsignacion, isLoading } = useInfoAsignacion(cliente?.id)
  const { data: todosUsuarios = [] } = useUsuarios()
  
  // Mutations
  const asignarUsuario = useAsignarUsuario()
  const desasignarUsuario = useDesasignarUsuario()
  
  // Reset al cerrar
  useEffect(() => {
    if (!isOpen) {
      setSelectedUsuario('')
    }
  }, [isOpen])
  
  // Filtrar usuarios disponibles (analistas y supervisores activos)
  const usuariosDisponibles = todosUsuarios.filter(
    u => PUEDEN_SER_ASIGNADOS_CLIENTE.includes(u.tipo_usuario) && u.is_active
  )
  
  const handleAsignarUsuario = async () => {
    if (!selectedUsuario) return
    
    try {
      await asignarUsuario.mutateAsync({
        clienteId: cliente.id,
        usuarioId: parseInt(selectedUsuario)
      })
      setSelectedUsuario('')
      toast.success('Usuario asignado al cliente')
    } catch (error) {
      toast.error(error.response?.data?.error || 'Error al asignar usuario')
    }
  }
  
  const handleDesasignarUsuario = async () => {
    try {
      await desasignarUsuario.mutateAsync({ clienteId: cliente.id })
      toast.success('Usuario desasignado')
    } catch (error) {
      toast.error('Error al desasignar usuario')
    }
  }
  
  if (!cliente) return null
  
  const usuarioAsignado = infoAsignacion?.usuario_asignado
  const supervisorHeredado = infoAsignacion?.supervisor_heredado
  
  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Asignar Usuario"
      size="md"
    >
      <div className="space-y-6">
        {/* Info del cliente */}
        <div className="flex items-center gap-3 p-4 bg-secondary-800/50 rounded-lg">
          <div className="p-3 rounded-lg bg-primary-600/20">
            <Building2 className="h-6 w-6 text-primary-400" />
          </div>
          <div>
            <h3 className="font-semibold text-white">{cliente.nombre_display || cliente.razon_social}</h3>
            <p className="text-sm text-secondary-400">{cliente.rut}</p>
          </div>
        </div>
        
        {isLoading ? (
          <div className="flex items-center justify-center py-8">
            <Loader2 className="w-8 h-8 animate-spin text-primary-500" />
          </div>
        ) : (
          <div className="space-y-4">
            {/* Usuario asignado actual */}
            <div className="space-y-3">
              <h4 className="text-sm font-semibold text-secondary-400 uppercase tracking-wider flex items-center gap-2">
                <UserCheck className="w-4 h-4" />
                Usuario Asignado
              </h4>
              
              {usuarioAsignado ? (
                <div className="flex items-center justify-between p-4 bg-secondary-800 rounded-lg">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-full bg-gradient-to-br from-primary-500 to-primary-700 flex items-center justify-center">
                      <User className="w-5 h-5 text-white" />
                    </div>
                    <div>
                      <p className="font-medium text-white">{usuarioAsignado.nombre}</p>
                      <p className="text-xs text-secondary-400">{usuarioAsignado.email}</p>
                    </div>
                    <Badge 
                      variant={usuarioAsignado.tipo_usuario === TIPO_USUARIO.SUPERVISOR ? 'primary' : 'secondary'}
                      className="ml-2"
                    >
                      {usuarioAsignado.tipo_usuario === TIPO_USUARIO.SUPERVISOR ? 'Supervisor' : 'Analista'}
                    </Badge>
                  </div>
                  <button
                    onClick={handleDesasignarUsuario}
                    disabled={desasignarUsuario.isPending}
                    className="p-2 rounded-lg text-secondary-400 hover:text-danger-400 hover:bg-danger-500/10 transition-colors"
                    title="Desasignar"
                  >
                    {desasignarUsuario.isPending ? (
                      <Loader2 className="w-4 h-4 animate-spin" />
                    ) : (
                      <X className="w-4 h-4" />
                    )}
                  </button>
                </div>
              ) : (
                <div className="flex items-center gap-2 p-4 bg-warning-500/10 rounded-lg border border-warning-500/20">
                  <AlertTriangle className="w-5 h-5 text-warning-400" />
                  <span className="text-sm text-warning-400">
                    Este cliente no tiene usuario asignado
                  </span>
                </div>
              )}
            </div>
            
            {/* Supervisor heredado (si el asignado es analista) */}
            {supervisorHeredado && (
              <div className="space-y-3">
                <h4 className="text-sm font-semibold text-secondary-400 uppercase tracking-wider flex items-center gap-2">
                  <ShieldCheck className="w-4 h-4" />
                  Supervisor con Acceso Heredado
                </h4>
                <div className="flex items-center gap-3 p-3 bg-primary-500/10 rounded-lg border border-primary-500/20">
                  <div className="w-8 h-8 rounded-full bg-primary-600/30 flex items-center justify-center">
                    <ShieldCheck className="w-4 h-4 text-primary-400" />
                  </div>
                  <div>
                    <p className="font-medium text-primary-300">{supervisorHeredado.nombre}</p>
                    <p className="text-xs text-primary-400/70">{supervisorHeredado.email}</p>
                  </div>
                </div>
                <p className="text-xs text-secondary-500 italic">
                  Este supervisor hereda acceso automáticamente porque supervisa al analista asignado.
                </p>
              </div>
            )}
            
            {/* Asignar nuevo usuario */}
            <div className="space-y-3 pt-4 border-t border-secondary-700">
              <h4 className="text-sm font-semibold text-secondary-400 uppercase tracking-wider flex items-center gap-2">
                <UserX className="w-4 h-4" />
                {usuarioAsignado ? 'Cambiar Usuario' : 'Asignar Usuario'}
              </h4>
              <div className="flex items-center gap-3">
                <div className="flex-1">
                  <Select
                    value={selectedUsuario}
                    onChange={(e) => setSelectedUsuario(e.target.value)}
                    options={[
                      { value: '', label: 'Seleccionar usuario...' },
                      ...usuariosDisponibles.map(u => ({
                        value: u.id.toString(),
                        label: `${u.nombre} ${u.apellido} (${u.tipo_usuario})`
                      }))
                    ]}
                  />
                </div>
                <Button
                  onClick={handleAsignarUsuario}
                  disabled={!selectedUsuario || asignarUsuario.isPending}
                  size="sm"
                >
                  {asignarUsuario.isPending ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <UserCheck className="w-4 h-4" />
                  )}
                  {usuarioAsignado ? 'Cambiar' : 'Asignar'}
                </Button>
              </div>
            </div>
          </div>
        )}
        
        {/* Acciones */}
        <div className="flex justify-end pt-4 border-t border-secondary-800">
          <Button variant="outline" onClick={onClose}>
            Cerrar
          </Button>
        </div>
      </div>
    </Modal>
  )
}

export default AsignacionClienteModal
