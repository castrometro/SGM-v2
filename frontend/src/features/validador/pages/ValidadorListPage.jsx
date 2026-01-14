/**
 * Página de listado de cierres del validador
 * Muestra los cierres del usuario actual
 */
import { useState, useMemo } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { Plus, FileCheck2, Clock, CheckCircle, AlertTriangle, XCircle, RefreshCw, Filter, Calendar, X } from 'lucide-react'
import api from '../../../api/axios'
import { Card, CardContent, CardHeader, CardTitle, ConfirmDialog, Select } from '../../../components/ui'
import Button from '../../../components/ui/Button'
import Badge from '../../../components/ui/Badge'
import { cn } from '../../../utils/cn'

// Estados del cierre y sus propiedades visuales
const ESTADOS = {
  carga_archivos: { label: 'Carga Libro ERP', color: 'info', icon: Clock },
  clasificacion_conceptos: { label: 'Clasificación', color: 'info', icon: Clock },
  carga_novedades: { label: 'Carga Novedades', color: 'info', icon: Clock },
  mapeo_items: { label: 'Mapeo Items', color: 'info', icon: Clock },
  comparacion: { label: 'Comparación', color: 'warning', icon: Clock },
  con_discrepancias: { label: 'Con Discrepancias', color: 'danger', icon: AlertTriangle },
  consolidado: { label: 'Consolidado', color: 'success', icon: CheckCircle },
  deteccion_incidencias: { label: 'Detectando Incidencias', color: 'warning', icon: Clock },
  revision_incidencias: { label: 'Revisión Incidencias', color: 'warning', icon: AlertTriangle },
  finalizado: { label: 'Finalizado', color: 'success', icon: CheckCircle },
  cancelado: { label: 'Cancelado', color: 'secondary', icon: XCircle },
  error: { label: 'Error', color: 'danger', icon: XCircle },
}

// Lista de meses para filtros
const MESES = [
  { value: '', label: 'Todos los meses' },
  { value: '1', label: 'Enero' },
  { value: '2', label: 'Febrero' },
  { value: '3', label: 'Marzo' },
  { value: '4', label: 'Abril' },
  { value: '5', label: 'Mayo' },
  { value: '6', label: 'Junio' },
  { value: '7', label: 'Julio' },
  { value: '8', label: 'Agosto' },
  { value: '9', label: 'Septiembre' },
  { value: '10', label: 'Octubre' },
  { value: '11', label: 'Noviembre' },
  { value: '12', label: 'Diciembre' },
]

// Generar años para el filtro (últimos 5 años)
const currentYear = new Date().getFullYear()
const ANIOS = [
  { value: '', label: 'Todos los años' },
  ...Array.from({ length: 5 }, (_, i) => ({
    value: String(currentYear - i),
    label: String(currentYear - i),
  })),
]

