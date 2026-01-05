/**
 * Hook simplificado para gestionar asignación de usuario a cliente
 * Issue #7: Un cliente = Un usuario asignado
 */
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import api from '../../../api/axios'

// Query Key
const CLIENTES_KEY = ['clientes']

/**
 * Obtiene información de asignación de un cliente específico
 */
export const useInfoAsignacion = (clienteId) => {
  return useQuery({
    queryKey: ['cliente-asignacion', clienteId],
    queryFn: async () => {
      const { data } = await api.get(`/v1/core/clientes/${clienteId}/info_asignacion/`)
      return data
    },
    enabled: !!clienteId,
  })
}

/**
 * Mutation para asignar usuario a un cliente
 */
export const useAsignarUsuario = () => {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: async ({ clienteId, usuarioId }) => {
      const { data } = await api.post(
        `/v1/core/clientes/${clienteId}/asignar_usuario/`,
        { usuario_id: usuarioId }
      )
      return data
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: CLIENTES_KEY })
      queryClient.invalidateQueries({ queryKey: ['cliente-asignacion', variables.clienteId] })
      queryClient.invalidateQueries({ queryKey: ['clientes-todos'] })
    },
  })
}

/**
 * Mutation para desasignar usuario de un cliente (asigna null)
 */
export const useDesasignarUsuario = () => {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: async ({ clienteId }) => {
      const { data } = await api.post(
        `/v1/core/clientes/${clienteId}/asignar_usuario/`,
        { usuario_id: null }
      )
      return data
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: CLIENTES_KEY })
      queryClient.invalidateQueries({ queryKey: ['cliente-asignacion', variables.clienteId] })
      queryClient.invalidateQueries({ queryKey: ['clientes-todos'] })
    },
  })
}
