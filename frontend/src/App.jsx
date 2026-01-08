/**
 * App principal con rutas protegidas por rol
 */
import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuth } from './contexts/AuthContext'
import { usePermissions } from './hooks/usePermissions'

// Layouts
import MainLayout from './components/layout/MainLayout'

// Auth
import LoginPage from './features/auth/pages/LoginPage'

// Dashboard
import DashboardPage from './features/dashboard/pages/DashboardPage'

// Validador
import ValidadorListPage from './features/validador/pages/ValidadorListPage'
import CierreDetailPage from './features/validador/pages/CierreDetailPage'
import NuevoCierrePage from './features/validador/pages/NuevoCierrePage'

// Clientes  
import ClientesPage from './features/clientes/pages/ClientesPage'
import ClienteDetailPage from './features/clientes/pages/ClienteDetailPage'

// Incidencias (supervisor+)
import IncidenciasPage from './features/incidencias/pages/IncidenciasPage'

// Admin (solo gerente)
import UsuariosPage from './features/admin/pages/UsuariosPage'
import AdminClientesPage from './features/admin/pages/AdminClientesPage'

// Supervisor
import { MiEquipoPage, CierresEquipoPage } from './features/supervisor'

// ============================================================================
// COMPONENTES DE PROTECCIÓN DE RUTAS
// ============================================================================

const LoadingSpinner = () => (
  <div className="min-h-screen flex items-center justify-center bg-secondary-950">
    <div className="flex flex-col items-center gap-4">
      <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-500"></div>
      <p className="text-secondary-400 text-sm">Cargando...</p>
    </div>
  </div>
)

const ProtectedRoute = ({ children }) => {
  const { isAuthenticated, isLoading } = useAuth()
  
  if (isLoading) return <LoadingSpinner />
  if (!isAuthenticated) return <Navigate to="/login" replace />
  
  return children
}

const SupervisorRoute = ({ children }) => {
  const { isAuthenticated, isLoading } = useAuth()
  const { isSupervisorOrHigher } = usePermissions()
  
  if (isLoading) return <LoadingSpinner />
  if (!isAuthenticated) return <Navigate to="/login" replace />
  if (!isSupervisorOrHigher) return <Navigate to="/dashboard" replace />
  
  return children
}

const GerenteRoute = ({ children }) => {
  const { isAuthenticated, isLoading } = useAuth()
  const { isGerente } = usePermissions()
  
  if (isLoading) return <LoadingSpinner />
  if (!isAuthenticated) return <Navigate to="/login" replace />
  if (!isGerente) return <Navigate to="/dashboard" replace />
  
  return children
}

// Placeholder para páginas no implementadas
const PlaceholderPage = ({ title }) => (
  <div className="flex flex-col items-center justify-center h-full gap-4 text-secondary-400">
    <div className="text-6xl">🚧</div>
    <h2 className="text-xl font-semibold text-secondary-200">{title}</h2>
    <p className="text-sm">Página en construcción</p>
  </div>
)

// ============================================================================
// APP
// ============================================================================

function App() {
  return (
    <Routes>
      {/* ===================== RUTAS PÚBLICAS ===================== */}
      <Route path="/login" element={<LoginPage />} />
      
      {/* ===================== RUTAS PROTEGIDAS ===================== */}
      <Route
        path="/"
        element={
          <ProtectedRoute>
            <MainLayout />
          </ProtectedRoute>
        }
      >
        {/* Index redirect */}
        <Route index element={<Navigate to="/dashboard" replace />} />
        
        {/* =================== RUTAS COMUNES (todos los roles) =================== */}
        <Route path="dashboard" element={<DashboardPage />} />
        
        {/* Validador / Mis Cierres */}
        <Route path="validador" element={<ValidadorListPage />} />
        <Route path="validador/nuevo" element={<NuevoCierrePage />} />
        <Route path="validador/cierre/:id" element={<CierreDetailPage />} />
        
        {/* Mis Clientes */}
        <Route path="clientes" element={<ClientesPage />} />
        <Route path="clientes/:id" element={<ClienteDetailPage />} />
        
        {/* =================== RUTAS SUPERVISOR+ =================== */}
        <Route 
          path="equipo" 
          element={
            <SupervisorRoute>
              <MiEquipoPage />
            </SupervisorRoute>
          } 
        />
        <Route 
          path="equipo/cierres" 
          element={
            <SupervisorRoute>
              <CierresEquipoPage />
            </SupervisorRoute>
          } 
        />
        <Route 
          path="equipo/incidencias" 
          element={
            <SupervisorRoute>
              <PlaceholderPage title="Incidencias del Equipo" />
            </SupervisorRoute>
          } 
        />
        <Route 
          path="incidencias" 
          element={
            <SupervisorRoute>
              <IncidenciasPage />
            </SupervisorRoute>
          } 
        />
        
        {/* =================== RUTAS GERENTE =================== */}
        <Route 
          path="ejecutivo" 
          element={
            <GerenteRoute>
              <PlaceholderPage title="Dashboard Ejecutivo" />
            </GerenteRoute>
          } 
        />
        <Route 
          path="reportes" 
          element={
            <GerenteRoute>
              <PlaceholderPage title="Reportes" />
            </GerenteRoute>
          } 
        />
        <Route 
          path="cierres" 
          element={
            <GerenteRoute>
              <PlaceholderPage title="Todos los Cierres" />
            </GerenteRoute>
          } 
        />
        
        {/* Administración */}
        <Route 
          path="admin/usuarios" 
          element={
            <GerenteRoute>
              <UsuariosPage />
            </GerenteRoute>
          } 
        />
        <Route 
          path="admin/clientes" 
          element={
            <GerenteRoute>
              <AdminClientesPage />
            </GerenteRoute>
          } 
        />
        <Route 
          path="admin/servicios" 
          element={
            <GerenteRoute>
              <PlaceholderPage title="Administrar Servicios" />
            </GerenteRoute>
          } 
        />
      </Route>
      
      {/* ===================== 404 ===================== */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}

export default App
