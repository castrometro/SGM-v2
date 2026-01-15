/**
 * Componente de Carga de Archivo de Novedades del Cliente
 * 
 * Permite cargar el archivo de novedades y luego abrir el modal de mapeo
 * para asociar los items del archivo con los conceptos del libro.
 * 
 * Flujo:
 * 1. Usuario sube archivo de novedades (Excel)
 * 2. Backend extrae headers automáticamente (tarea Celery)
 * 3. Usuario abre modal de mapeo y asocia items → conceptos del libro
 * 4. Cuando todos los items requeridos están mapeados, el archivo queda "listo"
 */
import { useState, useCallback, useRef } from 'react'
import { useQueryClient, useQuery } from '@tanstack/react-query'
import { 
  Upload, 
  FileSpreadsheet, 
  X, 
  Check, 
  AlertCircle, 
  Loader2, 
  Trash2,
  Tag,
  Link2,
  ChevronRight,
  FileText,
  Clock
} from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '../../../components/ui'
import Badge from '../../../components/ui/Badge'
import Button from '../../../components/ui/Button'
import { cn } from '../../../utils/cn'
import {
  useArchivosAnalista,
  useUploadArchivoAnalista,
  useDeleteArchivoAnalista,
} from '../hooks/useArchivos'
import MapeoNovedadesModal from './MapeoNovedadesModal'
import api from '../../../api/axios'
import { 
  ESTADO_ARCHIVO_NOVEDADES,
  novedadesRequiereAccion,
  puedeMapearNovedades,
  puedeProcesarNovedades,
  POLLING_INTERVALS
} from '../../../constants'

// Constantes para estados de archivo de novedades
const ESTADO_STYLES = {
  subido: { color: 'info', icon: FileSpreadsheet, label: 'Subido' },
  extrayendo_headers: { color: 'warning', icon: Loader2, label: 'Extrayendo Headers', animate: true },
  pendiente_mapeo: { color: 'warning', icon: Tag, label: 'Requiere Mapeo' },
  listo: { color: 'info', icon: Check, label: 'Listo para Procesar' },
  procesando: { color: 'warning', icon: Loader2, label: 'Procesando', animate: true },
  procesado: { color: 'success', icon: Check, label: 'Procesado' },
  error: { color: 'danger', icon: AlertCircle, label: 'Error' },
}

// Formatos permitidos
const FORMATOS_PERMITIDOS = ['.xlsx', '.xls']

/**
 * Hook para obtener el conteo de items sin mapear de un archivo
 */
const useItemsSinMapearCount = (archivoId, options = {}) => {
  return useQuery({
    queryKey: ['novedades-sin-mapear-count', archivoId],
    queryFn: async () => {
      const { data } = await api.get('/v1/validador/mapeos/sin_mapear/', {
        params: { archivo_id: archivoId }
      })
      return data.items?.length || 0
    },
    enabled: !!archivoId,
    ...options
  })
}

/**
 * Componente para carga de archivos de novedades
 * 
 * @param {Object} props
 * @param {string|number} props.cierreId - ID del cierre
 * @param {Object} props.cierre - Datos del cierre (incluye cliente_erp)
 */
