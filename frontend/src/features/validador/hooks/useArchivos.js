/**
 * Hooks para gestión de archivos del validador (ERP y Analista)
 */
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import api from '../../../api/axios'

// Tipos de archivos ERP
export const TIPOS_ERP = [
  { value: 'libro_remuneraciones', label: 'Libro de Remuneraciones', descripcion: 'Archivo de libro de remuneraciones del ERP' },
  { value: 'movimientos_mes', label: 'Movimientos del Mes', descripcion: 'Archivo de movimientos mensuales del ERP' },
]

// Tipos de archivos del Analista
export const TIPOS_ANALISTA = [
  { value: 'novedades', label: 'Novedades', descripcion: 'Novedades proporcionadas por el cliente' },
  { value: 'asistencias', label: 'Asistencias', descripcion: 'Registro de asistencias del personal' },
  { value: 'finiquitos', label: 'Finiquitos', descripcion: 'Documentos de finiquitos del período' },
  { value: 'ingresos', label: 'Ingresos', descripcion: 'Nuevos ingresos del período' },
]

/**
 * Hook para obtener archivos ERP de un cierre
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
  })
}

/**
 * Hook para obtener archivos del Analista de un cierre
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
