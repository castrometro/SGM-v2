/**
 * Página "Cierres del Equipo" para Supervisores
 * Muestra el cierre más reciente de cada cliente de los analistas supervisados
 */
import { useState, useMemo } from 'react'
import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { 
  Users, 
  FileCheck2, 
  Search, 
  RefreshCw,
  ChevronDown,
  ChevronRight,
  UserCircle,
  Clock,
  CheckCircle,
  AlertTriangle,
  XCircle,
  Building2,
  Calendar,
  ExternalLink
} from 'lucide-react'
import { Card, CardContent, Badge, Button } from '../../../components/ui'
import api from '../../../api/axios'

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
  finalizado: { label: 'Finalizado', color: 'success', icon: CheckCircle },
  rechazado: { label: 'Rechazado', color: 'danger', icon: XCircle },
}

const getEstadoConfig = (estado) => {
  return ESTADOS[estado] || { label: estado, color: 'secondary', icon: Clock }
}

const CierresEquipoPage = () => {
  const [search, setSearch] = useState('')
  const [expandedAnalistas, setExpandedAnalistas] = useState({})

  // Obtener cierres del equipo
  const { data, isLoading, refetch, isRefetching } = useQuery({
    queryKey: ['cierres-equipo'],
    queryFn: async () => {
      const { data } = await api.get('/v1/validador/cierres/cierres_equipo/')
      return data
    },
  })

  const equipo = data?.equipo || []
  const estadisticas = data?.estadisticas || { 
    total_analistas: 0, 
    total_cierres: 0,
    cierres_en_proceso: 0 
  }

  // Filtrar por búsqueda
  const equipoFiltrado = useMemo(() => {
    if (!search) return equipo
    
    const searchLower = search.toLowerCase()
    return equipo.map(item => ({
      ...item,
      cierres: item.cierres.filter(cierre => 
        cierre.cliente.nombre?.toLowerCase().includes(searchLower) ||
        cierre.cliente.rut?.toLowerCase().includes(searchLower)
      )
    })).filter(item => 
      item.cierres.length > 0 || 
      item.analista.nombre.toLowerCase().includes(searchLower)
    )
  }, [equipo, search])

  // Toggle expandir analista
  const toggleAnalista = (analistaId) => {
    setExpandedAnalistas(prev => ({
      ...prev,
      [analistaId]: !prev[analistaId]
    }))
  }

  // Expandir todos
  const expandAll = () => {
    const allExpanded = {}
    equipo.forEach(item => {
      allExpanded[item.analista.id] = true
    })
    setExpandedAnalistas(allExpanded)
  }

  // Colapsar todos
  const collapseAll = () => {
    setExpandedAnalistas({})
  }

  // Formatear periodo
  const formatPeriodo = (mes, anio) => {
    const meses = ['', 'Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']
    return `${meses[mes]} ${anio}`
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary-500"></div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-secondary-100 flex items-center gap-3">
            <FileCheck2 className="h-7 w-7 text-primary-500" />
            Cierres del Equipo
          </h1>
          <p className="text-secondary-400 mt-1">
            Cierre más reciente de cada cliente de tus analistas
          </p>
        </div>
        <Button 
          variant="outline" 
          onClick={() => refetch()}
          disabled={isRefetching}
        >
          <RefreshCw className={`h-4 w-4 ${isRefetching ? 'animate-spin' : ''}`} />
          Actualizar
        </Button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <Card className="bg-secondary-800/50 border-secondary-700">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <Users className="h-8 w-8 text-primary-500" />
              <div>
                <p className="text-2xl font-bold text-white">{estadisticas.total_analistas}</p>
                <p className="text-xs text-secondary-400">Analistas</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card className="bg-secondary-800/50 border-secondary-700">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <FileCheck2 className="h-8 w-8 text-success-500" />
              <div>
                <p className="text-2xl font-bold text-white">{estadisticas.total_cierres}</p>
                <p className="text-xs text-secondary-400">Cierres totales</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card className="bg-secondary-800/50 border-secondary-700">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <Clock className="h-8 w-8 text-warning-500" />
              <div>
                <p className="text-2xl font-bold text-white">{estadisticas.cierres_en_proceso}</p>
                <p className="text-xs text-secondary-400">En proceso</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Filtros */}
      <Card>
        <CardContent className="p-4">
          <div className="flex flex-col sm:flex-row gap-4">
            {/* Búsqueda */}
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-secondary-500" />
              <input
                type="text"
                placeholder="Buscar cliente o analista..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="w-full pl-10 pr-4 py-2.5 bg-secondary-800 border border-secondary-700 rounded-lg text-secondary-100 placeholder-secondary-500 focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              />
            </div>
            
            {/* Acciones */}
            <div className="flex gap-2">
              <Button variant="ghost" size="sm" onClick={expandAll}>
                Expandir todo
              </Button>
              <Button variant="ghost" size="sm" onClick={collapseAll}>
                Colapsar todo
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Lista de analistas con cierres */}
      <div className="space-y-4">
        {equipoFiltrado.length === 0 ? (
          <Card>
            <CardContent className="p-8 text-center">
              <Users className="h-12 w-12 text-secondary-600 mx-auto mb-4" />
              <p className="text-secondary-400">No hay analistas en tu equipo</p>
            </CardContent>
          </Card>
        ) : (
          equipoFiltrado.map((item) => (
            <Card key={item.analista.id} className="overflow-hidden">
              {/* Header del analista */}
              <button
                onClick={() => toggleAnalista(item.analista.id)}
                className="w-full p-4 flex items-center justify-between bg-secondary-800/50 hover:bg-secondary-700/50 transition-colors"
              >
                <div className="flex items-center gap-3">
                  {expandedAnalistas[item.analista.id] ? (
                    <ChevronDown className="h-5 w-5 text-secondary-400" />
                  ) : (
                    <ChevronRight className="h-5 w-5 text-secondary-400" />
                  )}
                  <UserCircle className="h-8 w-8 text-primary-400" />
                  <div className="text-left">
                    <p className="font-medium text-secondary-100">{item.analista.nombre}</p>
                    <p className="text-sm text-secondary-400">{item.analista.email}</p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <Badge variant="secondary">
                    {item.total_clientes} cliente{item.total_clientes !== 1 ? 's' : ''}
                  </Badge>
                  <Badge variant={item.total_cierres > 0 ? 'primary' : 'secondary'}>
                    {item.total_cierres} cierre{item.total_cierres !== 1 ? 's' : ''}
                  </Badge>
                </div>
              </button>

              {/* Lista de cierres del analista */}
              {expandedAnalistas[item.analista.id] && (
                <div className="border-t border-secondary-700">
                  {item.cierres.length === 0 ? (
                    <div className="p-4 text-center text-secondary-500">
                      Sin cierres registrados
                    </div>
                  ) : (
                    <div className="divide-y divide-secondary-700/50">
                      {item.cierres.map((cierre) => {
                        const estadoConfig = getEstadoConfig(cierre.estado)
                        const EstadoIcon = estadoConfig.icon
                        
                        return (
                          <div 
                            key={cierre.id}
                            className="p-4 flex items-center justify-between hover:bg-secondary-800/30"
                          >
                            <div className="flex items-center gap-4">
                              <div className="flex items-center gap-2">
                                <Building2 className="h-5 w-5 text-secondary-500" />
                                <div>
                                  <p className="font-medium text-secondary-200">
                                    {cierre.cliente.nombre}
                                  </p>
                                  <p className="text-sm text-secondary-500">
                                    {cierre.cliente.rut}
                                  </p>
                                </div>
                              </div>
                              
                              <div className="flex items-center gap-2 text-secondary-400">
                                <Calendar className="h-4 w-4" />
                                <span className="text-sm">{formatPeriodo(cierre.mes, cierre.anio)}</span>
                              </div>
                              
                              <Badge variant={estadoConfig.color}>
                                <EstadoIcon className="h-3 w-3 mr-1" />
                                {estadoConfig.label}
                              </Badge>
                            </div>
                            
                            <Link
                              to={`/validador/cierre/${cierre.id}`}
                              className="flex items-center gap-1 text-sm text-primary-400 hover:text-primary-300"
                            >
                              Ver detalle
                              <ExternalLink className="h-4 w-4" />
                            </Link>
                          </div>
                        )
                      })}
                    </div>
                  )}
                </div>
              )}
            </Card>
          ))
        )}
      </div>
    </div>
  )
}

export default CierresEquipoPage
