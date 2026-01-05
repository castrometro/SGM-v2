/**
 * Hook para gestionar asignaciones cliente-analista/supervisor
 */
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import api from '../../../api/axios'

// Query Keys
const CLIENTES_ASIGNACIONES_KEY = ['clientes-asignaciones']
const SUPERVISORES_CARGA_KEY = ['supervisores-carga']

/**
 * Obtiene todos los clientes con sus asignaciones (solo gerentes)
 */
export const useClientesConAsignaciones = (filters = {}) => {
  return useQuery({
    queryKey: [...CLIENTES_ASIGNACIONES_KEY, filters],
    queryFn: async () => {
      const params = new URLSearchParams()
      if (filters.search) params.append('search', filters.search)
      if (filters.supervisor) params.append('supervisor', filters.supervisor)
      if (filters.sinSupervisor) params.append('sin_supervisor', 'true')
      if (filters.sinAnalistas) params.append('sin_analistas', 'true')
      
      const { data } = await api.get(`/v1/core/clientes/con_asignaciones/?${params}`)
      return data
    },
  })
}

/**
 * Obtiene las asignaciones de un cliente específico
 */
export const useAsignacionesCliente = (clienteId) => {
  return useQuery({
    queryKey: ['cliente-asignaciones', clienteId],
    queryFn: async () => {
      const { data } = await api.get(`/v1/core/clientes/${clienteId}/asignaciones/`)
      return data
    },
    enabled: !!clienteId,
  })
}

/**
 * Obtiene la carga de trabajo de todos los supervisores
 */
export const useSupervisoresCarga = () => {
  return useQuery({
    queryKey: SUPERVISORES_CARGA_KEY,
    queryFn: async () => {
      const { data } = await api.get('/v1/core/clientes/supervisores_carga/')
      return data
    },
  })
}

/**
 * Mutation para asignar supervisor a un cliente
 */
export const useAsignarSupervisor = () => {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: async ({ clienteId, supervisorId }) => {
      const { data } = await api.post(
        `/v1/core/clientes/${clienteId}/asignar_supervisor/`,
        { supervisor_id: supervisorId }
      )
      return data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: CLIENTES_ASIGNACIONES_KEY })
      queryClient.invalidateQueries({ queryKey: SUPERVISORES_CARGA_KEY })
      queryClient.invalidateQueries({ queryKey: ['clientes'] })
    },
  })
}

/**
 * Mutation para asignar analista a un cliente
 */
export const useAsignarAnalista = () => {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: async ({ clienteId, usuarioId, esPrincipal = false, notas = '' }) => {
      const { data } = await api.post(
        `/v1/core/clientes/${clienteId}/asignar_analista/`,
        { 
          usuario_id: usuarioId,
          es_principal: esPrincipal,
          notas 
        }
      )
      return data
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: CLIENTES_ASIGNACIONES_KEY })
      queryClient.invalidateQueries({ queryKey: ['cliente-asignaciones', variables.clienteId] })
      queryClient.invalidateQueries({ queryKey: ['clientes'] })
    },
  })
}

/**
 * Mutation para desasignar analista de un cliente
 */
export const useDesasignarAnalista = () => {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: async ({ clienteId, usuarioId }) => {
      const { data } = await api.post(
        `/v1/core/clientes/${clienteId}/desasignar_analista/${usuarioId}/`
      )
      return data
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: CLIENTES_ASIGNACIONES_KEY })
      queryClient.invalidateQueries({ queryKey: ['cliente-asignaciones', variables.clienteId] })
      queryClient.invalidateQueries({ queryKey: ['clientes'] })
    },
  })
}
