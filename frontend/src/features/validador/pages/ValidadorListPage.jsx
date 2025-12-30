/**
 * Página de listado de cierres del validador
 * Muestra los cierres del usuario actual
 */
import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { Plus, FileCheck2, Clock, CheckCircle, AlertTriangle, XCircle } from 'lucide-react'
import api from '../../../api/axios'
import { Card, CardContent, CardHeader, CardTitle } from '../../../components/ui'
import Button from '../../../components/ui/Button'
import Badge from '../../../components/ui/Badge'
import { cn } from '../../../utils/cn'

// Estados del cierre y sus propiedades visuales
const ESTADOS = {
  carga_archivos: { label: 'Carga de Archivos', color: 'info', icon: Clock },
  clasificacion: { label: 'Clasificación', color: 'info', icon: Clock },
  mapeo_novedades: { label: 'Mapeo Novedades', color: 'info', icon: Clock },
  comparacion: { label: 'Comparación', color: 'warning', icon: Clock },
  consolidacion: { label: 'Consolidación', color: 'warning', icon: Clock },
  revision_incidencias: { label: 'Revisión Incidencias', color: 'warning', icon: AlertTriangle },
  aprobacion_supervisor: { label: 'Aprobación Supervisor', color: 'primary', icon: Clock },
  generacion_reportes: { label: 'Generación Reportes', color: 'info', icon: Clock },
  completado: { label: 'Completado', color: 'success', icon: CheckCircle },
  rechazado: { label: 'Rechazado', color: 'danger', icon: XCircle },
}

const ValidadorListPage = () => {
  const navigate = useNavigate()
  const [filtroEstado, setFiltroEstado] = useState('todos')

  // Obtener cierres
  const { data: cierres = [], isLoading } = useQuery({
    queryKey: ['mis-cierres', filtroEstado],
    queryFn: async () => {
      const params = filtroEstado !== 'todos' ? { estado: filtroEstado } : {}
      const { data } = await api.get('/v1/validador/cierres/', { params })
      return data.results || data
    },
  })

  // Estadísticas rápidas
  const stats = {
    total: cierres.length,
    enProceso: cierres.filter(c => !['completado', 'rechazado'].includes(c.estado)).length,
    completados: cierres.filter(c => c.estado === 'completado').length,
    conIncidencias: cierres.filter(c => c.estado === 'revision_incidencias').length,
  }

  if (isLoading) {
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
        <div>
          <h1 className="text-2xl font-bold text-secondary-100">Mis Cierres</h1>
          <p className="text-secondary-400 mt-1">Gestiona tus procesos de validación de nómina</p>
        </div>
        <Button onClick={() => navigate('/validador/nuevo')}>
          <Plus className="h-4 w-4" />
          Nuevo Cierre
        </Button>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-secondary-800">
                <FileCheck2 className="h-5 w-5 text-secondary-400" />
              </div>
              <div>
                <p className="text-2xl font-bold text-secondary-100">{stats.total}</p>
                <p className="text-xs text-secondary-500">Total Cierres</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-blue-600/20">
                <Clock className="h-5 w-5 text-blue-400" />
              </div>
              <div>
                <p className="text-2xl font-bold text-secondary-100">{stats.enProceso}</p>
                <p className="text-xs text-secondary-500">En Proceso</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-green-600/20">
                <CheckCircle className="h-5 w-5 text-green-400" />
              </div>
              <div>
                <p className="text-2xl font-bold text-secondary-100">{stats.completados}</p>
                <p className="text-xs text-secondary-500">Completados</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-amber-600/20">
                <AlertTriangle className="h-5 w-5 text-amber-400" />
              </div>
              <div>
                <p className="text-2xl font-bold text-secondary-100">{stats.conIncidencias}</p>
                <p className="text-xs text-secondary-500">Con Incidencias</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Filtros */}
      <div className="flex gap-2">
        {['todos', 'carga_archivos', 'revision_incidencias', 'completado'].map((estado) => (
          <button
            key={estado}
            onClick={() => setFiltroEstado(estado)}
            className={cn(
              'px-3 py-1.5 rounded-lg text-sm font-medium transition-colors',
              filtroEstado === estado
                ? 'bg-primary-600 text-white'
                : 'bg-secondary-800 text-secondary-400 hover:bg-secondary-700'
            )}
          >
            {estado === 'todos' ? 'Todos' : ESTADOS[estado]?.label || estado}
          </button>
        ))}
      </div>

      {/* Lista de Cierres */}
      <Card>
        <CardHeader>
          <CardTitle>Cierres</CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          {cierres.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12 text-secondary-400">
              <FileCheck2 className="h-12 w-12 mb-4 opacity-50" />
              <p className="text-lg font-medium">No hay cierres</p>
              <p className="text-sm">Crea tu primer cierre para comenzar</p>
            </div>
          ) : (
            <div className="divide-y divide-secondary-800">
              {cierres.map((cierre) => {
                const estadoInfo = ESTADOS[cierre.estado] || { label: cierre.estado, color: 'default' }
                const Icon = estadoInfo.icon || Clock
                
                return (
                  <Link
                    key={cierre.id}
                    to={`/validador/cierre/${cierre.id}`}
                    className="flex items-center gap-4 p-4 hover:bg-secondary-800/50 transition-colors"
                  >
                    <div className={cn(
                      'p-2 rounded-lg',
                      estadoInfo.color === 'success' && 'bg-green-600/20',
                      estadoInfo.color === 'warning' && 'bg-amber-600/20',
                      estadoInfo.color === 'danger' && 'bg-red-600/20',
                      estadoInfo.color === 'info' && 'bg-blue-600/20',
                      estadoInfo.color === 'primary' && 'bg-primary-600/20',
                    )}>
                      <Icon className={cn(
                        'h-5 w-5',
                        estadoInfo.color === 'success' && 'text-green-400',
                        estadoInfo.color === 'warning' && 'text-amber-400',
                        estadoInfo.color === 'danger' && 'text-red-400',
                        estadoInfo.color === 'info' && 'text-blue-400',
                        estadoInfo.color === 'primary' && 'text-primary-400',
                      )} />
                    </div>
                    
                    <div className="flex-1 min-w-0">
                      <p className="font-medium text-secondary-100">
                        {cierre.cliente_nombre || `Cliente #${cierre.cliente}`}
                      </p>
                      <p className="text-sm text-secondary-500">
                        {cierre.mes_nombre} {cierre.anio}
                      </p>
                    </div>
                    
                    <Badge variant={estadoInfo.color}>
                      {estadoInfo.label}
                    </Badge>
                    
                    <div className="text-right text-sm text-secondary-500">
                      <p>{new Date(cierre.fecha_creacion).toLocaleDateString()}</p>
                    </div>
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

export default ValidadorListPage
