/**
 * Store de autenticación con Zustand
 * Maneja el estado del usuario y tokens con persistencia
 * 
 * CUÁNDO USAR (Issue #16 - Consolidación):
 * 
 * 1. En componentes React: usar `useAuth()` de AuthContext
 *    - const { user, login, logout, isLoading } = useAuth()
 * 
 * 2. En axios interceptors u otros NO-React: usar `useAuthStore.getState()`
 *    - const { accessToken, refreshToken } = useAuthStore.getState()
 * 
 * 3. Para permisos detallados: usar `usePermissions()`
 *    - const { canApproveIncidencia, isGerente } = usePermissions()
 * 
 * @see contexts/AuthContext.jsx - wrapper que expone useAuth()
 * @see hooks/usePermissions.js - permisos detallados
 */
import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import { TIPO_USUARIO, PUEDEN_SUPERVISAR } from '../constants'

export const useAuthStore = create(
  persist(
    (set, get) => ({
      // Estado
      user: null,
      accessToken: null,
      refreshToken: null,
      isAuthenticated: false,

      // Acciones
      setAuth: (user, accessToken, refreshToken) => {
        set({
          user,
          accessToken,
          refreshToken,
          isAuthenticated: !!user,
        })
      },

      setUser: (user) => {
        set({ user, isAuthenticated: !!user })
      },

      setTokens: (accessToken, refreshToken) => {
        set({ accessToken, refreshToken })
      },

      logout: () => {
        set({
          user: null,
          accessToken: null,
          refreshToken: null,
          isAuthenticated: false,
        })
      },

      // Selectores de rol (usando constantes)
      isAnalista: () => get().user?.tipo_usuario === TIPO_USUARIO.ANALISTA,
      isSupervisor: () => get().user?.tipo_usuario === TIPO_USUARIO.SUPERVISOR,
      isGerente: () => get().user?.tipo_usuario === TIPO_USUARIO.GERENTE,
      isSupervisorOrHigher: () => 
        PUEDEN_SUPERVISAR.includes(get().user?.tipo_usuario),
      
      // Helpers
      getUserInitials: () => {
        const user = get().user
        if (!user) return ''
        return `${user.nombre?.[0] || ''}${user.apellido?.[0] || ''}`.toUpperCase()
      },

      getUserFullName: () => {
        const user = get().user
        if (!user) return ''
        return `${user.nombre} ${user.apellido}`
      },
    }),
    {
      name: 'sgm-auth',
      partialize: (state) => ({
        accessToken: state.accessToken,
        refreshToken: state.refreshToken,
      }),
    }
  )
)

export default useAuthStore
