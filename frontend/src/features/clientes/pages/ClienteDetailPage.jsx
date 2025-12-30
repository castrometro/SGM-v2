/**
 * Página de detalle de cliente
 */
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { ArrowLeft, Building2 } from 'lucide-react'
import api from '../../../api/axios'
import { Card, CardContent, CardHeader, CardTitle } from '../../../components/ui'

const ClienteDetailPage = () => {
  const { id } = useParams()
  const navigate = useNavigate()

  const { data: cliente, isLoading } = useQuery({
    queryKey: ['cliente', id],
    queryFn: async () => {
      const { data } = await api.get(`/v1/core/clientes/${id}/`)
      return data
    },
  })

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-500"></div>
      </div>
    )
  }

  if (!cliente) {
    return <div>Cliente no encontrado</div>
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <button 
          onClick={() => navigate(-1)}
          className="p-2 rounded-lg hover:bg-secondary-800 transition-colors"
        >
          <ArrowLeft className="h-5 w-5 text-secondary-400" />
        </button>
        <div className="flex items-center gap-4">
          <div className="p-3 rounded-lg bg-primary-600/20">
            <Building2 className="h-6 w-6 text-primary-400" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-secondary-100">{cliente.nombre}</h1>
            <p className="text-secondary-400">{cliente.rut}</p>
          </div>
        </div>
      </div>

      {/* Info */}
      <Card>
        <CardHeader>
          <CardTitle>Información del Cliente</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <p className="text-sm text-secondary-500">Industria</p>
              <p className="text-secondary-100">{cliente.industria_nombre || '-'}</p>
            </div>
            <div>
              <p className="text-sm text-secondary-500">Estado</p>
              <p className="text-secondary-100">{cliente.activo ? 'Activo' : 'Inactivo'}</p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

export default ClienteDetailPage
