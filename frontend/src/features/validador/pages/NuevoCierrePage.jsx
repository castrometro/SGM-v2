/**
 * Página para crear un nuevo cierre
 */
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery, useMutation } from '@tanstack/react-query'
import { ArrowLeft, Calendar, Building2 } from 'lucide-react'
import toast from 'react-hot-toast'
import api from '../../../api/axios'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../../../components/ui'
import Button from '../../../components/ui/Button'

const MESES = [
  { value: 1, label: 'Enero' },
  { value: 2, label: 'Febrero' },
  { value: 3, label: 'Marzo' },
  { value: 4, label: 'Abril' },
  { value: 5, label: 'Mayo' },
  { value: 6, label: 'Junio' },
  { value: 7, label: 'Julio' },
  { value: 8, label: 'Agosto' },
  { value: 9, label: 'Septiembre' },
  { value: 10, label: 'Octubre' },
  { value: 11, label: 'Noviembre' },
  { value: 12, label: 'Diciembre' },
]

const NuevoCierrePage = () => {
  const navigate = useNavigate()
  const currentYear = new Date().getFullYear()
  const currentMonth = new Date().getMonth() + 1

  const [formData, setFormData] = useState({
    cliente: '',
    mes: currentMonth,
    anio: currentYear,
  })

  // Obtener clientes asignados al usuario
  const { data: clientes = [], isLoading: loadingClientes } = useQuery({
    queryKey: ['mis-clientes'],
    queryFn: async () => {
      const { data } = await api.get('/v1/core/clientes/')
      return data.results || data
    },
  })

  // Mutation para crear cierre
  const createCierre = useMutation({
    mutationFn: async (data) => {
      const response = await api.post('/v1/validador/cierres/', data)
      return response.data
    },
    onSuccess: (data) => {
      toast.success('Cierre creado exitosamente')
      navigate(`/validador/cierre/${data.id}`)
    },
    onError: (error) => {
      const message = error.response?.data?.detail || 
                     error.response?.data?.non_field_errors?.[0] ||
                     'Error al crear el cierre'
      toast.error(message)
    },
  })

  const handleSubmit = (e) => {
    e.preventDefault()
    if (!formData.cliente) {
      toast.error('Selecciona un cliente')
      return
    }
    createCierre.mutate(formData)
  }

  // Años disponibles (actual y anterior)
  const years = [currentYear, currentYear - 1]

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <button 
          onClick={() => navigate(-1)}
          className="p-2 rounded-lg hover:bg-secondary-800 transition-colors"
        >
          <ArrowLeft className="h-5 w-5 text-secondary-400" />
        </button>
        <div>
          <h1 className="text-2xl font-bold text-secondary-100">Nuevo Cierre</h1>
          <p className="text-secondary-400 mt-1">Inicia un nuevo proceso de validación</p>
        </div>
      </div>

      {/* Formulario */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Calendar className="h-5 w-5" />
            Datos del Cierre
          </CardTitle>
          <CardDescription>
            Selecciona el cliente y el período para el cierre de nómina
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Cliente */}
            <div className="space-y-2">
              <label className="block text-sm font-medium text-secondary-200">
                Cliente
              </label>
              <div className="relative">
                <Building2 className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-secondary-500" />
                <select
                  value={formData.cliente}
                  onChange={(e) => setFormData({ ...formData, cliente: e.target.value })}
                  className="w-full pl-10 pr-4 py-2.5 bg-secondary-800 border border-secondary-700 rounded-lg text-secondary-100 focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  disabled={loadingClientes}
                >
                  <option value="">Selecciona un cliente</option>
                  {clientes.map((cliente) => (
                    <option key={cliente.id} value={cliente.id}>
                      {cliente.nombre_display || cliente.razon_social}
                    </option>
                  ))}
                </select>
              </div>
              {clientes.length === 0 && !loadingClientes && (
                <p className="text-sm text-amber-400">
                  No tienes clientes asignados. Contacta a tu supervisor.
                </p>
              )}
            </div>

            {/* Período */}
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <label className="block text-sm font-medium text-secondary-200">
                  Mes
                </label>
                <select
                  value={formData.mes}
                  onChange={(e) => setFormData({ ...formData, mes: parseInt(e.target.value) })}
                  className="w-full px-4 py-2.5 bg-secondary-800 border border-secondary-700 rounded-lg text-secondary-100 focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                >
                  {MESES.map((mes) => (
                    <option key={mes.value} value={mes.value}>
                      {mes.label}
                    </option>
                  ))}
                </select>
              </div>

              <div className="space-y-2">
                <label className="block text-sm font-medium text-secondary-200">
                  Año
                </label>
                <select
                  value={formData.anio}
                  onChange={(e) => setFormData({ ...formData, anio: parseInt(e.target.value) })}
                  className="w-full px-4 py-2.5 bg-secondary-800 border border-secondary-700 rounded-lg text-secondary-100 focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                >
                  {years.map((year) => (
                    <option key={year} value={year}>
                      {year}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            {/* Info */}
            <div className="p-4 bg-secondary-800/50 rounded-lg border border-secondary-700">
              <h4 className="text-sm font-medium text-secondary-200 mb-2">
                ¿Qué sucederá?
              </h4>
              <ul className="text-sm text-secondary-400 space-y-1">
                <li>• Se creará un nuevo cierre en estado "Carga de Archivos"</li>
                <li>• Podrás subir los archivos del ERP y del Analista</li>
                <li>• El sistema procesará y comparará la información</li>
              </ul>
            </div>

            {/* Actions */}
            <div className="flex justify-end gap-3">
              <Button
                type="button"
                variant="secondary"
                onClick={() => navigate(-1)}
              >
                Cancelar
              </Button>
              <Button
                type="submit"
                loading={createCierre.isPending}
                disabled={!formData.cliente}
              >
                Crear Cierre
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  )
}

export default NuevoCierrePage
