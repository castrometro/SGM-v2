/**
 * Hook para gestión de usuarios (CRUD)
 * Solo para rol Gerente
 */
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import api from '../../../api/axios'

const QUERY_KEY = 'admin-usuarios'

/**
 * Hook para obtener lista de usuarios
 */
export const useUsuarios = (filters = {}) => {
  const { search, tipo_usuario, is_active, supervisor } = filters

  return useQuery({
    queryKey: [QUERY_KEY, filters],
    queryFn: async () => {
      const params = new URLSearchParams()
      if (search) params.append('search', search)
      if (tipo_usuario) params.append('tipo_usuario', tipo_usuario)
      if (is_active !== undefined && is_active !== '') params.append('is_active', is_active)
      if (supervisor) params.append('supervisor', supervisor)
      
      const { data } = await api.get(`/v1/core/usuarios/todos/?${params.toString()}`)
      return data.results || data
    },
  })
}

/**
 * Hook para obtener un usuario específico
 */
export const useUsuario = (id) => {
  return useQuery({
    queryKey: [QUERY_KEY, id],
    queryFn: async () => {
      const { data } = await api.get(`/v1/core/usuarios/${id}/`)
      return data
    },
    enabled: !!id,
  })
}

/**
 * Hook para obtener supervisores (para select)
 */
export const useSupervisores = () => {
  return useQuery({
    queryKey: ['supervisores'],
    queryFn: async () => {
      const { data } = await api.get('/v1/core/usuarios/supervisores/')
      return data.results || data
    },
    staleTime: 5 * 60 * 1000,
  })
}

/**
 * Hook para crear usuario
 */
export const useCreateUsuario = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (usuarioData) => {
      const { data } = await api.post('/v1/core/usuarios/', usuarioData)
      return data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [QUERY_KEY] })
    },
  })
}

/**
 * Hook para actualizar usuario
 */
export const useUpdateUsuario = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async ({ id, ...usuarioData }) => {
      const { data } = await api.put(`/v1/core/usuarios/${id}/`, usuarioData)
      return data
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: [QUERY_KEY] })
      queryClient.setQueryData([QUERY_KEY, data.id], data)
    },
  })
}

/**
 * Hook para toggle estado activo
 */
export const useToggleUsuarioActivo = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (id) => {
      const { data } = await api.post(`/v1/core/usuarios/${id}/toggle_active/`)
      return data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [QUERY_KEY] })
    },
  })
}

/**
 * Hook para reset password
 */
export const useResetPassword = () => {
  return useMutation({
    mutationFn: async ({ id, new_password, confirm_password }) => {
      const { data } = await api.post(`/v1/core/usuarios/${id}/reset_password/`, {
        new_password,
        confirm_password,
      })
      return data
    },
  })
}

/**
 * Hook para eliminar usuario
 */
export const useDeleteUsuario = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (id) => {
      await api.delete(`/v1/core/usuarios/${id}/`)
      return id
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [QUERY_KEY] })
    },
  })
}
