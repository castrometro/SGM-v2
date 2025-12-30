import { Building2, FileCheck2, AlertCircle, CheckCircle } from 'lucide-react'
import { useAuth } from '../../../contexts/AuthContext'

const DashboardPage = () => {
  const { user } = useAuth()

  // Datos de ejemplo - estos vendrían de la API
  const stats = [
    {
      name: 'Clientes Asignados',
      value: '12',
      icon: Building2,
      color: 'bg-blue-500',
    },
    {
      name: 'Cierres Pendientes',
      value: '5',
      icon: FileCheck2,
      color: 'bg-yellow-500',
    },
    {
      name: 'Incidencias Abiertas',
      value: '3',
      icon: AlertCircle,
      color: 'bg-red-500',
    },
    {
      name: 'Cierres Completados',
      value: '28',
      icon: CheckCircle,
      color: 'bg-green-500',
    },
  ]

  return (
    <div className="space-y-6">
      {/* Welcome header */}
      <div>
        <h1 className="text-2xl font-bold text-white">
          ¡Hola, {user?.nombre}!
        </h1>
        <p className="text-secondary-400">
          Bienvenido al Sistema de Gestión de Nómina
        </p>
      </div>

      {/* Stats grid */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {stats.map((stat) => (
          <div key={stat.name} className="card">
            <div className="flex items-center gap-4">
              <div className={`rounded-lg p-3 ${stat.color}`}>
                <stat.icon className="h-6 w-6 text-white" />
              </div>
              <div>
                <p className="text-sm text-secondary-400">{stat.name}</p>
                <p className="text-2xl font-bold text-white">{stat.value}</p>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Quick actions */}
      <div className="grid gap-6 lg:grid-cols-2">
        {/* Cierres recientes */}
        <div className="card">
          <h3 className="mb-4 text-lg font-semibold text-white">
            Cierres Recientes
          </h3>
          <div className="space-y-3">
            <p className="text-secondary-400">
              No hay cierres recientes para mostrar.
            </p>
          </div>
        </div>

        {/* Actividad reciente */}
        <div className="card">
          <h3 className="mb-4 text-lg font-semibold text-white">
            Actividad Reciente
          </h3>
          <div className="space-y-3">
            <p className="text-secondary-400">
              No hay actividad reciente para mostrar.
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}

export default DashboardPage
