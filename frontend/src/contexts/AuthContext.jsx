/**
 * Context de autenticación
 * Integrado con Zustand store para persistencia
 */
import { createContext, useContext, useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '../api/axios'
import { useAuthStore } from '../stores/authStore'

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

  const value = {
    user,
    isAuthenticated,
    isLoading,
    login,
    logout,
    checkAuth,
  }

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  )
}

export default AuthProvider
