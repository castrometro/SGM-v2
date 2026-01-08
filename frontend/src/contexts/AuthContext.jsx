/**
 * Context de autenticación
 * Integrado con Zustand store para persistencia
 * 
 * USO ESTÁNDAR:
 * - En componentes React: usar `useAuth()` (este hook)
 * - En archivos no-React (ej: axios interceptors): usar `useAuthStore.getState()`
 * - Para permisos detallados: usar `usePermissions()`
 * 
 * @see Issue #16 - Consolidación Context vs Zustand
 */
import { createContext, useContext, useState, useEffect, useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '../api/axios'
import { useAuthStore } from '../stores/authStore'
import { TIPO_USUARIO, PUEDEN_SUPERVISAR, PUEDEN_APROBAR } from '../constants'

const AuthContext = createContext(null)

export const useAuth = () => {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth debe usarse dentro de AuthProvider')
  }
  return context
}

export const AuthProvider = ({ children }) => {
  const [isLoading, setIsLoading] = useState(true)
  const navigate = useNavigate()
  
  // Store de Zustand
  const { 
    user, 
    accessToken, 
    setAuth, 
    setUser, 
    logout: storeLogout,
    isAuthenticated 
  } = useAuthStore()

  // Verificar si hay sesión al cargar
  useEffect(() => {
    checkAuth()
  }, [])

  const checkAuth = async () => {
    if (!accessToken) {
      setIsLoading(false)
      return
    }

    try {
      const response = await api.get('/v1/core/me/')
      setUser(response.data)
    } catch (error) {
      console.error('Error verificando auth:', error)
      storeLogout()
    } finally {
      setIsLoading(false)
    }
  }

  const login = async (email, password) => {
    const response = await api.post('/auth/token/', { email, password })
    const { access, refresh } = response.data

    // Guardar tokens en el store
    setAuth(null, access, refresh)

    // Obtener datos del usuario
    const userResponse = await api.get('/v1/core/me/')
    setUser(userResponse.data)

    return userResponse.data
  }

  const logout = () => {
    storeLogout()
    navigate('/login')
  }

  // Helpers de rol derivados (Issue #16 - estandarización)
  const roleHelpers = useMemo(() => ({
    isAnalista: user?.tipo_usuario === TIPO_USUARIO.ANALISTA,
    isSupervisor: user?.tipo_usuario === TIPO_USUARIO.SUPERVISOR,
    isGerente: user?.tipo_usuario === TIPO_USUARIO.GERENTE,
    isSupervisorOrHigher: PUEDEN_SUPERVISAR.includes(user?.tipo_usuario),
    canApprove: PUEDEN_APROBAR.includes(user?.tipo_usuario),
  }), [user?.tipo_usuario])

  const value = {
    user,
    isAuthenticated,
    isLoading,
    login,
    logout,
    checkAuth,
    // Helpers de rol expuestos para conveniencia
    ...roleHelpers,
  }

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  )
}

export default AuthProvider
