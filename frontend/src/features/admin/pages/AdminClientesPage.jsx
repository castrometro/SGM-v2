/**
 * Página de administración de clientes (solo gerente)
 * CRUD completo de clientes del sistema
 */
import { useState, useMemo } from 'react'
import { Building2, Plus, Search, Filter, Download, RefreshCw } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle, Button, Select, Badge } from '../../../components/ui'
import { ClientesTable, ClienteModal, AsignacionClienteModal } from '../components'
import { useClientes, useIndustrias } from '../hooks/useClientes'
import { useClientesConAsignaciones } from '../hooks/useAsignaciones'
import { toast } from 'react-hot-toast'

const AdminClientesPage = () => {
  // Estado de filtros
  const [search, setSearch] = useState('')
  const [filterActivo, setFilterActivo] = useState('')
  const [filterIndustria, setFilterIndustria] = useState('')
  
  // Estado del modal de edición
  const [modalOpen, setModalOpen] = useState(false)
  const [selectedCliente, setSelectedCliente] = useState(null)
  
  // Estado del modal de asignaciones
  const [asignacionModalOpen, setAsignacionModalOpen] = useState(false)
  const [clienteAsignacion, setClienteAsignacion] = useState(null)

  // Queries - usar clientesConAsignaciones para mostrar supervisor y total_analistas
  const { 
    data: clientes = [], 
    isLoading, 
    isRefetching,
    refetch 
  } = useClientesConAsignaciones({ 
    search, 
    activo: filterActivo, 
    industria: filterIndustria 
  })
  
  const { data: industrias = [] } = useIndustrias()

  // Opciones para filtros
  const industriaOptions = useMemo(() => 
    industrias.map((ind) => ({ value: ind.id.toString(), label: ind.nombre })),
    [industrias]
  )

  const estadoOptions = [
    { value: 'true', label: 'Activos' },
    { value: 'false', label: 'Inactivos' },
  ]

  // Estadísticas
  const stats = useMemo(() => ({
    total: clientes.length,
    activos: clientes.filter(c => c.activo).length,
    inactivos: clientes.filter(c => !c.activo).length,
  }), [clientes])

  // Handlers
  const handleCreate = () => {
    setSelectedCliente(null)
    setModalOpen(true)
  }

  const handleEdit = (cliente) => {
    setSelectedCliente(cliente)
    setModalOpen(true)
  }

  const handleCloseModal = () => {
    setModalOpen(false)
    setSelectedCliente(null)
  }

  const handleManageAsignaciones = (cliente) => {
    setClienteAsignacion(cliente)
    setAsignacionModalOpen(true)
  }

  const handleCloseAsignacionModal = () => {
    setAsignacionModalOpen(false)
    setClienteAsignacion(null)
  }

  const handleClearFilters = () => {
    setSearch('')
    setFilterActivo('')
    setFilterIndustria('')
  }

  const handleExport = () => {
    // TODO: Implementar exportación a Excel
    toast.success('Funcionalidad de exportación próximamente')
  }

  const hasFilters = search || filterActivo || filterIndustria

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-secondary-100">Clientes</h1>
          <p className="text-secondary-400 mt-1">
            Administra todos los clientes del sistema
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" onClick={handleExport}>
            <Download className="h-4 w-4" />
            Exportar
          </Button>
          <Button onClick={handleCreate}>
            <Plus className="h-4 w-4" />
            Nuevo Cliente
          </Button>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-secondary-400">Total Clientes</p>
                <p className="text-2xl font-bold text-secondary-100">{stats.total}</p>
              </div>
              <div className="p-3 rounded-lg bg-primary-600/20">
                <Building2 className="h-6 w-6 text-primary-400" />
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-secondary-400">Activos</p>
                <p className="text-2xl font-bold text-green-400">{stats.activos}</p>
              </div>
              <Badge variant="success">
                {stats.total > 0 ? Math.round((stats.activos / stats.total) * 100) : 0}%
              </Badge>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-secondary-400">Inactivos</p>
                <p className="text-2xl font-bold text-secondary-500">{stats.inactivos}</p>
              </div>
              <Badge variant="secondary">
                {stats.total > 0 ? Math.round((stats.inactivos / stats.total) * 100) : 0}%
              </Badge>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Filtros */}
      <Card>
        <CardContent className="p-4">
          <div className="flex flex-col lg:flex-row gap-4">
            {/* Búsqueda */}
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-secondary-500" />
              <input
                type="text"
                placeholder="Buscar por nombre, RUT o razón social..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="w-full pl-10 pr-4 py-2.5 bg-secondary-800 border border-secondary-700 rounded-lg text-secondary-100 placeholder-secondary-500 focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              />
            </div>

            {/* Filtro Estado */}
            <div className="w-full lg:w-48">
              <Select
                options={estadoOptions}
                placeholder="Estado"
                value={filterActivo}
                onChange={(e) => setFilterActivo(e.target.value)}
              />
            </div>

            {/* Filtro Industria */}
            <div className="w-full lg:w-48">
              <Select
                options={industriaOptions}
                placeholder="Industria"
                value={filterIndustria}
                onChange={(e) => setFilterIndustria(e.target.value)}
              />
            </div>

            {/* Acciones de filtro */}
            <div className="flex items-center gap-2">
              {hasFilters && (
                <Button 
                  variant="ghost" 
                  size="sm"
                  onClick={handleClearFilters}
                >
                  <Filter className="h-4 w-4" />
                  Limpiar
                </Button>
              )}
              <Button 
                variant="ghost" 
                size="sm"
                onClick={() => refetch()}
                disabled={isRefetching}
              >
                <RefreshCw className={`h-4 w-4 ${isRefetching ? 'animate-spin' : ''}`} />
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Tabla de Clientes */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Building2 className="h-5 w-5 text-primary-400" />
            Lista de Clientes
            {hasFilters && (
              <Badge variant="secondary" className="ml-2">
                Filtrado: {clientes.length} resultados
              </Badge>
            )}
          </CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          {isLoading ? (
            <div className="flex items-center justify-center py-12">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-500"></div>
            </div>
          ) : (
            <ClientesTable 
              clientes={clientes} 
              onEdit={handleEdit}
              onManageAsignaciones={handleManageAsignaciones}
            />
          )}
        </CardContent>
      </Card>

      {/* Modal Crear/Editar */}
      <ClienteModal
        isOpen={modalOpen}
        onClose={handleCloseModal}
        cliente={selectedCliente}
      />

      {/* Modal de Asignaciones */}
      <AsignacionClienteModal
        open={asignacionModalOpen}
        onClose={handleCloseAsignacionModal}
        cliente={clienteAsignacion}
      />
    </div>
  )
}

export default AdminClientesPage
