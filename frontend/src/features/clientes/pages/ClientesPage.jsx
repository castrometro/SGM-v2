/**
 * Página de listado de clientes asignados
 * Issue #9: Formato tabla con filtros (mismo estilo que Admin > Clientes)
 */
import { useState, useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Building2, Search, RefreshCw } from 'lucide-react'
import api from '../../../api/axios'
import { Card, CardContent, CardHeader, CardTitle, Button, Select } from '../../../components/ui'
import MisClientesTable from '../components/MisClientesTable'

const ClientesPage = () => {
  // Estado de filtros
  const [search, setSearch] = useState('')
  const [filterActivo, setFilterActivo] = useState('')

  const { 
    data: clientes = [], 
    isLoading, 
    isFetching,
    refetch,
    isError,
    error 
  } = useQuery({
    queryKey: ['mis-clientes'],
    queryFn: async () => {
      const { data } = await api.get('/v1/core/clientes/')
      return data.results || data
    },
    refetchOnMount: 'always',
    staleTime: 0,
  })

  // Filtrar clientes localmente
  const clientesFiltrados = useMemo(() => {
    return clientes.filter((cliente) => {
      // Filtro de búsqueda
      const searchLower = search.toLowerCase()
      const matchSearch = !search || 
        (cliente.nombre || '').toLowerCase().includes(searchLower) ||
        (cliente.razon_social || '').toLowerCase().includes(searchLower) ||
        (cliente.nombre_comercial || '').toLowerCase().includes(searchLower) ||
        (cliente.rut || '').toLowerCase().includes(searchLower)

      // Filtro de estado
      const matchActivo = filterActivo === '' || 
        cliente.activo === (filterActivo === 'true')

      return matchSearch && matchActivo
    })
  }, [clientes, search, filterActivo])

  // Opciones de filtro
  const estadoOptions = [
    { value: 'true', label: 'Activos' },
    { value: 'false', label: 'Inactivos' },
  ]

  const hasFilters = search || filterActivo

  const handleClearFilters = () => {
    setSearch('')
    setFilterActivo('')
  }

  // Mostrar loading en la carga inicial
  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-500"></div>
      </div>
    )
  }

  // Mostrar error si falla la carga
  if (isError) {
    return (
      <div className="flex flex-col items-center justify-center h-64 text-secondary-400">
        <p className="text-red-400 mb-4">Error al cargar clientes: {error?.message}</p>
        <Button onClick={() => refetch()} variant="outline" size="sm">
          <RefreshCw className="h-4 w-4 mr-2" />
          Reintentar
        </Button>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-secondary-100">Mis Clientes</h1>
          <p className="text-secondary-400 mt-1">
            Clientes asignados a tu usuario ({clientes.length} total)
          </p>
        </div>
        <Button 
          variant="ghost" 
          size="sm" 
          onClick={() => refetch()}
          disabled={isFetching}
        >
          <RefreshCw className={`h-4 w-4 ${isFetching ? 'animate-spin' : ''}`} />
        </Button>
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
                placeholder="Buscar por nombre, RUT o razón social..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="w-full pl-10 pr-4 py-2.5 bg-secondary-800 border border-secondary-700 rounded-lg text-secondary-100 placeholder-secondary-500 focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              />
            </div>

            {/* Filtro Estado */}
            <div className="w-full sm:w-48">
              <Select
                options={estadoOptions}
                placeholder="Estado"
                value={filterActivo}
                onChange={(e) => setFilterActivo(e.target.value)}
              />
            </div>

            {/* Limpiar filtros */}
            {hasFilters && (
              <Button
                variant="ghost"
                size="sm"
                onClick={handleClearFilters}
                className="self-center"
              >
                Limpiar
              </Button>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Tabla de Clientes */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Building2 className="h-5 w-5 text-primary-400" />
            Lista de Clientes
            {hasFilters && clientesFiltrados.length !== clientes.length && (
              <span className="text-sm font-normal text-secondary-400 ml-2">
                (mostrando {clientesFiltrados.length} de {clientes.length})
              </span>
            )}
          </CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          <MisClientesTable clientes={clientesFiltrados} />
        </CardContent>
      </Card>
    </div>
  )
}

export default ClientesPage
