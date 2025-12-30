import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuth } from './contexts/AuthContext'

// Layouts
import MainLayout from './components/layout/MainLayout'

// Pages
import LoginPage from './features/auth/pages/LoginPage'
import DashboardPage from './features/dashboard/pages/DashboardPage'

// Protected Route wrapper
const ProtectedRoute = ({ children }) => {
  const { isAuthenticated, isLoading } = useAuth()
  
  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-secondary-950">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-500"></div>
      </div>
    )
  }
  
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }
  
  return children
}

function App() {
  return (
    <Routes>
      {/* Public routes */}
      <Route path="/login" element={<LoginPage />} />
      
      {/* Protected routes */}
      <Route
        path="/"
        element={
          <ProtectedRoute>
            <MainLayout />
          </ProtectedRoute>
        }
      >
        <Route index element={<Navigate to="/dashboard" replace />} />
        <Route path="dashboard" element={<DashboardPage />} />
        
        {/* Clientes */}
        <Route path="clientes" element={<div>Clientes - TODO</div>} />
        <Route path="clientes/:id" element={<div>Cliente Detalle - TODO</div>} />
        
        {/* Validador */}
        <Route path="validador" element={<div>Validador - TODO</div>} />
        <Route path="validador/cierre/:id" element={<div>Cierre Detalle - TODO</div>} />
        
        {/* Reportería */}
        <Route path="reportes" element={<div>Reportes - TODO</div>} />
        
        {/* Administración */}
        <Route path="admin/usuarios" element={<div>Usuarios - TODO</div>} />
      </Route>
      
      {/* 404 */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}

export default App
