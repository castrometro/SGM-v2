/**
 * App principal con rutas protegidas por rol
 * Implementa code splitting con React.lazy para optimizar la carga inicial
 */
import { lazy, Suspense } from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuth } from './contexts/AuthContext'
import { usePermissions } from './hooks/usePermissions'

// Error Boundary
import ErrorBoundary from './components/ErrorBoundary'

// Suspense Fallback
import SuspenseFallback from './components/SuspenseFallback'

// ============================================================================
// EAGER IMPORTS (carga inmediata)
// ============================================================================
// Estos componentes se cargan inmediatamente porque son críticos para la app

// Layouts - necesario para la estructura inicial
import MainLayout from './components/layout/MainLayout'

// Auth - crítico para el acceso
import LoginPage from './features/auth/pages/LoginPage'

// ============================================================================
// LAZY IMPORTS (carga bajo demanda)
// ============================================================================
// Estos componentes se cargan solo cuando el usuario navega a ellos

// Dashboard
const DashboardPage = lazy(() => import('./features/dashboard/pages/DashboardPage'))

// Validador
const ValidadorListPage = lazy(() => import('./features/validador/pages/ValidadorListPage'))
const CierreDetailPage = lazy(() => import('./features/validador/pages/CierreDetailPage'))
const NuevoCierrePage = lazy(() => import('./features/validador/pages/NuevoCierrePage'))

// Clientes
const ClientesPage = lazy(() => import('./features/clientes/pages/ClientesPage'))
const ClienteDetailPage = lazy(() => import('./features/clientes/pages/ClienteDetailPage'))

// Incidencias (supervisor+)
const IncidenciasPage = lazy(() => import('./features/incidencias/pages/IncidenciasPage'))

// Supervisor
const MiEquipoPage = lazy(() => import('./features/supervisor/pages/MiEquipoPage'))
const CierresEquipoPage = lazy(() => import('./features/supervisor/pages/CierresEquipoPage'))

// Admin (gerente)
const UsuariosPage = lazy(() => import('./features/admin/pages/UsuariosPage'))
const AdminClientesPage = lazy(() => import('./features/admin/pages/AdminClientesPage'))

// Error Test (solo desarrollo)
const ErrorTestPage = lazy(() => import('./components/ErrorTestPage'))

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

/**
 * Wrapper para componentes lazy con Suspense
 * Muestra un fallback mientras el componente se carga
 */
const LazyRoute = ({ children }) => (
  <Suspense fallback={<SuspenseFallback />}>
    {children}
  </Suspense>
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
    <ErrorBoundary>
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
        <Route path="dashboard" element={<LazyRoute><DashboardPage /></LazyRoute>} />
        
        {/* Test Error Boundary (solo desarrollo) */}
        {import.meta.env.DEV && (
          <Route path="test-error" element={<LazyRoute><ErrorTestPage /></LazyRoute>} />
        )}
        
        {/* Validador / Mis Cierres */}
        <Route path="validador" element={<LazyRoute><ValidadorListPage /></LazyRoute>} />
        <Route path="validador/nuevo" element={<LazyRoute><NuevoCierrePage /></LazyRoute>} />
        <Route path="validador/cierre/:id" element={<LazyRoute><CierreDetailPage /></LazyRoute>} />
        
        {/* Mis Clientes */}
        <Route path="clientes" element={<LazyRoute><ClientesPage /></LazyRoute>} />
        <Route path="clientes/:id" element={<LazyRoute><ClienteDetailPage /></LazyRoute>} />
        
        {/* =================== RUTAS SUPERVISOR+ =================== */}
        <Route 
          path="equipo" 
          element={
            <SupervisorRoute>
              <LazyRoute><MiEquipoPage /></LazyRoute>
            </SupervisorRoute>
          } 
        />
        <Route 
          path="equipo/cierres" 
          element={
            <SupervisorRoute>
              <LazyRoute><CierresEquipoPage /></LazyRoute>
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
              <LazyRoute><IncidenciasPage /></LazyRoute>
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
              <LazyRoute><UsuariosPage /></LazyRoute>
            </GerenteRoute>
          } 
        />
        <Route 
          path="admin/clientes" 
          element={
            <GerenteRoute>
              <LazyRoute><AdminClientesPage /></LazyRoute>
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
    </ErrorBoundary>
  )
}

export default App
