/**
 * Modal de Mapeo de Conceptos de Novedades
 * 
 * Muestra los headers extraídos del archivo de novedades del cliente
 * y permite mapearlos a los conceptos del libro de remuneraciones (ConceptoLibro).
 * 
 * Este mapeo es necesario para poder comparar los datos del ERP (libro)
 * con los datos del cliente (novedades).
 * 
 * Los ConceptoNovedades son por cliente+ERP (no por archivo), por lo que
 * los mapeos se reutilizan entre cierres del mismo cliente.
 */
import { useState, useEffect, useMemo } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { 
  Loader2, 
  PlayCircle,
  AlertCircle,
  Check,
  FileSpreadsheet,
  Link2,
  Link2Off,
  ArrowRight
} from 'lucide-react'
import Modal from '../../../components/ui/Modal'
import Button from '../../../components/ui/Button'
import api from '../../../api/axios'
import { cn } from '../../../utils/cn'
import { 
  ESTADO_ARCHIVO_NOVEDADES, 
  puedeMapearNovedades,
  puedeProcesarNovedades
} from '../../../constants'

/**
 * Hook para obtener los conceptos de novedades sin mapear para un cliente
 */
const useConceptosNovedadesSinMapear = (clienteId, erpId, options = {}) => {
  return useQuery({
    queryKey: ['conceptos-novedades-sin-mapear', clienteId, erpId],
    queryFn: async () => {
      const { data } = await api.get('/v1/validador/mapeos/sin_mapear/', {
        params: { 
          cliente_id: clienteId,
          erp_id: erpId
        }
      })
      return data
    },
    enabled: !!clienteId,
    ...options
  })
}

/**
 * Hook para obtener los conceptos del libro disponibles para mapeo
 */
const useConceptosLibro = (clienteId, erpId, options = {}) => {
  return useQuery({
    queryKey: ['conceptos-libro-mapeo', clienteId, erpId],
    queryFn: async () => {
      const { data } = await api.get('/v1/validador/mapeos/conceptos_libro/', {
        params: { 
          cliente_id: clienteId,
          erp_id: erpId
        }
      })
      return data
    },
    enabled: !!clienteId,
    ...options
  })
}

/**
 * Modal para el mapeo de conceptos de novedades a conceptos del libro
 * 
 * @param {Object} props
 * @param {boolean} props.isOpen - Si el modal está abierto
 * @param {function} props.onClose - Callback al cerrar el modal
 * @param {Object} props.archivo - Objeto del archivo de novedades (ArchivoAnalista)
 * @param {string|number} props.cierreId - ID del cierre
 * @param {Object} props.cliente - Objeto del cliente con ID
 * @param {string|number} props.erpId - ID del ERP
 * @param {function} props.onMapeoComplete - Callback cuando se completa el mapeo
 */
