/**
 * Modal para asignar supervisor a un analista
 * Issue #4: Asignación de Analistas a Supervisores
 */
import { useState, useEffect } from 'react'
import { X, UserCog, Users, AlertCircle } from 'lucide-react'
import { Button, Select } from '../../../components/ui'
import { useSupervisores, useAsignarSupervisor } from '../hooks/useUsuarios'
import { toast } from 'react-hot-toast'

const AsignacionSupervisorModal = ({ isOpen, onClose, analista }) => {
  const [supervisorId, setSupervisorId] = useState('')
  
  const { data: supervisores = [], isLoading: loadingSupervisores } = useSupervisores()
  const asignarMutation = useAsignarSupervisor()

  // Inicializar con el supervisor actual
  useEffect(() => {
    if (analista?.supervisor) {
      setSupervisorId(analista.supervisor.toString())
    } else {
      setSupervisorId('')
    }
  }, [analista])

  if (!isOpen || !analista) return null

  const handleSubmit = async (e) => {
    e.preventDefault()
    
    try {
      await asignarMutation.mutateAsync({
        analistaId: analista.id,
        supervisorId: supervisorId ? parseInt(supervisorId) : null
      })
      toast.success(
        supervisorId 
          ? `Supervisor asignado a ${analista.nombre_completo || analista.nombre}`
          : `Supervisor removido de ${analista.nombre_completo || analista.nombre}`
      )
      onClose()
    } catch (error) {
      toast.error(error.response?.data?.error || 'Error al asignar supervisor')
    }
  }

  const handleRemoveSupervisor = async () => {
    try {
      await asignarMutation.mutateAsync({
        analistaId: analista.id,
        supervisorId: null
      })
      toast.success(`Supervisor removido de ${analista.nombre_completo || analista.nombre}`)
      onClose()
    } catch (error) {
      toast.error(error.response?.data?.error || 'Error al remover supervisor')
    }
  }

  const supervisorOptions = supervisores.map(s => ({
    value: s.id.toString(),
    label: `${s.nombre_completo || `${s.nombre} ${s.apellido}`} (${s.tipo_usuario})`
  }))

  const supervisorActual = analista?.supervisor_info || 
    supervisores.find(s => s.id === analista?.supervisor)

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      {/* Backdrop */}
      <div 
        className="fixed inset-0 bg-black/60 backdrop-blur-sm"
        onClick={onClose}
      />

      {/* Modal */}
      <div className="relative min-h-screen flex items-center justify-center p-4">
        <div className="relative bg-secondary-800 rounded-xl shadow-2xl w-full max-w-md border border-secondary-700">
          {/* Header */}
          <div className="flex items-center justify-between p-4 border-b border-secondary-700">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-primary-600/20">
                <UserCog className="h-5 w-5 text-primary-400" />
              </div>
              <div>
                <h2 className="text-lg font-semibold text-secondary-100">
                  Asignar Supervisor
                </h2>
                <p className="text-sm text-secondary-400">
                  {analista.nombre_completo || `${analista.nombre} ${analista.apellido}`}
                </p>
              </div>
            </div>
            <button
              onClick={onClose}
              className="p-2 hover:bg-secondary-700 rounded-lg transition-colors"
            >
              <X className="h-5 w-5 text-secondary-400" />
            </button>
          </div>

          {/* Content */}
          <form onSubmit={handleSubmit} className="p-4 space-y-4">
            {/* Info del analista */}
            <div className="p-3 rounded-lg bg-secondary-700/50">
              <div className="flex items-center gap-2 text-sm text-secondary-300">
                <Users className="h-4 w-4" />
                <span>Analista: <strong className="text-secondary-100">{analista.email}</strong></span>
              </div>
              {supervisorActual && (
                <div className="mt-2 flex items-center gap-2 text-sm text-secondary-400">
                  <AlertCircle className="h-4 w-4 text-amber-400" />
                  <span>
                    Supervisor actual: <strong className="text-amber-300">
                      {supervisorActual.nombre_completo || `${supervisorActual.nombre} ${supervisorActual.apellido}`}
                    </strong>
                  </span>
                </div>
              )}
            </div>

            {/* Select supervisor */}
            <div>
              <label className="block text-sm font-medium text-secondary-300 mb-2">
                Seleccionar Supervisor
              </label>
              <Select
                value={supervisorId}
                onChange={(e) => setSupervisorId(e.target.value)}
                options={supervisorOptions}
                placeholder={loadingSupervisores ? "Cargando..." : "Seleccionar supervisor..."}
                disabled={loadingSupervisores}
              />
            </div>

            {/* Actions */}
            <div className="flex gap-3 pt-4">
              {analista.supervisor && (
                <Button
                  type="button"
                  variant="danger"
                  onClick={handleRemoveSupervisor}
                  disabled={asignarMutation.isPending}
                  className="flex-1"
                >
                  Remover Supervisor
                </Button>
              )}
              <Button
                type="button"
                variant="outline"
                onClick={onClose}
                disabled={asignarMutation.isPending}
                className={analista.supervisor ? '' : 'flex-1'}
              >
                Cancelar
              </Button>
              <Button
                type="submit"
                disabled={asignarMutation.isPending || !supervisorId}
                className={analista.supervisor ? '' : 'flex-1'}
              >
                {asignarMutation.isPending ? 'Guardando...' : 'Asignar'}
              </Button>
            </div>
          </form>
        </div>
      </div>
    </div>
  )
}

export default AsignacionSupervisorModal
