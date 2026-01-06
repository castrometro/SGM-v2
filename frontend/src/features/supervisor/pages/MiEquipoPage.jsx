/**
 * Página "Mi Equipo" para Supervisores
 * Issue #5: Vista de supervisor para gestionar clientes de su equipo
 */
import { useState, useMemo } from 'react'
import { 
  Users, 
  Building2, 
  Search, 
  RefreshCw,
  ChevronDown,
  ChevronRight,
  UserCircle,
  ArrowRightLeft
} from 'lucide-react'
import { Card, CardContent, Badge, Button } from '../../../components/ui'
import { useMiEquipo, useReasignarCliente } from '../../admin/hooks/useClientes'
import ReasignarClienteModal from '../components/ReasignarClienteModal'
import toast from 'react-hot-toast'

const MiEquipoPage = () => {
  const [search, setSearch] = useState('')
  const [expandedAnalistas, setExpandedAnalistas] = useState({})
  const [modalOpen, setModalOpen] = useState(false)
  const [clienteReasignar, setClienteReasignar] = useState(null)

  const { data, isLoading, refetch, isRefetching } = useMiEquipo()
  const reasignarMutation = useReasignarCliente()

  const equipo = data?.equipo || []
  const estadisticas = data?.estadisticas || { total_analistas: 0, total_clientes: 0 }

  // Filtrar clientes por búsqueda
  const equipoFiltrado = useMemo(() => {
    if (!search) return equipo
    
    const searchLower = search.toLowerCase()
    return equipo.map(item => ({
      ...item,
      clientes: item.clientes.filter(cliente => 
        cliente.razon_social?.toLowerCase().includes(searchLower) ||
        cliente.nombre_comercial?.toLowerCase().includes(searchLower) ||
        cliente.rut?.toLowerCase().includes(searchLower)
      )
    })).filter(item => item.clientes.length > 0 || item.analista.nombre.toLowerCase().includes(searchLower))
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

  // Abrir modal de reasignación
  const handleReasignar = (cliente, analistaActual) => {
    setClienteReasignar({ ...cliente, analista_actual: analistaActual })
    setModalOpen(true)
  }

  // Confirmar reasignación
  const handleConfirmReasignar = async (nuevoUsuarioId) => {
    try {
      await reasignarMutation.mutateAsync({
        clienteId: clienteReasignar.id,
        usuarioId: nuevoUsuarioId
      })
      toast.success('Cliente reasignado correctamente')
      setModalOpen(false)
      setClienteReasignar(null)
    } catch (error) {
      toast.error(error.response?.data?.error || 'Error al reasignar cliente')
    }
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
            <Users className="h-7 w-7 text-primary-500" />
            Mi Equipo
          </h1>
          <p className="text-secondary-400 mt-1">
            Gestiona los clientes asignados a tu equipo
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
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <Card className="bg-secondary-800/50 border-secondary-700">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <Users className="h-8 w-8 text-primary-500" />
              <div>
                <p className="text-2xl font-bold text-white">{estadisticas.total_analistas}</p>
                <p className="text-xs text-secondary-400">Analistas en equipo</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card className="bg-secondary-800/50 border-secondary-700">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <Building2 className="h-8 w-8 text-success-500" />
              <div>
                <p className="text-2xl font-bold text-white">{estadisticas.total_clientes}</p>
                <p className="text-xs text-secondary-400">Clientes totales</p>
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

      {/* Lista de analistas con clientes */}
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
                <Badge variant={item.total_clientes > 0 ? 'primary' : 'secondary'}>
                  {item.total_clientes} cliente{item.total_clientes !== 1 ? 's' : ''}
                </Badge>
              </button>

              {/* Lista de clientes del analista */}
              {expandedAnalistas[item.analista.id] && (
                <div className="border-t border-secondary-700">
                  {item.clientes.length === 0 ? (
                    <div className="p-4 text-center text-secondary-500">
                      Sin clientes asignados
                    </div>
                  ) : (
                    <div className="divide-y divide-secondary-700/50">
                      {item.clientes.map((cliente) => (
                        <div 
                          key={cliente.id}
                          className="p-4 flex items-center justify-between hover:bg-secondary-800/30"
                        >
                          <div className="flex items-center gap-3">
                            <Building2 className="h-5 w-5 text-secondary-500" />
                            <div>
                              <p className="font-medium text-secondary-200">
                                {cliente.nombre_comercial || cliente.razon_social}
                              </p>
                              <p className="text-sm text-secondary-500">
                                {cliente.rut} • {cliente.industria_nombre || 'Sin industria'}
                              </p>
                            </div>
                          </div>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleReasignar(cliente, item.analista)}
                            title="Reasignar cliente"
                          >
                            <ArrowRightLeft className="h-4 w-4" />
                            Reasignar
                          </Button>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </Card>
          ))
        )}
      </div>

      {/* Modal de reasignación */}
      <ReasignarClienteModal
        isOpen={modalOpen}
        onClose={() => {
          setModalOpen(false)
          setClienteReasignar(null)
        }}
        cliente={clienteReasignar}
        equipo={equipo}
        onConfirm={handleConfirmReasignar}
        isLoading={reasignarMutation.isPending}
      />
    </div>
  )
}

export default MiEquipoPage
