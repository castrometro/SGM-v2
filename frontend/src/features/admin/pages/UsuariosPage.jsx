/**
 * Página de administración de usuarios (solo gerente)
 * CRUD completo: listar, crear, editar, activar/desactivar, resetear contraseña, eliminar
 */
import { useState, useMemo } from 'react'
import { 
  Users, 
  Plus, 
  Search,
  Shield,
  UserCheck,
  Briefcase,
  CheckCircle,
  XCircle,
  Filter,
  RefreshCw
} from 'lucide-react'
import { useAuth } from '../../../contexts/AuthContext'
import { Card, CardContent, Modal, Select } from '../../../components/ui'
import Button from '../../../components/ui/Button'
import { TIPO_USUARIO } from '../../../constants'
import { 
  useUsuarios, 
  useCreateUsuario, 
  useUpdateUsuario, 
  useToggleUsuarioActivo, 
  useResetPassword, 
  useDeleteUsuario,
  useSupervisores 
} from '../hooks'
import { UsuarioForm, UsuariosTable, AsignacionSupervisorModal } from '../components'
import toast from 'react-hot-toast'

const UsuariosPage = () => {
  const { user: currentUser } = useAuth()
  const [search, setSearch] = useState('')
  const [filtroTipo, setFiltroTipo] = useState('')
  const [filtroEstado, setFiltroEstado] = useState('')
  
  // Modal states
  const [modalOpen, setModalOpen] = useState(false)
  const [usuarioEditar, setUsuarioEditar] = useState(null)
  const [supervisorModalOpen, setSupervisorModalOpen] = useState(false)
  const [analistaAsignar, setAnalistaAsignar] = useState(null)

  // Data hooks
  const { data: usuarios = [], isLoading, refetch, isRefetching } = useUsuarios()
  const { data: supervisores = [] } = useSupervisores()
  
  // Mutation hooks
  const createUsuario = useCreateUsuario()
  const updateUsuario = useUpdateUsuario()
  const toggleActivo = useToggleUsuarioActivo()
  const resetPassword = useResetPassword()
  const deleteUsuario = useDeleteUsuario()

  // Filtrado de usuarios
  const usuariosFiltrados = useMemo(() => {
    return usuarios.filter((usuario) => {
      // Filtro de búsqueda
      const searchLower = search.toLowerCase()
      const matchSearch = !search || 
        usuario.nombre?.toLowerCase().includes(searchLower) ||
        usuario.apellido?.toLowerCase().includes(searchLower) ||
        usuario.email?.toLowerCase().includes(searchLower) ||
        usuario.cargo?.toLowerCase().includes(searchLower)
      
      // Filtro de tipo
      const matchTipo = !filtroTipo || usuario.tipo_usuario === filtroTipo
      
      // Filtro de estado
      const matchEstado = !filtroEstado || 
        (filtroEstado === 'activo' && usuario.is_active) ||
        (filtroEstado === 'inactivo' && !usuario.is_active)
      
      return matchSearch && matchTipo && matchEstado
    })
  }, [usuarios, search, filtroTipo, filtroEstado])

  // Estadísticas
  const stats = useMemo(() => ({
    total: usuarios.length,
    gerentes: usuarios.filter(u => u.tipo_usuario === TIPO_USUARIO.GERENTE).length,
    supervisores: usuarios.filter(u => u.tipo_usuario === TIPO_USUARIO.SUPERVISOR).length,
    analistas: usuarios.filter(u => u.tipo_usuario === TIPO_USUARIO.ANALISTA).length,
    activos: usuarios.filter(u => u.is_active).length,
    inactivos: usuarios.filter(u => !u.is_active).length,
  }), [usuarios])

  // Handlers
  const handleCreate = () => {
    setUsuarioEditar(null)
    setModalOpen(true)
  }

  const handleEdit = (usuario) => {
    setUsuarioEditar(usuario)
    setModalOpen(true)
  }

  const handleCloseModal = () => {
    setModalOpen(false)
    setUsuarioEditar(null)
  }

  const handleAsignarSupervisor = (analista) => {
    setAnalistaAsignar(analista)
    setSupervisorModalOpen(true)
  }

  const handleCloseSupervisorModal = () => {
    setSupervisorModalOpen(false)
    setAnalistaAsignar(null)
  }

  const handleSubmit = async (data) => {
    try {
      if (usuarioEditar) {
        await updateUsuario.mutateAsync({ id: usuarioEditar.id, data })
        toast.success('Usuario actualizado correctamente')
      } else {
        await createUsuario.mutateAsync(data)
        toast.success('Usuario creado correctamente')
      }
      handleCloseModal()
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Error al guardar usuario')
    }
  }

  const handleToggleActive = async (id) => {
    try {
      const result = await toggleActivo.mutateAsync(id)
      toast.success(
        result.is_active 
          ? 'Usuario activado correctamente' 
          : 'Usuario desactivado correctamente'
      )
    } catch (error) {
      toast.error('Error al cambiar estado del usuario')
    }
  }

  const handleResetPassword = async (id) => {
    try {
      const result = await resetPassword.mutateAsync(id)
      toast.success(
        <div>
          <p>Contraseña reseteada</p>
          <p className="text-sm mt-1">Nueva: <code className="bg-secondary-700 px-1 rounded">{result.new_password}</code></p>
        </div>,
        { duration: 10000 }
      )
    } catch (error) {
      toast.error('Error al resetear contraseña')
    }
  }

  const handleDelete = async (id) => {
    try {
      await deleteUsuario.mutateAsync(id)
      toast.success('Usuario eliminado correctamente')
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Error al eliminar usuario')
    }
  }

  // Opciones para filtros
  const tipoOptions = [
    { value: '', label: 'Todos los roles' },
    { value: 'gerente', label: 'Gerentes' },
    { value: 'supervisor', label: 'Supervisores' },
    { value: 'analista', label: 'Analistas' },
  ]

  const estadoOptions = [
    { value: '', label: 'Todos los estados' },
    { value: 'activo', label: 'Activos' },
    { value: 'inactivo', label: 'Inactivos' },
  ]

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-secondary-100 flex items-center gap-3">
            <Users className="h-7 w-7 text-primary-500" />
            Usuarios
          </h1>
          <p className="text-secondary-400 mt-1">
            Administra los usuarios del sistema
          </p>
        </div>
        <Button onClick={handleCreate}>
          <Plus className="h-4 w-4" />
          Nuevo Usuario
        </Button>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
        <Card className="bg-secondary-800/50 border-secondary-700">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <Users className="h-8 w-8 text-primary-500" />
              <div>
                <p className="text-2xl font-bold text-white">{stats.total}</p>
                <p className="text-xs text-secondary-400">Total</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-secondary-800/50 border-secondary-700">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <Shield className="h-8 w-8 text-danger-500" />
              <div>
                <p className="text-2xl font-bold text-white">{stats.gerentes}</p>
                <p className="text-xs text-secondary-400">Gerentes</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-secondary-800/50 border-secondary-700">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <UserCheck className="h-8 w-8 text-warning-500" />
              <div>
                <p className="text-2xl font-bold text-white">{stats.supervisores}</p>
                <p className="text-xs text-secondary-400">Supervisores</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-secondary-800/50 border-secondary-700">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <Briefcase className="h-8 w-8 text-info-500" />
              <div>
                <p className="text-2xl font-bold text-white">{stats.analistas}</p>
                <p className="text-xs text-secondary-400">Analistas</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-secondary-800/50 border-secondary-700">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <CheckCircle className="h-8 w-8 text-success-500" />
              <div>
                <p className="text-2xl font-bold text-white">{stats.activos}</p>
                <p className="text-xs text-secondary-400">Activos</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-secondary-800/50 border-secondary-700">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <XCircle className="h-8 w-8 text-secondary-500" />
              <div>
                <p className="text-2xl font-bold text-white">{stats.inactivos}</p>
                <p className="text-xs text-secondary-400">Inactivos</p>
              </div>
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
                placeholder="Buscar por nombre, email o cargo..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="w-full pl-10 pr-4 py-2.5 bg-secondary-800 border border-secondary-700 rounded-lg text-secondary-100 placeholder-secondary-500 focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              />
            </div>
            
            {/* Filtro por tipo */}
            <div className="w-full lg:w-48">
              <Select
                value={filtroTipo}
                onChange={(e) => setFiltroTipo(e.target.value)}
                options={tipoOptions}
                placeholder="Rol"
              />
            </div>
            
            {/* Filtro por estado */}
            <div className="w-full lg:w-48">
              <Select
                value={filtroEstado}
                onChange={(e) => setFiltroEstado(e.target.value)}
                options={estadoOptions}
                placeholder="Estado"
              />
            </div>

            {/* Acciones de filtro */}
            <div className="flex items-center gap-2">
              {(search || filtroTipo || filtroEstado) && (
                <Button 
                  variant="ghost" 
                  size="sm"
                  onClick={() => {
                    setSearch('')
                    setFiltroTipo('')
                    setFiltroEstado('')
                  }}
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

      {/* Tabla de usuarios */}
      <Card>
        <CardContent className="p-0">
          <UsuariosTable
            usuarios={usuariosFiltrados}
            isLoading={isLoading}
            onEdit={handleEdit}
            onToggleActive={handleToggleActive}
            onResetPassword={handleResetPassword}
            onDelete={handleDelete}
            onAsignarSupervisor={handleAsignarSupervisor}
            currentUserId={currentUser?.id}
          />
        </CardContent>
      </Card>

      {/* Resumen de resultados */}
      {!isLoading && (
        <p className="text-sm text-secondary-500 text-center">
          Mostrando {usuariosFiltrados.length} de {usuarios.length} usuarios
        </p>
      )}

      {/* Modal de crear/editar */}
      <Modal
        isOpen={modalOpen}
        onClose={handleCloseModal}
        title={usuarioEditar ? 'Editar Usuario' : 'Nuevo Usuario'}
        size="lg"
      >
        <UsuarioForm
          usuario={usuarioEditar}
          supervisores={supervisores}
          onSubmit={handleSubmit}
          onCancel={handleCloseModal}
          isLoading={createUsuario.isPending || updateUsuario.isPending}
        />
      </Modal>

      {/* Modal de asignación de supervisor */}
      <AsignacionSupervisorModal
        isOpen={supervisorModalOpen}
        onClose={handleCloseSupervisorModal}
        analista={analistaAsignar}
      />
    </div>
  )
}

export default UsuariosPage
