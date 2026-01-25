/**
 * Hooks para gestión de discrepancias del validador.
 * 
 * Incluye:
 * - Generación de discrepancias con polling de progreso
 * - Consulta de discrepancias con filtros
 * - Resolución de discrepancias
 * 
 * @module features/validador/hooks/useDiscrepancias
 */
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useState, useCallback } from 'react'
import api from '../../../api/axios'
import { POLLING_INTERVALS, ESTADO_CIERRE } from '../../../constants'

/**
 * Hook para generar discrepancias (comparación ERP vs Analista).
 * 
 * Dispara el task Celery y maneja el polling de progreso automáticamente.
 * 
 * @param {string|number} cierreId - ID del cierre
 * @returns {Object} - { generarDiscrepancias, progreso, isGenerating, error }
 */
export const useGenerarDiscrepancias = (cierreId) => {
  const queryClient = useQueryClient()
  const [isGenerating, setIsGenerating] = useState(false)
  const [error, setError] = useState(null)

  // Query para polling de progreso
  const { data: progreso, refetch: refetchProgreso } = useQuery({
    queryKey: ['progreso-comparacion', cierreId],
    queryFn: async () => {
      const { data } = await api.get(`/v1/validador/cierres/${cierreId}/progreso-comparacion/`)
      return data
    },
    enabled: isGenerating && !!cierreId,
    refetchInterval: (query) => {
      const data = query.state.data
      // Seguir polling mientras esté comparando
      if (data?.estado === 'comparando') {
        return POLLING_INTERVALS.TAREA_CELERY
      }
      // Cuando termina, parar polling e invalidar queries
      if (data?.estado === 'completado') {
        setIsGenerating(false)
        setError(null)
        queryClient.invalidateQueries({ queryKey: ['cierre', cierreId] })
        queryClient.invalidateQueries({ queryKey: ['discrepancias', cierreId] })
      }
      if (data?.estado === 'error') {
        setIsGenerating(false)
        setError(data.mensaje || 'Error al generar discrepancias')
        queryClient.invalidateQueries({ queryKey: ['cierre', cierreId] })
      }
      return false
    },
  })

  // Mutation para iniciar la generación
  const mutation = useMutation({
    mutationFn: async () => {
      const { data } = await api.post(`/v1/validador/cierres/${cierreId}/generar-discrepancias/`)
      return data
    },
    onSuccess: () => {
      setIsGenerating(true)
      setError(null)
      // Iniciar polling
      refetchProgreso()
    },
    onError: (err) => {
      setError(err.response?.data?.error || 'Error al generar discrepancias')
      setIsGenerating(false)
    },
  })

  const generarDiscrepancias = useCallback(() => {
    setError(null)
    mutation.mutate()
  }, [mutation])

  return {
    generarDiscrepancias,
    progreso: progreso || { estado: 'pendiente', progreso: 0, mensaje: 'Listo para iniciar' },
    isGenerating,
    error,
    isStarting: mutation.isPending,
  }
}

/**
 * Hook para obtener discrepancias de un cierre.
 * 
 * @param {string|number} cierreId - ID del cierre
 * @param {Object} filtros - Filtros opcionales { tipo, origen, resuelta }
 * @returns {UseQueryResult} - Resultado de React Query
 */
export const useDiscrepancias = (cierreId, filtros = {}) => {
  return useQuery({
    queryKey: ['discrepancias', cierreId, filtros],
    queryFn: async () => {
      const params = { cierre: cierreId, ...filtros }
      const { data } = await api.get('/v1/validador/discrepancias/', { params })
      return data
    },
    enabled: !!cierreId,
  })
}

/**
 * Hook para obtener resumen de discrepancias.
 * 
 * @param {string|number} cierreId - ID del cierre
 * @returns {UseQueryResult} - { total, por_tipo, por_origen, resueltas, pendientes }
 */
export const useResumenDiscrepancias = (cierreId) => {
  return useQuery({
    queryKey: ['discrepancias-resumen', cierreId],
    queryFn: async () => {
      const { data } = await api.get('/v1/validador/discrepancias/resumen/', {
        params: { cierre: cierreId }
      })
      return data
    },
    enabled: !!cierreId,
  })
}

/**
 * Hook para resolver una discrepancia.
 * 
 * @returns {UseMutationResult}
 */
export const useResolverDiscrepancia = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async ({ discrepanciaId, resolucion }) => {
      const { data } = await api.post(`/v1/validador/discrepancias/${discrepanciaId}/resolver/`, {
        resolucion,
      })
      return data
    },
    onSuccess: (_, { cierreId }) => {
      queryClient.invalidateQueries({ queryKey: ['discrepancias', cierreId] })
      queryClient.invalidateQueries({ queryKey: ['discrepancias-resumen', cierreId] })
      queryClient.invalidateQueries({ queryKey: ['cierre', cierreId] })
    },
  })
}

/**
 * Tipos de discrepancia con metadata para UI
 */
export const TIPOS_DISCREPANCIA = [
  { value: 'monto_diferente', label: 'Monto Diferente', color: 'warning', icon: 'DollarSign' },
  { value: 'falta_en_erp', label: 'Falta en ERP', color: 'danger', icon: 'FileX' },
  { value: 'falta_en_cliente', label: 'Falta en Cliente', color: 'info', icon: 'FileQuestion' },
  { value: 'empleado_no_encontrado', label: 'Empleado No Encontrado', color: 'danger', icon: 'UserX' },
  { value: 'item_no_mapeado', label: 'Item No Mapeado', color: 'secondary', icon: 'Link2Off' },
]

/**
 * Orígenes de discrepancia con metadata para UI
 */
export const ORIGENES_DISCREPANCIA = [
  { value: 'libro_vs_novedades', label: 'Libro vs Novedades', description: 'Comparación de montos' },
  { value: 'movimientos_vs_analista', label: 'Movimientos vs Analista', description: 'Comparación de ingresos/bajas' },
]

/**
 * Helper para obtener metadata de tipo de discrepancia
 */
export const getTipoDiscrepanciaInfo = (tipo) => {
  return TIPOS_DISCREPANCIA.find(t => t.value === tipo) || { label: tipo, color: 'default' }
}

/**
 * Helper para obtener metadata de origen de discrepancia
 */
export const getOrigenDiscrepanciaInfo = (origen) => {
  return ORIGENES_DISCREPANCIA.find(o => o.value === origen) || { label: origen }
}