const ValidadorListPage = () => {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [filtroEstado, setFiltroEstado] = useState('todos')
  const [filtroMes, setFiltroMes] = useState('')
  const [filtroAnio, setFiltroAnio] = useState('')
  const [mostrarFiltrosAvanzados, setMostrarFiltrosAvanzados] = useState(false)
  const [showConfirmModal, setShowConfirmModal] = useState(false)

  // Obtener cierres
  const { data: cierres = [], isLoading, isFetching, refetch } = useQuery({
    queryKey: ['mis-cierres'],
    queryFn: async () => {
      const { data } = await api.get('/v1/validador/cierres/')
      return data.results || data
    },
  })

  // Filtrar cierres en el cliente para mejor UX
  const cierresFiltrados = useMemo(() => {
    return cierres.filter((cierre) => {
      // Filtro por estado
      if (filtroEstado !== 'todos' && cierre.estado !== filtroEstado) {
        return false
      }
      // Filtro por mes
      if (filtroMes && String(cierre.mes) !== filtroMes) {
        return false
      }
      // Filtro por año
      if (filtroAnio && String(cierre.anio) !== filtroAnio) {
        return false
      }
      return true
    })
  }, [cierres, filtroEstado, filtroMes, filtroAnio])

  // Estadísticas rápidas (sobre todos los cierres, no filtrados)
  const stats = {
    total: cierres.length,
    enProceso: cierres.filter(c => !['completado', 'rechazado'].includes(c.estado)).length,
    completados: cierres.filter(c => c.estado === 'completado').length,
    conIncidencias: cierres.filter(c => c.estado === 'revision_incidencias').length,
  }

  // Verificar si hay cierres en progreso
  const cierresEnProgreso = cierres.filter(c => !['completado', 'rechazado'].includes(c.estado))

  // Manejar clic en "Nuevo Cierre"
  const handleNuevoCierre = () => {
    if (cierresEnProgreso.length > 0) {
      setShowConfirmModal(true)
    } else {
      navigate('/validador/nuevo')
    }
  }

  // Confirmar creación de nuevo cierre
  const handleConfirmNuevoCierre = () => {
    setShowConfirmModal(false)
    navigate('/validador/nuevo')
  }

  // Refrescar lista
  const handleRefresh = () => {
    refetch()
  }

  // Limpiar filtros
  const handleLimpiarFiltros = () => {
    setFiltroEstado('todos')
    setFiltroMes('')
    setFiltroAnio('')
  }

  // Verificar si hay filtros activos
  const hayFiltrosActivos = filtroEstado !== 'todos' || filtroMes !== '' || filtroAnio !== ''

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
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            onClick={handleRefresh}
            disabled={isFetching}
            title="Refrescar lista"
          >
            <RefreshCw className={cn("h-4 w-4", isFetching && "animate-spin")} />
            {isFetching ? 'Actualizando...' : 'Refrescar'}
          </Button>
          <Button onClick={handleNuevoCierre}>
            <Plus className="h-4 w-4" />
            Nuevo Cierre
          </Button>
        </div>
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
      <div className="space-y-3">
        {/* Filtros rápidos por estado */}
        <div className="flex items-center gap-2 flex-wrap">
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
          
          <div className="ml-auto flex items-center gap-2">
            {hayFiltrosActivos && (
              <Button
                variant="ghost"
                size="sm"
                onClick={handleLimpiarFiltros}
                className="text-secondary-400 hover:text-secondary-100"
              >
                <X className="h-4 w-4 mr-1" />
                Limpiar filtros
              </Button>
            )}
            <Button
              variant="outline"
              size="sm"
              onClick={() => setMostrarFiltrosAvanzados(!mostrarFiltrosAvanzados)}
            >
              <Filter className="h-4 w-4 mr-1" />
              {mostrarFiltrosAvanzados ? 'Ocultar filtros' : 'Más filtros'}
            </Button>
          </div>
        </div>

        {/* Filtros avanzados */}
        {mostrarFiltrosAvanzados && (
          <Card>
            <CardContent className="p-4">
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                {/* Filtro por estado completo */}
                <div>
                  <label className="block text-sm font-medium text-secondary-300 mb-1">
                    Estado
                  </label>
                  <Select
                    value={filtroEstado}
                    onChange={(e) => setFiltroEstado(e.target.value)}
                  >
                    <option value="todos">Todos los estados</option>
                    {Object.entries(ESTADOS).map(([key, { label }]) => (
                      <option key={key} value={key}>{label}</option>
                    ))}
                  </Select>
                </div>

                {/* Filtro por mes */}
                <div>
                  <label className="block text-sm font-medium text-secondary-300 mb-1">
                    <Calendar className="h-4 w-4 inline mr-1" />
                    Mes
                  </label>
                  <Select
                    value={filtroMes}
                    onChange={(e) => setFiltroMes(e.target.value)}
                  >
                    {MESES.map(({ value, label }) => (
                      <option key={value} value={value}>{label}</option>
                    ))}
                  </Select>
                </div>

                {/* Filtro por año */}
                <div>
                  <label className="block text-sm font-medium text-secondary-300 mb-1">
                    Año
                  </label>
                  <Select
                    value={filtroAnio}
                    onChange={(e) => setFiltroAnio(e.target.value)}
                  >
                    {ANIOS.map(({ value, label }) => (
                      <option key={value} value={value}>{label}</option>
                    ))}
                  </Select>
                </div>

                {/* Resumen de filtros */}
                <div className="flex items-end">
                  <p className="text-sm text-secondary-400">
                    Mostrando <span className="font-semibold text-secondary-100">{cierresFiltrados.length}</span> de {cierres.length} cierres
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        )}
      </div>

      {/* Lista de Cierres */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle>Cierres</CardTitle>
          {hayFiltrosActivos && (
            <Badge variant="info">
              {cierresFiltrados.length} resultado{cierresFiltrados.length !== 1 ? 's' : ''}
            </Badge>
          )}
        </CardHeader>
        <CardContent className="p-0">
          {cierresFiltrados.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12 text-secondary-400">
              <FileCheck2 className="h-12 w-12 mb-4 opacity-50" />
              {hayFiltrosActivos ? (
                <>
                  <p className="text-lg font-medium">No hay resultados</p>
                  <p className="text-sm">No se encontraron cierres con los filtros aplicados</p>
                  <Button
                    variant="outline"
                    size="sm"
                    className="mt-4"
                    onClick={handleLimpiarFiltros}
                  >
                    Limpiar filtros
                  </Button>
                </>
              ) : (
                <>
                  <p className="text-lg font-medium">No hay cierres</p>
                  <p className="text-sm">Crea tu primer cierre para comenzar</p>
                </>
              )}
            </div>
          ) : (
            <div className="divide-y divide-secondary-800">
              {cierresFiltrados.map((cierre) => {
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

      {/* Modal de confirmación para nuevo cierre */}
      <ConfirmDialog
        isOpen={showConfirmModal}
        onClose={() => setShowConfirmModal(false)}
        onConfirm={handleConfirmNuevoCierre}
        title="¿Crear nuevo cierre?"
        description={
          cierresEnProgreso.length === 1
            ? `Tienes 1 cierre en progreso. ¿Deseas crear uno nuevo de todas formas?`
            : `Tienes ${cierresEnProgreso.length} cierres en progreso. ¿Deseas crear uno nuevo de todas formas?`
        }
        confirmText="Sí, crear nuevo"
        cancelText="Cancelar"
        variant="warning"
      />
    </div>
  )
}

export default ValidadorListPage
