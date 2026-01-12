/**
 * Hooks para gestión de archivos del validador (ERP y Analista)
 * 
 * Incluye polling automático cuando hay archivos en procesamiento.
 * @module features/validador/hooks/useArchivos
 */
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import api from '../../../api/axios'
import { 
  TIPO_ARCHIVO_ERP, 
  TIPO_ARCHIVO_ANALISTA,
  ESTADOS_ARCHIVO_PROCESANDO,
  POLLING_INTERVALS,
} from '../../../constants'

// Tipos de archivos ERP con metadata para UI
export const TIPOS_ERP = [
  { value: TIPO_ARCHIVO_ERP.LIBRO_REMUNERACIONES, label: 'Libro de Remuneraciones', descripcion: 'Archivo de libro de remuneraciones del ERP' },
  { value: TIPO_ARCHIVO_ERP.MOVIMIENTOS_MES, label: 'Movimientos del Mes', descripcion: 'Archivo de movimientos mensuales del ERP' },
]

// Tipos de archivos del Analista con metadata para UI
export const TIPOS_ANALISTA = [
  { value: TIPO_ARCHIVO_ANALISTA.NOVEDADES, label: 'Novedades', descripcion: 'Novedades proporcionadas por el cliente' },
  { value: TIPO_ARCHIVO_ANALISTA.ASISTENCIAS, label: 'Asistencias', descripcion: 'Registro de asistencias del personal' },
  { value: TIPO_ARCHIVO_ANALISTA.FINIQUITOS, label: 'Finiquitos', descripcion: 'Documentos de finiquitos del período' },
  { value: TIPO_ARCHIVO_ANALISTA.INGRESOS, label: 'Ingresos', descripcion: 'Nuevos ingresos del período' },
]

/**
 * Verifica si algún archivo está en estado de procesamiento.
 * Usa las constantes centralizadas para determinar qué estados requieren polling.
 * 
 * @param {Object} archivos - Objeto con archivos indexados por tipo
 * @returns {boolean} - true si hay al menos un archivo procesando
 */
const tieneArchivosProcesando = (archivos) => {
  if (!archivos) return false
  return Object.values(archivos).some(
    archivo => archivo && ESTADOS_ARCHIVO_PROCESANDO.includes(archivo.estado)
  )
}

/**
 * Hook para obtener archivos ERP de un cierre.
 * 
 * Incluye polling automático cada POLLING_INTERVALS.ARCHIVO_PROCESANDO ms
 * mientras haya archivos en estado de procesamiento.
 * 
 * @param {string|number} cierreId - ID del cierre
 * @returns {UseQueryResult} - Resultado de React Query con archivos ERP
 */
export const useArchivosERP = (cierreId) => {
  return useQuery({
    queryKey: ['archivos-erp', cierreId],
    queryFn: async () => {
      const { data } = await api.get(`/v1/validador/archivos-erp/por_cierre/`, {
        params: { cierre_id: cierreId }
      })
      return data
    },
    enabled: !!cierreId,
    staleTime: 0,
    refetchOnMount: 'always',
    refetchInterval: (query) => {
      const data = query.state.data
      return tieneArchivosProcesando(data) ? POLLING_INTERVALS.ARCHIVO_PROCESANDO : false
    },
  })
}

/**
 * Hook para obtener archivos del Analista de un cierre.
 * 
 * Incluye polling automático cada POLLING_INTERVALS.ARCHIVO_PROCESANDO ms
 * mientras haya archivos en estado de procesamiento.
 * 
 * @param {string|number} cierreId - ID del cierre
 * @returns {UseQueryResult} - Resultado de React Query con archivos del analista
 */
export const useArchivosAnalista = (cierreId) => {
  return useQuery({
    queryKey: ['archivos-analista', cierreId],
    queryFn: async () => {
      const { data } = await api.get(`/v1/validador/archivos-analista/por_cierre/`, {
        params: { cierre_id: cierreId }
      })
      return data
    },
    enabled: !!cierreId,
    staleTime: 0,
    refetchOnMount: 'always',
    refetchInterval: (query) => {
      const data = query.state.data
      return tieneArchivosProcesando(data) ? POLLING_INTERVALS.ARCHIVO_PROCESANDO : false
    },
  })
}

