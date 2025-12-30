/**
 * Store de autenticación con Zustand
 * Maneja el estado del usuario y tokens
 */
import { create } from 'zustand'
import { persist } from 'zustand/middleware'

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

      // Selectores de rol
      isAnalista: () => get().user?.tipo_usuario === 'analista',
      isSupervisor: () => get().user?.tipo_usuario === 'supervisor',
      isGerente: () => get().user?.tipo_usuario === 'gerente',
      isSupervisorOrHigher: () => 
        ['supervisor', 'gerente'].includes(get().user?.tipo_usuario),
      
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
