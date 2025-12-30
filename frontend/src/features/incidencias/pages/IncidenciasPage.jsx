/**
 * Página de incidencias pendientes (solo supervisor+)
 */
import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { AlertTriangle, Clock, CheckCircle, XCircle } from 'lucide-react'
import api from '../../../api/axios'
import { Card, CardContent, CardHeader, CardTitle } from '../../../components/ui'
import Badge from '../../../components/ui/Badge'
import { cn } from '../../../utils/cn'

const ESTADOS_INCIDENCIA = {
  pendiente: { label: 'Pendiente', color: 'warning', icon: Clock },
  en_revision: { label: 'En Revisión', color: 'info', icon: AlertTriangle },
  aprobada: { label: 'Aprobada', color: 'success', icon: CheckCircle },
  rechazada: { label: 'Rechazada', color: 'danger', icon: XCircle },
}

const IncidenciasPage = () => {
  const [filtro, setFiltro] = useState('pendiente')

  const { data: incidencias = [], isLoading } = useQuery({
    queryKey: ['incidencias', filtro],
    queryFn: async () => {
      const params = filtro !== 'todas' ? { estado: filtro } : {}
      const { data } = await api.get('/v1/validador/incidencias/', { params })
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
        <h1 className="text-2xl font-bold text-secondary-100">Incidencias</h1>
        <p className="text-secondary-400 mt-1">Gestiona las incidencias de validación pendientes de aprobación</p>
      </div>

      {/* Filtros */}
      <div className="flex gap-2">
        {['todas', 'pendiente', 'en_revision', 'aprobada', 'rechazada'].map((estado) => (
          <button
            key={estado}
            onClick={() => setFiltro(estado)}
            className={cn(
              'px-3 py-1.5 rounded-lg text-sm font-medium transition-colors',
              filtro === estado
                ? 'bg-primary-600 text-white'
                : 'bg-secondary-800 text-secondary-400 hover:bg-secondary-700'
            )}
          >
            {estado === 'todas' ? 'Todas' : ESTADOS_INCIDENCIA[estado]?.label || estado}
          </button>
        ))}
      </div>

      {/* Lista */}
      <Card>
        <CardHeader>
          <CardTitle>Incidencias</CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          {incidencias.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12 text-secondary-400">
              <AlertTriangle className="h-12 w-12 mb-4 opacity-50" />
              <p className="text-lg font-medium">No hay incidencias</p>
              <p className="text-sm">No se encontraron incidencias con el filtro actual</p>
            </div>
          ) : (
            <div className="divide-y divide-secondary-800">
              {incidencias.map((incidencia) => {
                const estadoInfo = ESTADOS_INCIDENCIA[incidencia.estado] || { label: incidencia.estado, color: 'default' }
                
                return (
                  <Link
                    key={incidencia.id}
                    to={`/validador/cierre/${incidencia.cierre}`}
                    className="flex items-center gap-4 p-4 hover:bg-secondary-800/50 transition-colors"
                  >
                    <div className="p-2 rounded-lg bg-amber-600/20">
                      <AlertTriangle className="h-5 w-5 text-amber-400" />
                    </div>
                    
                    <div className="flex-1 min-w-0">
                      <p className="font-medium text-secondary-100">
                        {incidencia.concepto_nombre}
                      </p>
                      <p className="text-sm text-secondary-500">
                        Variación: {incidencia.porcentaje_variacion?.toFixed(1)}%
                      </p>
                    </div>
                    
                    <Badge variant={estadoInfo.color}>
                      {estadoInfo.label}
                    </Badge>
                  </Link>
                )
              })}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}

export default IncidenciasPage