/**
 * Hook para subir archivo ERP
 */
export const useUploadArchivoERP = () => {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: async ({ cierreId, tipo, archivo, onProgress }) => {
      const formData = new FormData()
      formData.append('cierre', cierreId)
      formData.append('tipo', tipo)
      formData.append('archivo', archivo)
      
      const { data } = await api.post('/v1/validador/archivos-erp/', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        onUploadProgress: (progressEvent) => {
          if (onProgress) {
            const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total)
            onProgress(progress)
          }
        },
      })
      return data
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['archivos-erp', variables.cierreId] })
      queryClient.invalidateQueries({ queryKey: ['cierre', variables.cierreId] })
    },
  })
}

/**
 * Hook para subir archivo del Analista
 */
export const useUploadArchivoAnalista = () => {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: async ({ cierreId, tipo, archivo, onProgress }) => {
      const formData = new FormData()
      formData.append('cierre', cierreId)
      formData.append('tipo', tipo)
      formData.append('archivo', archivo)
      
      const { data } = await api.post('/v1/validador/archivos-analista/', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        onUploadProgress: (progressEvent) => {
          if (onProgress) {
            const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total)
            onProgress(progress)
          }
        },
      })
      return data
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['archivos-analista', variables.cierreId] })
      queryClient.invalidateQueries({ queryKey: ['cierre', variables.cierreId] })
    },
  })
}

/**
 * Hook para eliminar archivo ERP
 */
export const useDeleteArchivoERP = () => {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: async ({ archivoId, cierreId }) => {
      await api.delete(`/v1/validador/archivos-erp/${archivoId}/`)
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['archivos-erp', variables.cierreId] })
    },
  })
}

/**
 * Hook para eliminar archivo del Analista
 */
export const useDeleteArchivoAnalista = () => {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: async ({ archivoId, cierreId }) => {
      await api.delete(`/v1/validador/archivos-analista/${archivoId}/`)
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['archivos-analista', variables.cierreId] })
    },
  })
}

/**
 * Hook para obtener el progreso de procesamiento del Libro de Remuneraciones.
 * 
 * Este hook hace polling al endpoint específico de progreso que usa cache de Celery,
 * proporcionando información detallada: porcentaje, empleados procesados, mensaje.
 * 
 * El polling se activa automáticamente cuando el estado es 'procesando' y se detiene
 * cuando cambia a 'completado' o 'error'.
 * 
 * @param {string|number} archivoId - ID del archivo ERP (libro_remuneraciones)
 * @param {Object} options - Opciones de configuración
 * @param {boolean} options.enabled - Si el polling está activo (default: true)
 * @returns {UseQueryResult} - Resultado con { estado, progreso, empleados_procesados, mensaje }
 */
export const useProgresoLibro = (archivoId, { enabled = true } = {}) => {
  const queryClient = useQueryClient()
  
  return useQuery({
    queryKey: ['progreso-libro', archivoId],
    queryFn: async () => {
      const { data } = await api.get(`/v1/validador/libro/${archivoId}/progreso/`)
      return data
    },
    enabled: !!archivoId && enabled,
    staleTime: 0,
    refetchInterval: (query) => {
      const data = query.state.data
      // Solo hacer polling mientras está procesando
      if (data?.estado === 'procesando') {
        return POLLING_INTERVALS.TAREA_CELERY
      }
      // Cuando termina, invalidar los archivos para refrescar el estado
      if (data?.estado === 'completado' || data?.estado === 'error') {
        // Invalidar queries de archivos para que reflejen el nuevo estado
        queryClient.invalidateQueries({ queryKey: ['archivos-erp'] })
      }
      return false
    },
  })
}