const CargaNovedades = ({ cierreId, cierre }) => {
  const queryClient = useQueryClient()
  const fileInputRef = useRef(null)
  const [isDragging, setIsDragging] = useState(false)
  const [modalMapeoAbierto, setModalMapeoAbierto] = useState(false)
  const [archivoSeleccionado, setArchivoSeleccionado] = useState(null)
  
  // Hook para archivos del analista
  const { 
    data: archivosAnalista, 
    isLoading: loadingArchivos,
    refetch: refetchArchivos
  } = useArchivosAnalista(cierreId, {
    // Polling si hay archivos en procesamiento
    refetchInterval: (data) => {
      // data es un objeto { novedades, asistencias, finiquitos, ingresos }
      const archivo = data?.novedades
      const procesando = archivo && (
        archivo.estado === ESTADO_ARCHIVO_NOVEDADES.EXTRAYENDO_HEADERS ||
        archivo.estado === ESTADO_ARCHIVO_NOVEDADES.PROCESANDO
      )
      return procesando ? POLLING_INTERVALS.ARCHIVO_PROCESANDO : false
    }
  })
  
  // archivosAnalista es un objeto con claves: { novedades, asistencias, finiquitos, ingresos }
  // Accedemos directamente al archivo de novedades
  const archivoNovedades = archivosAnalista?.novedades || null
  
  // Conteo de items sin mapear
  const { data: sinMapearCount } = useItemsSinMapearCount(archivoNovedades?.id, {
    enabled: !!archivoNovedades && puedeMapearNovedades(archivoNovedades.estado)
  })
  
  // Mutations
  const uploadMutation = useUploadArchivoAnalista(cierreId)
  const deleteMutation = useDeleteArchivoAnalista(cierreId)
  
  // Handlers de drag & drop
  const handleDragEnter = useCallback((e) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragging(true)
  }, [])
  
  const handleDragLeave = useCallback((e) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragging(false)
  }, [])
  
  const handleDragOver = useCallback((e) => {
    e.preventDefault()
    e.stopPropagation()
  }, [])
  
  const handleDrop = useCallback((e) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragging(false)
    
    const files = Array.from(e.dataTransfer.files)
    const file = files[0]
    
    if (file) {
      handleUpload(file)
    }
  }, [])
  
  const handleFileSelect = (e) => {
    const file = e.target.files[0]
    if (file) {
      handleUpload(file)
    }
    // Reset input
    e.target.value = ''
  }
  
  const handleUpload = async (file) => {
    // Validar extensión
    const ext = '.' + file.name.split('.').pop().toLowerCase()
    if (!FORMATOS_PERMITIDOS.includes(ext)) {
      alert(`Formato no permitido. Use: ${FORMATOS_PERMITIDOS.join(', ')}`)
      return
    }
    
    try {
      await uploadMutation.mutateAsync({
        cierreId,
        tipo: 'novedades',
        archivo: file
      })
      refetchArchivos()
    } catch (error) {
      console.error('Error al subir archivo:', error)
    }
  }
  
  const handleDelete = async (archivoId) => {
    if (!confirm('¿Está seguro de eliminar este archivo?')) return
    
    try {
      await deleteMutation.mutateAsync(archivoId)
      refetchArchivos()
    } catch (error) {
      console.error('Error al eliminar archivo:', error)
    }
  }
  
  const handleAbrirMapeo = (archivo) => {
    setArchivoSeleccionado(archivo)
    setModalMapeoAbierto(true)
  }
  
  const handleMapeoComplete = () => {
    // Refrescar datos
    refetchArchivos()
    queryClient.invalidateQueries(['novedades-sin-mapear-count', archivoSeleccionado?.id])
    queryClient.invalidateQueries(['cierre', cierreId])
  }
  
  // Render del estado del archivo
  const renderEstadoArchivo = (archivo) => {
    // Debug: ver qué estado viene
    console.log('Estado archivo novedades:', archivo.estado, 'Estilos disponibles:', Object.keys(ESTADO_STYLES))
    
    const estilos = ESTADO_STYLES[archivo.estado] || ESTADO_STYLES.subido
    const Icon = estilos.icon
    
    return (
      <Badge 
        variant={estilos.color} 
        className={cn(
          "gap-1.5 whitespace-nowrap px-2.5 py-1",
          estilos.animate && "animate-pulse"
        )}
      >
        <Icon className={cn("h-3 w-3 flex-shrink-0", estilos.animate && "animate-spin")} />
        <span>{estilos.label}</span>
      </Badge>
    )
  }
  
  // UI para estado de carga
  if (loadingArchivos) {
    return (
      <Card>
        <CardContent className="py-8">
          <div className="flex items-center justify-center text-secondary-400">
            <Loader2 className="h-6 w-6 animate-spin mr-2" />
            <span>Cargando archivos...</span>
          </div>
        </CardContent>
      </Card>
    )
  }
  
  return (
    <>
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <FileText className="h-5 w-5 text-primary-400" />
            Archivo de Novedades del Cliente
          </CardTitle>
        </CardHeader>
        
        <CardContent className="space-y-4">
          {/* Info del proceso */}
          <div className="bg-blue-900/20 border border-blue-500/30 rounded-lg p-4">
            <p className="text-sm text-blue-300">
              Suba el archivo de novedades proporcionado por el cliente. 
              Los headers serán extraídos automáticamente y deberá mapearlos 
              a los conceptos del libro de remuneraciones.
            </p>
          </div>
          
          {/* Si no hay archivo, mostrar zona de drop */}
          {!archivoNovedades && (
            <div
              onDragEnter={handleDragEnter}
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
              onClick={() => fileInputRef.current?.click()}
              className={cn(
                "border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors",
                isDragging 
                  ? "border-primary-500 bg-primary-500/10" 
                  : "border-secondary-600 hover:border-secondary-500 hover:bg-secondary-800/50"
              )}
            >
              <Upload className="h-12 w-12 mx-auto text-secondary-400 mb-4" />
              <p className="text-secondary-300 mb-2">
                Arrastra el archivo aquí o haz clic para seleccionar
              </p>
              <p className="text-xs text-secondary-500">
                Formatos: {FORMATOS_PERMITIDOS.join(', ')}
              </p>
              <input
                ref={fileInputRef}
                type="file"
                accept={FORMATOS_PERMITIDOS.join(',')}
                onChange={handleFileSelect}
                className="hidden"
              />
            </div>
          )}
          
          {/* Mostrar progreso de subida */}
          {uploadMutation.isPending && (
            <div className="flex items-center gap-3 p-4 bg-secondary-800 rounded-lg">
              <Loader2 className="h-5 w-5 animate-spin text-primary-400" />
              <span className="text-secondary-300">Subiendo archivo...</span>
            </div>
          )}
          
          {/* Si hay archivo, mostrar info y acciones */}
          {archivoNovedades && (
            <div className="border border-secondary-700 rounded-lg p-4 space-y-4">
              {/* Header del archivo */}
              <div className="flex items-start justify-between gap-4">
                <div className="flex items-start gap-3 min-w-0">
                  <FileSpreadsheet className="h-8 w-8 text-green-400 flex-shrink-0" />
                  <div className="min-w-0">
                    <p className="text-secondary-200 font-medium truncate">
                      {archivoNovedades.nombre_original}
                    </p>
                    <div className="flex items-center gap-2 mt-1 text-xs text-secondary-500">
                      <Clock className="h-3 w-3 flex-shrink-0" />
                      <span>
                        Subido: {new Date(archivoNovedades.fecha_subida).toLocaleString()}
                      </span>
                    </div>
                  </div>
                </div>
                
                <div className="flex items-center gap-2 flex-shrink-0">
                  {renderEstadoArchivo(archivoNovedades)}
                  
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => handleDelete(archivoNovedades.id)}
                    disabled={deleteMutation.isPending}
                    className="text-red-400 hover:text-red-300 hover:bg-red-900/20"
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              </div>
              
              {/* Mensaje de error si aplica */}
              {archivoNovedades.estado === ESTADO_ARCHIVO_NOVEDADES.ERROR && (
                <div className="bg-red-900/20 border border-red-500/30 rounded-lg p-3">
                  <p className="text-sm text-red-400 flex items-center gap-2">
                    <AlertCircle className="h-4 w-4" />
                    {archivoNovedades.mensaje_error || 'Error al procesar el archivo'}
                  </p>
                </div>
              )}
              
              {/* Mensaje si está extrayendo headers */}
              {archivoNovedades.estado === ESTADO_ARCHIVO_NOVEDADES.EXTRAYENDO_HEADERS && (
                <div className="bg-yellow-900/20 border border-yellow-500/30 rounded-lg p-3">
                  <p className="text-sm text-yellow-400 flex items-center gap-2">
                    <Loader2 className="h-4 w-4 animate-spin" />
                    Extrayendo headers del archivo... Por favor espere.
                  </p>
                </div>
              )}
              
              {/* Acción de mapeo si está pendiente */}
              {novedadesRequiereAccion(archivoNovedades.estado) && (
                <div className="bg-amber-900/20 border border-amber-500/30 rounded-lg p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-amber-300 font-medium">Mapeo de Items Pendiente</p>
                      <p className="text-sm text-amber-400/80 mt-1">
                        {sinMapearCount !== undefined 
                          ? `${sinMapearCount} items sin mapear` 
                          : 'Cargando...'}
                      </p>
                    </div>
                    <Button
                      variant="primary"
                      onClick={() => handleAbrirMapeo(archivoNovedades)}
                      rightIcon={ChevronRight}
                    >
                      <Link2 className="h-4 w-4 mr-2" />
                      Mapear Items
                    </Button>
                  </div>
                </div>
              )}
              
              {/* Estado listo */}
              {archivoNovedades.estado === ESTADO_ARCHIVO_NOVEDADES.LISTO && (
                <div className="bg-green-900/20 border border-green-500/30 rounded-lg p-3">
                  <p className="text-sm text-green-400 flex items-center gap-2">
                    <Check className="h-4 w-4" />
                    Todos los items están mapeados. El archivo está listo para procesar.
                  </p>
                </div>
              )}
              
              {/* Estado procesado */}
              {archivoNovedades.estado === ESTADO_ARCHIVO_NOVEDADES.PROCESADO && (
                <div className="bg-green-900/20 border border-green-500/30 rounded-lg p-3">
                  <p className="text-sm text-green-400 flex items-center gap-2">
                    <Check className="h-4 w-4" />
                    Archivo procesado exitosamente
                  </p>
                </div>
              )}
            </div>
          )}
        </CardContent>
      </Card>
      
      {/* Modal de Mapeo */}
      <MapeoNovedadesModal
        isOpen={modalMapeoAbierto}
        onClose={() => setModalMapeoAbierto(false)}
        archivo={archivoSeleccionado}
        cierreId={cierreId}
        cliente={{ 
          id: cierre?.cliente,  // ID del cliente
          erp_id: cierre?.cliente_erp?.id  // ID del ERP activo
        }}
        onMapeoComplete={handleMapeoComplete}
      />
    </>
  )
}

export default CargaNovedades
