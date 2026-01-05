/**
 * Modal para gestionar asignaciones de un cliente
 */
import { useState, useEffect } from 'react'
import { 
  Building2, 
  User, 
  UserPlus, 
  X, 
  Loader2,
  AlertTriangle
} from 'lucide-react'
import Modal from '../../../components/ui/Modal'
import Button from '../../../components/ui/Button'
import { Badge, Select } from '../../../components/ui'
import { 
  useAsignacionesCliente, 
  useAsignarAnalista, 
  useDesasignarAnalista 
} from '../hooks'
import { useUsuarios } from '../hooks'
import toast from 'react-hot-toast'

const AsignacionClienteModal = ({ 
  isOpen, 
  onClose, 
  cliente // { id, nombre, rut }
}) => {
  const [selectedUsuario, setSelectedUsuario] = useState('')
  
  // Queries
  const { data: asignaciones, isLoading: loadingAsignaciones } = useAsignacionesCliente(cliente?.id)
  const { data: todosUsuarios = [] } = useUsuarios()
  
  // Mutations
  const asignarAnalista = useAsignarAnalista()
  const desasignarAnalista = useDesasignarAnalista()
  
  // Reset al cerrar
  useEffect(() => {
    if (!isOpen) {
      setSelectedUsuario('')
    }
  }, [isOpen])
  
  // Filtrar usuarios disponibles para asignar (analistas y supervisores no asignados)
  const usuariosAsignados = asignaciones?.analistas?.map(a => a.usuario) || []
  const usuariosDisponibles = todosUsuarios.filter(
    u => (u.tipo_usuario === 'analista' || u.tipo_usuario === 'supervisor') && 
         u.is_active &&
         !usuariosAsignados.includes(u.id)
  )
  
  const handleAsignarUsuario = async () => {
    if (!selectedUsuario) return
    
    try {
      await asignarAnalista.mutateAsync({
        clienteId: cliente.id,
        usuarioId: parseInt(selectedUsuario),
        esPrincipal: usuariosAsignados.length === 0
      })
      setSelectedUsuario('')
      toast.success('Usuario asignado al cliente')
    } catch (error) {
      toast.error(error.response?.data?.error || 'Error al asignar usuario')
    }
  }
  
  const handleDesasignarUsuario = async (usuarioId) => {
    try {
      await desasignarAnalista.mutateAsync({
        clienteId: cliente.id,
        usuarioId
      })
      toast.success('Usuario desasignado')
    } catch (error) {
      toast.error('Error al desasignar usuario')
    }
  }
  
  if (!cliente) return null
  
  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Gestionar Asignaciones"
      size="lg"
    >
      <div className="space-y-6">
        {/* Info del cliente */}
        <div className="flex items-center gap-3 p-4 bg-secondary-800/50 rounded-lg">
          <div className="p-3 rounded-lg bg-primary-600/20">
            <Building2 className="h-6 w-6 text-primary-400" />
          </div>
          <div>
            <h3 className="font-semibold text-white">{cliente.nombre_display || cliente.nombre}</h3>
            <p className="text-sm text-secondary-400">{cliente.rut}</p>
          </div>
        </div>
        
        {loadingAsignaciones ? (
          <div className="flex items-center justify-center py-8">
            <Loader2 className="w-8 h-8 animate-spin text-primary-500" />
          </div>
        ) : (
          <div className="space-y-3">
            <h4 className="text-sm font-semibold text-secondary-400 uppercase tracking-wider flex items-center gap-2">
              <User className="w-4 h-4" />
              Usuarios Asignados ({asignaciones?.analistas?.length || 0})
            </h4>
            
            {/* Agregar usuario */}
            <div className="flex items-center gap-3">
              <div className="flex-1">
                <Select
                  value={selectedUsuario}
                  onChange={(e) => setSelectedUsuario(e.target.value)}
                  placeholder="Seleccionar usuario..."
                  options={[
                    { value: '', label: 'Seleccionar usuario para asignar...' },
                    ...usuariosDisponibles.map(u => ({
                      value: u.id.toString(),
                      label: `${u.nombre} ${u.apellido}`
                    }))
                  ]}
                />
              </div>
              <Button
                onClick={handleAsignarUsuario}
                disabled={!selectedUsuario || asignarAnalista.isPending}
                size="sm"
              >
                {asignarAnalista.isPending ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <UserPlus className="w-4 h-4" />
                )}
                Agregar
              </Button>
            </div>
            
            {/* Lista de usuarios asignados */}
            {asignaciones?.analistas?.length > 0 ? (
              <div className="space-y-2">
                {asignaciones.analistas.map((asig) => (
                  <div 
                    key={asig.id}
                    className="flex items-center justify-between p-3 bg-secondary-800 rounded-lg"
                  >
                    <div className="flex items-center gap-3">
                      <div className="w-8 h-8 rounded-full bg-gradient-to-br from-primary-500 to-primary-700 flex items-center justify-center">
                        <User className="w-4 h-4 text-white" />
                      </div>
                      <div>
                        <p className="font-medium text-white">
                          {asig.usuario_info?.nombre_completo || asig.usuario_nombre}
                        </p>
                        <p className="text-xs text-secondary-400">
                          {asig.usuario_info?.email}
                        </p>
                      </div>
                      {asig.es_principal && (
                        <Badge variant="success" className="ml-2">Principal</Badge>
                      )}
                    </div>
                    <button
                      onClick={() => handleDesasignarUsuario(asig.usuario)}
                      disabled={desasignarAnalista.isPending}
                      className="p-2 rounded-lg text-secondary-400 hover:text-danger-400 hover:bg-danger-500/10 transition-colors"
                      title="Desasignar"
                    >
                      <X className="w-4 h-4" />
                    </button>
                  </div>
                ))}
              </div>
            ) : (
              <div className="flex items-center gap-2 p-4 bg-warning-500/10 rounded-lg border border-warning-500/20">
                <AlertTriangle className="w-5 h-5 text-warning-400" />
                <span className="text-sm text-warning-400">
                  Este cliente no tiene usuarios asignados
                </span>
              </div>
            )}
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