const MapeoNovedadesModal = ({ 
  isOpen, 
  onClose, 
  archivo, 
  cierreId,
  cliente,
  erpId,
  onMapeoComplete
}) => {
  const queryClient = useQueryClient()
  const [mapeos, setMapeos] = useState({}) // { conceptoNovedadesId: conceptoLibroId }
  
  // Queries para datos - usando cliente+ERP (no archivo)
  const { data: conceptosSinMapear, isLoading: loadingConceptos } = useConceptosNovedadesSinMapear(
    cliente?.id,
    erpId,
    { enabled: isOpen && !!cliente?.id }
  )
  
  const { data: conceptosLibro, isLoading: loadingLibro } = useConceptosLibro(
    cliente?.id,
    erpId,
    { enabled: isOpen && !!cliente?.id }
  )
  
  // Mutation para guardar mapeos
  const guardarMapeosMutation = useMutation({
    mutationFn: async (mapeosData) => {
      const { data } = await api.post('/v1/validador/mapeos/mapear_batch/', mapeosData)
      return data
    },
    onSuccess: (data) => {
      // Invalidar queries
      queryClient.invalidateQueries(['conceptos-novedades-sin-mapear', cliente?.id])
      queryClient.invalidateQueries(['archivos-analista', cierreId])
      queryClient.invalidateQueries(['cierre', cierreId])
      
      if (onMapeoComplete) {
        onMapeoComplete(data)
      }
      
      // Cerrar modal si todos están mapeados
      if (data.sin_mapear === 0) {
        onClose()
      }
    }
  })
  
  // Reset mapeos cuando se abre el modal
  useEffect(() => {
    if (isOpen) {
      setMapeos({})
    }
  }, [isOpen])
  
  // Handler para asignar un mapeo
  const handleAsignarMapeo = (conceptoNovedadesId, conceptoLibroId) => {
    setMapeos(prev => ({
      ...prev,
      [conceptoNovedadesId]: conceptoLibroId
    }))
  }
  
  // Handler para quitar un mapeo
  const handleQuitarMapeo = (conceptoNovedadesId) => {
    setMapeos(prev => {
      const nuevo = { ...prev }
      delete nuevo[conceptoNovedadesId]
      return nuevo
    })
  }
  
  // Handler para guardar
  const handleGuardar = () => {
    // Transformar mapeos a formato esperado por el backend
    const mapeosArray = Object.entries(mapeos).map(([conceptoNovedadesId, conceptoLibroId]) => ({
      concepto_novedades_id: parseInt(conceptoNovedadesId),
      concepto_libro_id: conceptoLibroId
    }))
    
    guardarMapeosMutation.mutate({
      mapeos: mapeosArray
    })
  }
  
  if (!cliente) return null
  
  const isLoading = loadingConceptos || loadingLibro
  const conceptosSinMapearList = conceptosSinMapear?.items || []
  const conceptosLibroList = conceptosLibro?.conceptos || []
  const hayMapeosNuevos = Object.keys(mapeos).length > 0
  
  // Agrupar conceptos del libro por categoría para facilitar selección
  const conceptosPorCategoria = useMemo(() => {
    const grupos = {}
    conceptosLibroList.forEach(concepto => {
      const cat = concepto.categoria_display || 'Sin clasificar'
      if (!grupos[cat]) grupos[cat] = []
      grupos[cat].push(concepto)
    })
    return grupos
  }, [conceptosLibroList])

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Mapeo de Conceptos de Novedades"
      description="Asocia cada concepto del archivo de novedades con su equivalente en el libro de remuneraciones"
      size="xl"
    >
      <div className="py-4">
        {/* Loading state */}
        {isLoading && (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="h-8 w-8 text-primary-500 animate-spin" />
            <span className="ml-3 text-gray-400">Cargando datos...</span>
          </div>
        )}
        
        {/* Sin conceptos pendientes */}
        {!isLoading && conceptosSinMapearList.length === 0 && (
          <div className="flex flex-col items-center justify-center py-12">
            <Check className="h-12 w-12 text-green-400 mb-4" />
            <p className="text-gray-300 text-lg">Todos los conceptos están mapeados</p>
            <p className="text-gray-500 text-sm mt-2">El archivo de novedades está listo para procesar</p>
          </div>
        )}
        
        {/* Lista de conceptos para mapear */}
        {!isLoading && conceptosSinMapearList.length > 0 && (
          <div className="space-y-4">
            {/* Info */}
            <div className="bg-blue-900/20 border border-blue-500/30 rounded-lg p-3">
              <p className="text-sm text-blue-300">
                <strong>{conceptosSinMapearList.length}</strong> conceptos pendientes de mapeo.
                Selecciona el concepto del libro que corresponda a cada uno.
              </p>
            </div>
            
            {/* Tabla de mapeo */}
            <div className="max-h-[400px] overflow-y-auto">
              <table className="w-full">
                <thead className="bg-dark-700 sticky top-0">
                  <tr>
                    <th className="text-left text-sm font-medium text-gray-400 px-4 py-2">
                      Concepto en Novedades
                    </th>
                    <th className="text-center text-sm font-medium text-gray-400 px-4 py-2 w-12">
                      <ArrowRight className="h-4 w-4 mx-auto" />
                    </th>
                    <th className="text-left text-sm font-medium text-gray-400 px-4 py-2">
                      Concepto del Libro
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-700/50">
                  {conceptosSinMapearList.map(concepto => (
                    <tr key={concepto.id} className="hover:bg-dark-700/50">
                      <td className="px-4 py-3">
                        <span className="text-gray-200">{concepto.header_original}</span>
                        <span className="text-xs text-gray-500 ml-2">(col. {concepto.orden})</span>
                      </td>
                      <td className="px-4 py-3 text-center">
                        {mapeos[concepto.id] ? (
                          <Link2 className="h-4 w-4 text-green-400 mx-auto" />
                        ) : (
                          <Link2Off className="h-4 w-4 text-gray-600 mx-auto" />
                        )}
                      </td>
                      <td className="px-4 py-3">
                        <select
                          value={mapeos[concepto.id] || ''}
                          onChange={(e) => {
                            const val = e.target.value
                            if (val) {
                              handleAsignarMapeo(concepto.id, parseInt(val))
                            } else {
                              handleQuitarMapeo(concepto.id)
                            }
                          }}
                          className={cn(
                            "w-full bg-dark-600 border rounded-md px-3 py-2 text-sm",
                            "focus:outline-none focus:ring-2 focus:ring-primary-500",
                            mapeos[concepto.id] 
                              ? "border-green-500/50 text-gray-200" 
                              : "border-gray-600 text-gray-400"
                          )}
                        >
                          <option value="">-- Seleccionar concepto --</option>
                          {Object.entries(conceptosPorCategoria).map(([categoria, conceptosLibro]) => (
                            <optgroup key={categoria} label={categoria}>
                              {conceptosLibro.map(cl => (
                                <option key={cl.id} value={cl.id}>
                                  {cl.header_original}
                                </option>
                              ))}
                            </optgroup>
                          ))}
                        </select>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            
            {/* Resumen y acciones */}
            <div className="flex items-center justify-between pt-4 border-t border-gray-700">
              <div className="text-sm text-gray-400">
                {Object.keys(mapeos).length > 0 ? (
                  <span className="text-green-400">
                    {Object.keys(mapeos).length} de {conceptosSinMapearList.length} conceptos seleccionados
                  </span>
                ) : (
                  <span>Selecciona al menos un mapeo para guardar</span>
                )}
              </div>
              
              <div className="flex gap-3">
                <Button
                  variant="ghost"
                  onClick={onClose}
                >
                  Cancelar
                </Button>
                <Button
                  variant="primary"
                  onClick={handleGuardar}
                  disabled={!hayMapeosNuevos || guardarMapeosMutation.isPending}
                  leftIcon={guardarMapeosMutation.isPending ? Loader2 : Check}
                >
                  {guardarMapeosMutation.isPending ? 'Guardando...' : 'Guardar Mapeos'}
                </Button>
              </div>
            </div>
          </div>
        )}
        
        {/* Error state */}
        {guardarMapeosMutation.isError && (
          <div className="mt-4 bg-red-900/20 border border-red-500/30 rounded-lg p-3">
            <p className="text-sm text-red-400 flex items-center gap-2">
              <AlertCircle className="h-4 w-4" />
              Error al guardar mapeos: {guardarMapeosMutation.error?.message || 'Error desconocido'}
            </p>
          </div>
        )}
      </div>
    </Modal>
  )
}

export default MapeoNovedadesModal
