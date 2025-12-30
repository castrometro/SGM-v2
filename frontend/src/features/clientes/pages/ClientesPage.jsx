/**
 * Página de listado de clientes asignados
 */
import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { Building2, Users, FileCheck2 } from 'lucide-react'
import api from '../../../api/axios'
import { Card, CardContent, CardHeader, CardTitle } from '../../../components/ui'

const ClientesPage = () => {
  const { data: clientes = [], isLoading } = useQuery({
    queryKey: ['mis-clientes'],
    queryFn: async () => {
      const { data } = await api.get('/v1/core/clientes/')
      return data.results || data
    },
  })

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-500"></div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-secondary-100">Mis Clientes</h1>
        <p className="text-secondary-400 mt-1">Clientes asignados a tu usuario</p>
      </div>

      {clientes.length === 0 ? (
        <Card>
          <CardContent className="py-12">
            <div className="flex flex-col items-center justify-center text-secondary-400">
              <Building2 className="h-12 w-12 mb-4 opacity-50" />
              <p className="text-lg font-medium">No hay clientes asignados</p>
              <p className="text-sm">Contacta a tu supervisor para que te asigne clientes</p>
            </div>
          </CardContent>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {clientes.map((cliente) => (
            <Link key={cliente.id} to={`/clientes/${cliente.id}`}>
              <Card className="hover:border-primary-500/50 transition-colors cursor-pointer">
                <CardContent className="p-6">
                  <div className="flex items-start gap-4">
                    <div className="p-3 rounded-lg bg-primary-600/20">
                      <Building2 className="h-6 w-6 text-primary-400" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <h3 className="font-semibold text-secondary-100 truncate">
                        {cliente.nombre}
                      </h3>
                      <p className="text-sm text-secondary-500 truncate">
                        {cliente.rut || 'Sin RUT'}
                      </p>
                    </div>
                  </div>
                  <div className="mt-4 flex items-center gap-4 text-sm text-secondary-400">
                    <span className="flex items-center gap-1">
                      <Users className="h-4 w-4" />
                      {cliente.total_empleados || 0} empleados
                    </span>
                    <span className="flex items-center gap-1">
                      <FileCheck2 className="h-4 w-4" />
                      {cliente.cierres_activos || 0} cierres
                    </span>
                  </div>
                </CardContent>
              </Card>
            </Link>
          ))}
        </div>
      )}
    </div>
  )
}

export default ClientesPage
