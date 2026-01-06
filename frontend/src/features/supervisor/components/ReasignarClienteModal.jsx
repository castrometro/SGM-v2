/**
 * Modal para reasignar un cliente a otro analista del equipo
 * Issue #5: Vista de supervisor
 */
import { useState } from 'react'
import { X, ArrowRightLeft, Building2, UserCircle } from 'lucide-react'
import { Button, Select } from '../../../components/ui'

const ReasignarClienteModal = ({ 
  isOpen, 
  onClose, 
  cliente, 
  equipo = [], 
  onConfirm,
  isLoading 
}) => {
  const [nuevoUsuarioId, setNuevoUsuarioId] = useState('')

  if (!isOpen || !cliente) return null

  // Opciones de analistas del equipo (excluyendo el actual)
  const analistaOptions = equipo
    .filter(item => item.analista.id !== cliente.analista_actual?.id)
    .map(item => ({
      value: item.analista.id.toString(),
      label: `${item.analista.nombre} (${item.total_clientes} clientes)`
    }))

  const handleSubmit = (e) => {
    e.preventDefault()
    if (nuevoUsuarioId) {
      onConfirm(parseInt(nuevoUsuarioId))
    }
  }

  const analistaSeleccionado = equipo.find(
    item => item.analista.id.toString() === nuevoUsuarioId
  )

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
                <ArrowRightLeft className="h-5 w-5 text-primary-400" />
              </div>
              <div>
                <h2 className="text-lg font-semibold text-secondary-100">
                  Reasignar Cliente
                </h2>
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
            {/* Info del cliente */}
            <div className="p-3 rounded-lg bg-secondary-700/50">
              <div className="flex items-center gap-2 text-sm text-secondary-300">
                <Building2 className="h-4 w-4" />
                <span className="font-medium text-secondary-100">
                  {cliente.nombre_comercial || cliente.razon_social}
                </span>
              </div>
              <p className="text-xs text-secondary-500 mt-1">
                {cliente.rut}
              </p>
            </div>

            {/* Analista actual */}
            {cliente.analista_actual && (
              <div className="flex items-center gap-2 p-3 rounded-lg bg-secondary-700/30">
                <UserCircle className="h-5 w-5 text-secondary-400" />
                <div>
                  <p className="text-xs text-secondary-500">Asignado actualmente a:</p>
                  <p className="text-sm text-secondary-200">{cliente.analista_actual.nombre}</p>
                </div>
              </div>
            )}

            {/* Select nuevo analista */}
            <div>
              <label className="block text-sm font-medium text-secondary-300 mb-2">
                Reasignar a:
              </label>
              <Select
                value={nuevoUsuarioId}
                onChange={(e) => setNuevoUsuarioId(e.target.value)}
                options={analistaOptions}
                placeholder="Seleccionar analista..."
              />
            </div>

            {/* Preview del analista seleccionado */}
            {analistaSeleccionado && (
              <div className="p-3 rounded-lg bg-primary-600/10 border border-primary-600/30">
                <div className="flex items-center gap-2">
                  <UserCircle className="h-5 w-5 text-primary-400" />
                  <div>
                    <p className="text-sm font-medium text-primary-300">
                      {analistaSeleccionado.analista.nombre}
                    </p>
                    <p className="text-xs text-secondary-400">
                      {analistaSeleccionado.analista.email} • 
                      {analistaSeleccionado.total_clientes} clientes actuales
                    </p>
                  </div>
                </div>
              </div>
            )}

            {/* Actions */}
            <div className="flex gap-3 pt-4">
              <Button
                type="button"
                variant="outline"
                onClick={onClose}
                disabled={isLoading}
                className="flex-1"
              >
                Cancelar
              </Button>
              <Button
                type="submit"
                disabled={isLoading || !nuevoUsuarioId}
                className="flex-1"
              >
                {isLoading ? 'Reasignando...' : 'Confirmar'}
              </Button>
            </div>
          </form>
        </div>
      </div>
    </div>
  )
}

export default ReasignarClienteModal
