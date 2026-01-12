/**
 * Modal de Clasificación del Libro de Remuneraciones
 * 
 * Muestra el componente ClasificacionLibro dentro de un modal
 * para clasificar los conceptos cuando el libro está en estado pendiente_clasificacion
 */
import { useState, useEffect } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { 
  Loader2, 
  PlayCircle,
  AlertCircle 
} from 'lucide-react'
import Modal from '../../../components/ui/Modal'
import Button from '../../../components/ui/Button'
import ClasificacionLibroV2 from './ClasificacionLibroV2'
import api from '../../../api/axios'
import { 
  ESTADO_ARCHIVO_LIBRO, 
  puedeClasificarLibro,
  puedeProcesarLibro
} from '../../../constants'

/**
 * Modal para la clasificación de conceptos del Libro de Remuneraciones
 * 
 * @param {Object} props
 * @param {boolean} props.isOpen - Si el modal está abierto
 * @param {function} props.onClose - Callback al cerrar el modal
 * @param {Object} props.archivo - Objeto del archivo ERP (libro de remuneraciones)
 * @param {string|number} props.cierreId - ID del cierre
 * @param {function} props.onClasificacionComplete - Callback cuando se completa la clasificación
 * @param {function} props.onProcesoIniciado - Callback cuando se inicia el procesamiento
 */
const ClasificacionLibroModal = ({ 
  isOpen, 
  onClose, 
  archivo, 
  cierreId,
  onClasificacionComplete,
  onProcesoIniciado
}) => {
  const queryClient = useQueryClient()
  const [listoParaProcesar, setListoParaProcesar] = useState(false)

  // Actualizar estado cuando cambia el archivo
  useEffect(() => {
    if (archivo?.estado === ESTADO_ARCHIVO_LIBRO.LISTO) {
      setListoParaProcesar(true)
    }
  }, [archivo?.estado])

  // Mutation para iniciar procesamiento del libro
  const procesarMutation = useMutation({
    mutationFn: async () => {
      const { data } = await api.post(`/v1/validador/libro/${archivo.id}/procesar/`)
      return data
    },
    onSuccess: (data) => {
      // Invalidar queries relacionadas
      queryClient.invalidateQueries(['archivos-erp', cierreId])
      queryClient.invalidateQueries(['cierre', cierreId])
      
      // Notificar al padre que se inició el proceso
      if (onProcesoIniciado) {
        onProcesoIniciado(data)
      }
      
      // Cerrar modal
      onClose()
    },
  })

  // Callback cuando se completa la clasificación
  const handleClasificacionComplete = () => {
    setListoParaProcesar(true)
    
    // Invalidar queries para refrescar estado
    queryClient.invalidateQueries(['archivos-erp', cierreId])
    queryClient.invalidateQueries(['libro-headers', archivo?.id])
    queryClient.invalidateQueries(['libro-pendientes', archivo?.id])
    
    if (onClasificacionComplete) {
      onClasificacionComplete()
    }
  }

  // Handler para iniciar procesamiento
  const handleProcesar = () => {
    procesarMutation.mutate()
  }

  if (!archivo) return null

  const puedeClasificar = puedeClasificarLibro(archivo.estado)
  const puedeProcesar = puedeProcesarLibro(archivo.estado) || listoParaProcesar

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Clasificación de Conceptos del Libro"
      description="Selecciona múltiples conceptos o arrástralos a las categorías para clasificarlos"
      size="full"
    >
      <div className="max-h-[75vh] overflow-y-auto -mx-6 px-6">
        {puedeClasificar || listoParaProcesar ? (
          <ClasificacionLibroV2 
            archivoId={archivo.id}
            clienteId={archivo.cliente}
            cierreId={cierreId}
            onComplete={handleClasificacionComplete}
          />
        ) : (
          <div className="py-8 text-center">
            <AlertCircle className="h-12 w-12 mx-auto mb-3 text-warning-400" />
            <p className="text-secondary-300">
              El archivo no está en un estado que permita clasificación.
            </p>
            <p className="text-sm text-secondary-500 mt-2">
              Estado actual: <code className="bg-secondary-800 px-2 py-0.5 rounded">{archivo.estado}</code>
            </p>
          </div>
        )}
      </div>

      {/* Footer con acciones */}
      <Modal.Footer>
        <Button 
          variant="secondary" 
          onClick={onClose}
        >
          Cerrar
        </Button>
        
        {puedeProcesar && (
          <Button
            variant="primary"
            onClick={handleProcesar}
            disabled={procesarMutation.isPending}
            className="flex items-center gap-2"
          >
            {procesarMutation.isPending ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                Iniciando procesamiento...
              </>
            ) : (
              <>
                <PlayCircle className="h-4 w-4" />
                Procesar Libro
              </>
            )}
          </Button>
        )}
      </Modal.Footer>
    </Modal>
  )
}

export default ClasificacionLibroModal
