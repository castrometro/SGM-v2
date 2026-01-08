/**
 * Hub de Dashboards de Nómina
 * Permite seleccionar período y acceder a Libro de Remuneraciones o Movimientos
 */
import { useState } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { 
  ArrowLeft, 
  BookOpen, 
  Users, 
  Calendar,
  ChevronRight,
  AlertCircle
} from 'lucide-react'
import api from '@/api/axios'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui'
import { formatPeriodo } from '../utils'

// Mock de cierres finalizados (TODO: obtener del backend)
const MOCK_CIERRES_FINALIZADOS = [
  { id: 1, periodo: '2025-12', estado: 'finalizado' },
  { id: 2, periodo: '2025-11', estado: 'finalizado' },
  { id: 3, periodo: '2025-10', estado: 'finalizado' },
]

const DashboardHubPage = () => {
  const { clienteId } = useParams()
  const navigate = useNavigate()
  const [selectedPeriodo, setSelectedPeriodo] = useState('')

  // Obtener info del cliente
  const { data: cliente, isLoading: loadingCliente } = useQuery({
    queryKey: ['cliente', clienteId],
    queryFn: async () => {
      const { data } = await api.get(`/v1/core/clientes/${clienteId}/`)
      return data
    },
  })

  // TODO: Obtener cierres finalizados del cliente
  const cierresFinalizados = MOCK_CIERRES_FINALIZADOS

  const dashboardOptions = [
    {
      title: 'Libro de Remuneraciones',
      description: 'Análisis de haberes, descuentos y aportes patronales',
      icon: BookOpen,
      href: `/validador/cliente/${clienteId}/dashboard/libro`,
      color: 'border-green-500/30 hover:border-green-500/60',
      iconColor: 'text-green-400',
      bgColor: 'bg-green-500/10',
    },
    {
      title: 'Movimientos de Personal',
      description: 'Ingresos, finiquitos, ausencias y ausentismo',
      icon: Users,
      href: `/validador/cliente/${clienteId}/dashboard/movimientos`,
      color: 'border-blue-500/30 hover:border-blue-500/60',
      iconColor: 'text-blue-400',
      bgColor: 'bg-blue-500/10',
    },
  ]

  if (loadingCliente) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-500"></div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <button 
            onClick={() => navigate(`/clientes/${clienteId}`)}
            className="p-2 rounded-lg hover:bg-secondary-800 transition-colors"
          >
            <ArrowLeft className="h-5 w-5 text-secondary-400" />
          </button>
          <div>
            <h1 className="text-2xl font-bold text-secondary-100">Dashboard de Nómina</h1>
            <p className="text-secondary-400 mt-1">
              {cliente?.nombre_display || cliente?.razon_social || 'Cliente'}
            </p>
          </div>
        </div>
      </div>

      {/* Selector de Período */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Calendar className="h-5 w-5 text-primary-400" />
            Seleccionar Período
          </CardTitle>
        </CardHeader>
        <CardContent>
          {cierresFinalizados.length > 0 ? (
            <div className="flex flex-wrap gap-3">
              {cierresFinalizados.map((cierre) => (
                <button
                  key={cierre.id}
                  onClick={() => setSelectedPeriodo(cierre.periodo)}
                  className={`px-4 py-2 rounded-lg border transition-all ${
                    selectedPeriodo === cierre.periodo
                      ? 'border-primary-500 bg-primary-500/20 text-primary-300'
                      : 'border-secondary-700 hover:border-secondary-600 text-secondary-300'
                  }`}
                >
                  {formatPeriodo(cierre.periodo)}
                </button>
              ))}
            </div>
          ) : (
            <div className="flex items-center gap-3 text-secondary-400">
              <AlertCircle className="h-5 w-5" />
              <span>No hay cierres finalizados disponibles para este cliente.</span>
            </div>
          )}
          
          {selectedPeriodo && (
            <div className="mt-4 p-3 bg-primary-500/10 border border-primary-500/30 rounded-lg">
              <p className="text-sm text-primary-300">
                Período seleccionado: <strong>{formatPeriodo(selectedPeriodo)}</strong>
                {' '}— Se comparará automáticamente con el mes anterior si está disponible.
              </p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Opciones de Dashboard */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {dashboardOptions.map((option) => (
          <Link
            key={option.title}
            to={selectedPeriodo ? `${option.href}?periodo=${selectedPeriodo}` : '#'}
            onClick={(e) => {
              if (!selectedPeriodo) {
                e.preventDefault()
              }
            }}
            className={`group block ${!selectedPeriodo ? 'opacity-50 cursor-not-allowed' : ''}`}
          >
            <Card className={`h-full border-2 transition-all ${option.color} ${!selectedPeriodo ? '' : 'hover:shadow-lg'}`}>
              <CardContent className="p-6">
                <div className="flex items-start gap-4">
                  <div className={`p-3 rounded-lg ${option.bgColor}`}>
                    <option.icon className={`h-8 w-8 ${option.iconColor}`} />
                  </div>
                  <div className="flex-1">
                    <h3 className="text-lg font-semibold text-secondary-100 group-hover:text-primary-400 transition-colors">
                      {option.title}
                    </h3>
                    <p className="text-sm text-secondary-400 mt-1">
                      {option.description}
                    </p>
                  </div>
                  <ChevronRight className={`h-5 w-5 text-secondary-600 group-hover:text-secondary-400 transition-colors ${!selectedPeriodo ? 'opacity-0' : ''}`} />
                </div>
              </CardContent>
            </Card>
          </Link>
        ))}
      </div>

      {/* Nota */}
      {!selectedPeriodo && (
        <div className="p-4 bg-amber-500/10 border border-amber-500/30 rounded-lg">
          <p className="text-sm text-amber-400">
            👆 Selecciona un período arriba para acceder a los dashboards.
          </p>
        </div>
      )}

      {/* Mock data notice */}
      <div className="p-3 bg-secondary-800/50 border border-secondary-700 rounded-lg">
        <p className="text-xs text-secondary-500">
          ⚠️ Página en desarrollo. Los períodos mostrados son de ejemplo.
        </p>
      </div>
    </div>
  )
}

export default DashboardHubPage
