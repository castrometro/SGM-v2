/**
 * Hook para gestión de clientes (CRUD)
 * Solo para rol Gerente
 */
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import api from '../../../api/axios'

const QUERY_KEY = 'admin-clientes'

/**
 * Hook para obtener lista de clientes
 */
export const useClientes = (filters = {}) => {
  const { search, activo, industria } = filters

  return useQuery({
    queryKey: [QUERY_KEY, filters],
    queryFn: async () => {
      const params = new URLSearchParams()
      if (search) params.append('search', search)
      if (activo !== undefined && activo !== '') params.append('activo', activo)
      if (industria) params.append('industria', industria)
      
      const { data } = await api.get(`/v1/core/clientes/todos/?${params.toString()}`)
      return data.results || data
    },
  })
}

/**
 * Hook para obtener un cliente específico
 */
export const useCliente = (id) => {
  return useQuery({
    queryKey: [QUERY_KEY, id],
    queryFn: async () => {
      const { data } = await api.get(`/v1/core/clientes/${id}/`)
      return data
    },
    enabled: !!id,
  })
}

/**
 * Hook para obtener industrias
 */
export const useIndustrias = () => {
  return useQuery({
    queryKey: ['industrias'],
    queryFn: async () => {
      const { data } = await api.get('/v1/core/industrias/')
      return data.results || data
    },
    staleTime: 5 * 60 * 1000, // 5 minutos
  })
}

/**
 * Hook para crear cliente
 */
export const useCreateCliente = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (clienteData) => {
      const { data } = await api.post('/v1/core/clientes/', clienteData)
      return data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [QUERY_KEY] })
    },
  })
}

/**
 * Hook para actualizar cliente
 */
export const useUpdateCliente = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async ({ id, ...clienteData }) => {
      const { data } = await api.put(`/v1/core/clientes/${id}/`, clienteData)
      return data
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: [QUERY_KEY] })
      queryClient.setQueryData([QUERY_KEY, data.id], data)
    },
  })
}

/**
 * Hook para eliminar cliente (soft delete)
 */
export const useDeleteCliente = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (id) => {
      await api.delete(`/v1/core/clientes/${id}/`)
      return id
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [QUERY_KEY] })
    },
  })
}

/**
 * Hook para toggle estado activo
 */
export const useToggleClienteActivo = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async ({ id, activo }) => {
      const { data } = await api.patch(`/v1/core/clientes/${id}/`, { activo })
      return data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [QUERY_KEY] })
    },
  })
}

// ============================================
// Hooks para Issue #5: Vista de Supervisor
// ============================================

/**
 * Hook para obtener clientes del equipo del supervisor
 */
export const useMiEquipo = () => {
  return useQuery({
    queryKey: ['mi-equipo'],
    queryFn: async () => {
      const { data } = await api.get('/v1/core/clientes/mi_equipo/')
      return data
    },
  })
}

/**
 * Hook para reasignar cliente a otro analista del equipo
 */
export const useReasignarCliente = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async ({ clienteId, usuarioId }) => {
      const { data } = await api.post(
        `/v1/core/clientes/${clienteId}/reasignar/`,
        { usuario_id: usuarioId }
      )
      return data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['mi-equipo'] })
      queryClient.invalidateQueries({ queryKey: [QUERY_KEY] })
      queryClient.invalidateQueries({ queryKey: ['clientes'] })
    },
  })
}
