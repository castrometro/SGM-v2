/**
 * Modal para gestionar asignaciones de un cliente
 */
import { useState, useEffect } from 'react'
import { 
  Building2, 
  User, 
  Users, 
  UserPlus, 
  X, 
  Check,
  Loader2,
  AlertTriangle
} from 'lucide-react'
import Modal from '../../../components/ui/Modal'
import Button from '../../../components/ui/Button'
import { Badge, Select } from '../../../components/ui'
import { 
  useAsignacionesCliente, 
  useAsignarSupervisor, 
  useAsignarAnalista, 
  useDesasignarAnalista 
} from '../hooks'
import { useUsuarios, useSupervisores } from '../hooks'
import toast from 'react-hot-toast'

const AsignacionClienteModal = ({ 
  open, 
  onClose, 
  cliente // { id, nombre, rut }
}) => {
  const [selectedAnalista, setSelectedAnalista] = useState('')
  
  // Queries
  const { data: asignaciones, isLoading: loadingAsignaciones } = useAsignacionesCliente(cliente?.id)
  const { data: todosUsuarios = [] } = useUsuarios()
  const { data: supervisores = [] } = useSupervisores()
  
  // Mutations
  const asignarSupervisor = useAsignarSupervisor()
  const asignarAnalista = useAsignarAnalista()
  const desasignarAnalista = useDesasignarAnalista()
  
  // Filtrar analistas disponibles (no asignados ya)
  const analistasAsignados = asignaciones?.analistas?.map(a => a.usuario) || []
  const analistasDisponibles = todosUsuarios.filter(
    u => (u.tipo_usuario === 'analista' || u.tipo_usuario === 'supervisor') && 
         u.is_active &&
         !analistasAsignados.includes(u.id)
  )
  
  const handleAsignarSupervisor = async (supervisorId) => {
    try {
      await asignarSupervisor.mutateAsync({
        clienteId: cliente.id,
        supervisorId: supervisorId || null
      })
      toast.success(supervisorId ? 'Supervisor asignado' : 'Supervisor desasignado')
    } catch (error) {
      toast.error('Error al asignar supervisor')
    }
  }
  
  const handleAsignarAnalista = async () => {
    if (!selectedAnalista) return
    
    try {
      await asignarAnalista.mutateAsync({
        clienteId: cliente.id,
        usuarioId: parseInt(selectedAnalista),
        esPrincipal: analistasAsignados.length === 0 // El primero es principal
      })
      setSelectedAnalista('')
      toast.success('Analista asignado')
    } catch (error) {
      toast.error(error.response?.data?.error || 'Error al asignar analista')
    }
  }
  
  const handleDesasignarAnalista = async (usuarioId) => {
    try {
      await desasignarAnalista.mutateAsync({
        clienteId: cliente.id,
        usuarioId
      })
      toast.success('Analista desasignado')
    } catch (error) {
      toast.error('Error al desasignar analista')
    }
  }
  
  if (!cliente) return null
  
  return (
    <Modal
      open={open}
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
            <h3 className="font-semibold text-white">{cliente.nombre}</h3>
            <p className="text-sm text-secondary-400">{cliente.rut}</p>
          </div>
        </div>
        
        {loadingAsignaciones ? (
          <div className="flex items-center justify-center py-8">
            <Loader2 className="w-8 h-8 animate-spin text-primary-500" />
          </div>
        ) : (
          <>
            {/* Sección: Supervisor */}
            <div className="space-y-3">
              <h4 className="text-sm font-semibold text-secondary-400 uppercase tracking-wider flex items-center gap-2">
                <Users className="w-4 h-4" />
                Supervisor Responsable
              </h4>
              
              <div className="flex items-center gap-3">
                <div className="flex-1">
                  <Select
                    value={asignaciones?.supervisor?.id || ''}
                    onChange={(e) => handleAsignarSupervisor(e.target.value)}
                    disabled={asignarSupervisor.isPending}
                    options={[
                      { value: '', label: 'Sin supervisor asignado' },
                      ...supervisores.map(s => ({
                        value: s.id,
                        label: `${s.nombre} ${s.apellido}`
                      }))
                    ]}
                  />
                </div>
                {asignarSupervisor.isPending && (
                  <Loader2 className="w-5 h-5 animate-spin text-primary-500" />
                )}
              </div>
              
              {asignaciones?.supervisor && (
                <div className="flex items-center gap-2 p-2 bg-success-500/10 rounded-lg border border-success-500/20">
                  <Check className="w-4 h-4 text-success-400" />
                  <span className="text-sm text-success-400">
                    {asignaciones.supervisor.nombre} está a cargo de este cliente
                  </span>
                </div>
              )}
            </div>
            
            {/* Sección: Analistas */}
            <div className="space-y-3">
              <h4 className="text-sm font-semibold text-secondary-400 uppercase tracking-wider flex items-center gap-2">
                <User className="w-4 h-4" />
                Analistas Asignados ({asignaciones?.analistas?.length || 0})
              </h4>
              
              {/* Agregar analista */}
              <div className="flex items-center gap-3">
                <div className="flex-1">
                  <Select
                    value={selectedAnalista}
                    onChange={(e) => setSelectedAnalista(e.target.value)}
                    placeholder="Seleccionar analista..."
                    options={[
                      { value: '', label: 'Seleccionar analista...' },
                      ...analistasDisponibles.map(a => ({
                        value: a.id,
                        label: `${a.nombre} ${a.apellido} (${a.tipo_usuario})`
                      }))
                    ]}
                  />
                </div>
                <Button
                  onClick={handleAsignarAnalista}
                  disabled={!selectedAnalista || asignarAnalista.isPending}
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
              
              {/* Lista de analistas asignados */}
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
                        onClick={() => handleDesasignarAnalista(asig.usuario)}
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
                    Este cliente no tiene analistas asignados
                  </span>
                </div>
              )}
            </div>
          </>
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
