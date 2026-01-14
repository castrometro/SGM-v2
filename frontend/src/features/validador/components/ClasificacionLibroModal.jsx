/**
 * Modal de Clasificación del Libro de Remuneraciones
 * 
 * Muestra el componente ClasificacionLibro dentro de un modal
 * para clasificar los conceptos cuando el libro está en estado pendiente_clasificacion.
 * 
 * También muestra el progreso del procesamiento con barra de porcentaje
 * cuando el usuario presiona "Procesar Libro".
 */
import { useState, useEffect } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { 
  Loader2, 
  PlayCircle,
  AlertCircle,
  Check,
  FileSpreadsheet
} from 'lucide-react'
import Modal from '../../../components/ui/Modal'
import Button from '../../../components/ui/Button'
import ClasificacionLibroV2 from './ClasificacionLibroV2'
import api from '../../../api/axios'
import { useProgresoLibro } from '../hooks/useArchivos'
import { cn } from '../../../utils/cn'
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
  const [todosClasificados, setTodosClasificados] = useState(false)
  const [mostrarProcesamiento, setMostrarProcesamiento] = useState(false)

  // Hook para polling del progreso de procesamiento
  const { data: progreso } = useProgresoLibro(archivo?.id, {
    enabled: mostrarProcesamiento && !!archivo?.id
  })

  // Actualizar estado cuando cambia el archivo
  useEffect(() => {
    if (archivo?.estado === ESTADO_ARCHIVO_LIBRO.LISTO) {
      setListoParaProcesar(true)
      setTodosClasificados(true)
    }
  }, [archivo?.estado])
  
  // Reset cuando se abre el modal
  useEffect(() => {
    if (isOpen) {
      // SIEMPRE resetear vista de procesamiento al abrir el modal
      setMostrarProcesamiento(false)
      
      // Solo resetear clasificación si el archivo no está listo
      if (archivo?.estado !== ESTADO_ARCHIVO_LIBRO.LISTO) {
        setListoParaProcesar(false)
        setTodosClasificados(false)
      }
    }
  }, [isOpen, archivo?.estado])

  // Cuando el procesamiento termina (completado o error), cerrar modal automáticamente
  useEffect(() => {
    if (mostrarProcesamiento && progreso) {
      if (progreso.estado === 'completado' || progreso.estado === 'error') {
        // Dar tiempo para que el usuario vea el resultado final
        const timer = setTimeout(() => {
          // Invalidar queries para refrescar estado
          queryClient.invalidateQueries(['archivos-erp', cierreId])
          queryClient.invalidateQueries(['cierre', cierreId])
          
          if (onProcesoIniciado) {
            onProcesoIniciado(progreso)
          }
          
          // Cerrar modal
          onClose()
        }, progreso.estado === 'completado' ? 1500 : 3000) // Más tiempo si hay error
        
        return () => clearTimeout(timer)
      }
    }
  }, [mostrarProcesamiento, progreso, queryClient, cierreId, onProcesoIniciado, onClose])

  // Mutation para iniciar procesamiento del libro
  const procesarMutation = useMutation({
    mutationFn: async () => {
      const { data } = await api.post(`/v1/validador/libro/${archivo.id}/procesar/`)
      return data
    },
    onSuccess: (data) => {
      // Cambiar a vista de procesamiento (NO cerrar modal)
      setMostrarProcesamiento(true)
      
      // Invalidar queries relacionadas
      queryClient.invalidateQueries(['archivos-erp', cierreId])
      queryClient.invalidateQueries(['cierre', cierreId])
    },
  })

  // Callback cuando se completa la clasificación
  const handleClasificacionComplete = () => {
    setListoParaProcesar(true)
    setTodosClasificados(true)
    
    // Invalidar queries para refrescar estado
    queryClient.invalidateQueries(['archivos-erp', cierreId])
    queryClient.invalidateQueries(['libro-headers', archivo?.id])
    queryClient.invalidateQueries(['libro-pendientes', archivo?.id])
    
    if (onClasificacionComplete) {
      onClasificacionComplete()
    }
  }
  
  // Callback cuando cambia el estado de "todos clasificados"
  const handleAllClassifiedChange = (allClassified) => {
    setTodosClasificados(allClassified)
    if (allClassified) {
      setListoParaProcesar(true)
    }
  }

  // Handler para iniciar procesamiento
  const handleProcesar = () => {
    procesarMutation.mutate()
  }

  if (!archivo) return null

  const puedeClasificar = puedeClasificarLibro(archivo.estado)
  // Solo puede procesar si todos los conceptos están clasificados (sin cambios pendientes)
  const puedeProcesar = (puedeProcesarLibro(archivo.estado) || listoParaProcesar) && todosClasificados

  // Calcular valores de progreso para la vista de procesamiento
  const porcentaje = progreso?.progreso || 0
  const empleadosProcesados = progreso?.empleados_procesados || 0
  const mensajeProceso = progreso?.mensaje || 'Iniciando procesamiento...'
  const estadoProceso = progreso?.estado || 'procesando'

  // Colores según estado del procesamiento
  const barColor = estadoProceso === 'error' 
    ? 'bg-red-500' 
    : estadoProceso === 'completado'
      ? 'bg-green-500'
      : 'bg-gradient-to-r from-primary-500 to-accent-500'

  // Título dinámico del modal
  const modalTitle = mostrarProcesamiento 
    ? 'Procesando Libro de Remuneraciones'
    : 'Clasificación de Conceptos del Libro'
  
  const modalDescription = mostrarProcesamiento
    ? 'Extrayendo y procesando los datos de cada empleado'
    : 'Selecciona múltiples conceptos o arrástralos a las categorías para clasificarlos'

  return (
    <Modal
      isOpen={isOpen}
      onClose={mostrarProcesamiento && estadoProceso === 'procesando' ? undefined : onClose}
      title={modalTitle}
      description={modalDescription}
      size={mostrarProcesamiento ? 'md' : 'full'}
    >
      {/* Vista de Procesamiento con barra de progreso */}
      {mostrarProcesamiento ? (
        <div className="py-8 px-4">
          {/* Icono central */}
          <div className="flex justify-center mb-6">
            <div className={cn(
              "p-4 rounded-full",
              estadoProceso === 'completado' ? 'bg-green-500/20' :
              estadoProceso === 'error' ? 'bg-red-500/20' : 'bg-primary-500/20'
            )}>
              {estadoProceso === 'completado' ? (
                <Check className="h-12 w-12 text-green-400" />
              ) : estadoProceso === 'error' ? (
                <AlertCircle className="h-12 w-12 text-red-400" />
              ) : (
                <FileSpreadsheet className="h-12 w-12 text-primary-400 animate-pulse" />
              )}
            </div>
          </div>

          {/* Barra de progreso */}
          <div className="space-y-3 max-w-md mx-auto">
            <div className="w-full bg-secondary-700 rounded-full h-4 overflow-hidden">
              <div 
                className={cn(
                  "h-full transition-all duration-500 ease-out",
                  barColor,
                  estadoProceso === 'procesando' && "animate-pulse"
                )}
                style={{ width: `${Math.min(porcentaje, 100)}%` }}
              />
            </div>
            
            {/* Porcentaje y mensaje */}
            <div className="text-center space-y-1">
              <p className={cn(
                "text-2xl font-bold",
                estadoProceso === 'completado' ? 'text-green-400' :
                estadoProceso === 'error' ? 'text-red-400' : 'text-primary-400'
              )}>
                {porcentaje}%
              </p>
              <p className="text-secondary-400 text-sm">
                {mensajeProceso}
              </p>
              {empleadosProcesados > 0 && estadoProceso !== 'error' && (
                <p className="text-secondary-500 text-xs">
                  {empleadosProcesados} empleados procesados
                </p>
              )}
            </div>

            {/* Mensaje de cierre automático */}
            {estadoProceso === 'completado' && (
              <p className="text-center text-xs text-secondary-500 mt-4">
                Cerrando automáticamente...
              </p>
            )}
            {estadoProceso === 'error' && (
              <div className="mt-4 text-center">
                <Button variant="secondary" onClick={onClose} size="sm">
                  Cerrar
                </Button>
              </div>
            )}
          </div>
        </div>
      ) : (
        /* Vista de Clasificación */
        <>
          <div className="max-h-[75vh] overflow-y-auto -mx-6 px-6">
            {puedeClasificar || listoParaProcesar ? (
              <ClasificacionLibroV2 
                archivoId={archivo.id}
                clienteId={archivo.cliente}
                cierreId={cierreId}
                onComplete={handleClasificacionComplete}
                onAllClassifiedChange={handleAllClassifiedChange}
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
        </>
      )}
    </Modal>
  )
}

export default ClasificacionLibroModal
