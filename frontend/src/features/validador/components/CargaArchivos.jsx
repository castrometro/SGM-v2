/**
 * Componente Hub de Carga de Archivos para el Validador de Nómina
 * 
 * Este es el componente principal del estado CARGA_ARCHIVOS.
 * Muestra las dos secciones de archivos:
 * - Archivos del ERP (Libro de Remuneraciones, Movimientos)
 * - Archivos del Cliente (Novedades, Ingresos, Finiquitos, etc.)
 */
import { useState, useCallback, useRef } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { 
  Upload, 
  File, 
  FileSpreadsheet, 
  Check, 
  AlertCircle, 
  Loader2, 
  Trash2,
  RefreshCw,
  FileCheck,
  Database,
  Settings,
  Tag,
  Link2
} from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '../../../components/ui'
import Badge from '../../../components/ui/Badge'
import Button from '../../../components/ui/Button'
import { cn } from '../../../utils/cn'
import {
  useArchivosERP,
  useArchivosAnalista,
  useUploadArchivoERP,
  useUploadArchivoAnalista,
  useDeleteArchivoERP,
  useDeleteArchivoAnalista,
  useProgresoLibro,
  TIPOS_ERP,
  TIPOS_ANALISTA,
} from '../hooks/useArchivos'
import ClasificacionLibroModal from './ClasificacionLibroModal'
import MapeoNovedadesModal from './MapeoNovedadesModal'
import { 
  TIPO_ARCHIVO_ERP, 
  TIPO_ARCHIVO_ANALISTA,
  ESTADO_ARCHIVO,
  ESTADO_ARCHIVO_LIBRO,
  ESTADO_ARCHIVO_NOVEDADES,
  libroRequiereAccion,
  puedeClasificarLibro,
  novedadesRequiereAccion,
  puedeMapearNovedades
} from '../../../constants'

// Constantes para estados de archivo
const ESTADO_STYLES = {
  subido: { color: 'info', icon: FileCheck, label: 'Subido' },
  procesando: { color: 'warning', icon: Loader2, label: 'Procesando', animate: true },
  procesado: { color: 'success', icon: Check, label: 'Procesado' },
  error: { color: 'danger', icon: AlertCircle, label: 'Error' },
  // Estados específicos del libro
  extrayendo_headers: { color: 'warning', icon: Loader2, label: 'Extrayendo Headers', animate: true },
  pendiente_clasificacion: { color: 'warning', icon: Tag, label: 'Requiere Clasificación' },
  listo: { color: 'info', icon: FileCheck, label: 'Listo para Procesar' },
  // Estados específicos de novedades
  pendiente_mapeo: { color: 'warning', icon: Link2, label: 'Requiere Mapeo' },
}

// Formatos de archivo permitidos
const FORMATOS_PERMITIDOS = ['.xlsx', '.xls', '.csv']

/**
 * Componente para mostrar progreso detallado del procesamiento del Libro
 * Usa el endpoint específico de progreso con polling cada 2s
 * 
 * Fases del progreso:
 * - 0-5%: Preparando procesamiento
 * - 5-10%: Leyendo archivo Excel
 * - 10-15%: Parseando empleados
 * - 15-30%: Procesando datos
 * - 30-50%: Creando empleados en BD
 * - 50-90%: Procesando conceptos (proporcional a empleados)
 * - 90-95%: Guardando registros
 * - 95-100%: Finalizando
 */
const ProgresoProcesamientoLibro = ({ archivoId }) => {
  const { data: progreso, isLoading } = useProgresoLibro(archivoId, {
    enabled: !!archivoId
  })

  if (isLoading || !progreso) {
    return (
      <div className="flex items-center gap-2 text-xs text-secondary-400">
        <Loader2 className="h-3 w-3 animate-spin" />
        <span>Iniciando procesamiento...</span>
      </div>
    )
  }

  const { estado, progreso: porcentaje = 0, empleados_procesados = 0, mensaje } = progreso

  // Colores según estado
  const barColor = estado === 'error' 
    ? 'bg-red-500' 
    : estado === 'completado'
      ? 'bg-green-500'
      : 'bg-gradient-to-r from-primary-500 to-accent-500'

  return (
    <div className="mt-2 space-y-2">
      {/* Barra de progreso con animación */}
      <div className="w-full bg-secondary-700 rounded-full h-2.5 overflow-hidden">
        <div 
          className={cn(
            "h-full transition-all duration-500 ease-out",
            barColor,
            estado === 'procesando' && "animate-pulse"
          )}
          style={{ width: `${Math.min(porcentaje, 100)}%` }}
        />
      </div>
      
      {/* Info del progreso */}
      <div className="flex items-center justify-between text-xs">
        <div className="flex items-center gap-2 text-secondary-400 min-w-0 flex-1">
          {estado === 'procesando' && (
            <>
              <Loader2 className="h-3 w-3 animate-spin text-primary-400 flex-shrink-0" />
              <span className="truncate">{mensaje || 'Procesando...'}</span>
            </>
          )}
          {estado === 'completado' && (
            <>
              <Check className="h-3 w-3 text-green-400 flex-shrink-0" />
              <span className="text-green-400">Procesamiento completado</span>
            </>
          )}
          {estado === 'error' && (
            <>
              <AlertCircle className="h-3 w-3 text-red-400 flex-shrink-0" />
              <span className="text-red-400 truncate">{mensaje || 'Error en procesamiento'}</span>
            </>
          )}
        </div>
        
        <div className="flex items-center gap-3 text-secondary-500 flex-shrink-0 ml-2">
          {empleados_procesados > 0 && (
            <span className="flex items-center gap-1 text-primary-400">
              <Users className="h-3 w-3" />
              <span className="font-medium">{empleados_procesados.toLocaleString()}</span>
            </span>
          )}
          <span className={cn(
            "font-bold tabular-nums",
            estado === 'completado' ? "text-green-400" : "text-secondary-300"
          )}>
            {porcentaje}%
          </span>
        </div>
      </div>
    </div>
  )
}

/**
 * Componente de zona de drop para un tipo de archivo específico
 */
const DropZone = ({ tipo, label, descripcion, archivo, onUpload, onDelete, isUploading, progress, categoria, onClasificar, disabled, disabledMessage }) => {
  const [isDragging, setIsDragging] = useState(false)
  const fileInputRef = useRef(null)

  const handleDragOver = useCallback((e) => {
    if (disabled) return
    e.preventDefault()
    setIsDragging(true)
  }, [disabled])

  const handleDragLeave = useCallback((e) => {
    e.preventDefault()
    setIsDragging(false)
  }, [])

  const handleDrop = useCallback((e) => {
    e.preventDefault()
    setIsDragging(false)
    
    if (disabled) return
    
    const files = e.dataTransfer.files
    if (files.length > 0) {
      const file = files[0]
      const ext = '.' + file.name.split('.').pop().toLowerCase()
      if (FORMATOS_PERMITIDOS.includes(ext)) {
        onUpload(file)
      } else {
        alert(`Formato no permitido. Use: ${FORMATOS_PERMITIDOS.join(', ')}`)
      }
    }
  }, [onUpload, disabled])

  const handleFileSelect = useCallback((e) => {
    const file = e.target.files[0]
    if (file) {
      onUpload(file)
    }
    // Limpiar el input para permitir seleccionar el mismo archivo de nuevo
    e.target.value = ''
  }, [onUpload])

  const handleClick = () => {
    if (!isUploading && !archivo && !disabled) {
      fileInputRef.current?.click()
    }
  }

  const estadoInfo = archivo ? ESTADO_STYLES[archivo.estado] : null
  const IconEstado = estadoInfo?.icon

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between gap-4">
        <div className="min-w-0">
          <h4 className="text-sm font-medium text-secondary-200">{label}</h4>
          <p className="text-xs text-secondary-500">{descripcion}</p>
        </div>
        {archivo && estadoInfo && (
          <Badge 
            variant={estadoInfo.color} 
            className={cn(
              "flex-shrink-0 gap-1.5 whitespace-nowrap px-2.5 py-1",
              estadoInfo.animate && "animate-pulse"
            )}
          >
            {IconEstado && (
              <IconEstado className={cn("h-3 w-3", estadoInfo.animate && "animate-spin")} />
            )}
            <span>{estadoInfo.label}</span>
          </Badge>
        )}
      </div>

      {/* Archivo existente */}
      {archivo && !isUploading ? (
        <div className="p-3 bg-secondary-800/50 rounded-lg border border-secondary-700">
          <div className="flex items-center gap-3">
            <FileSpreadsheet className="h-8 w-8 text-primary-400 flex-shrink-0" />
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-secondary-100 truncate">
                {archivo.nombre_original}
              </p>
              <div className="flex items-center gap-2 text-xs text-secondary-400">
                <span>v{archivo.version}</span>
                {archivo.estado !== ESTADO_ARCHIVO.PROCESANDO && (
                  <>
                    <span>•</span>
                    <span>{archivo.filas_procesadas} filas</span>
                  </>
                )}
                {archivo.subido_por_nombre && (
                  <>
                    <span>•</span>
                    <span>{archivo.subido_por_nombre}</span>
                  </>
                )}
              </div>
            </div>
            <div className="flex items-center gap-1">
              {/* Botón de clasificación para Libro de Remuneraciones */}
              {tipo === TIPO_ARCHIVO_ERP.LIBRO_REMUNERACIONES && 
               puedeClasificarLibro(archivo.estado) && 
               onClasificar && (
                <button
                  onClick={() => onClasificar(archivo)}
                  className={cn(
                    "p-1.5 rounded-lg transition-colors flex items-center gap-1",
                    libroRequiereAccion(archivo.estado)
                      ? "text-warning-400 hover:text-warning-300 hover:bg-warning-500/20 animate-pulse"
                      : "text-secondary-400 hover:text-primary-400 hover:bg-secondary-700"
                  )}
                  title="Clasificar conceptos"
                >
                  <Settings className="h-4 w-4" />
                </button>
              )}
              {/* Botón de mapeo para Novedades */}
              {tipo === TIPO_ARCHIVO_ANALISTA.NOVEDADES && 
               puedeMapearNovedades(archivo.estado) && 
               onClasificar && (
                <button
                  onClick={() => onClasificar(archivo)}
                  className={cn(
                    "p-1.5 rounded-lg transition-colors flex items-center gap-1",
                    novedadesRequiereAccion(archivo.estado)
                      ? "text-warning-400 hover:text-warning-300 hover:bg-warning-500/20 animate-pulse"
                      : "text-secondary-400 hover:text-primary-400 hover:bg-secondary-700"
                  )}
                  title="Mapear conceptos"
                >
                  <Link2 className="h-4 w-4" />
                </button>
              )}
              {/* Solo mostrar icono spinner si NO es libro (libro tiene su propio componente de progreso) */}
              {IconEstado && !(tipo === TIPO_ARCHIVO_ERP.LIBRO_REMUNERACIONES && archivo.estado === ESTADO_ARCHIVO.PROCESANDO) && (
                <IconEstado className={cn(
                  "h-4 w-4",
                  estadoInfo.animate && "animate-spin",
                  estadoInfo.color === 'success' && "text-green-400",
                  estadoInfo.color === 'danger' && "text-red-400",
                  estadoInfo.color === 'warning' && "text-yellow-400",
                  estadoInfo.color === 'info' && "text-blue-400",
                )} />
              )}
              <button
                onClick={() => onDelete(archivo.id)}
                className="p-1.5 rounded-lg text-secondary-400 hover:text-red-400 hover:bg-secondary-700 transition-colors"
                title="Eliminar archivo"
                disabled={archivo.estado === ESTADO_ARCHIVO.PROCESANDO}
              >
                <Trash2 className="h-4 w-4" />
              </button>
              <button
                onClick={() => fileInputRef.current?.click()}
                className="p-1.5 rounded-lg text-secondary-400 hover:text-primary-400 hover:bg-secondary-700 transition-colors"
                title="Reemplazar archivo"
                disabled={archivo.estado === ESTADO_ARCHIVO.PROCESANDO}
              >
                <RefreshCw className="h-4 w-4" />
              </button>
            </div>
          </div>
          
          {/* Mostrar progreso detallado para Libro de Remuneraciones en procesamiento */}
          {tipo === TIPO_ARCHIVO_ERP.LIBRO_REMUNERACIONES && archivo.estado === ESTADO_ARCHIVO.PROCESANDO && (
            <ProgresoProcesamientoLibro archivoId={archivo.id} />
          )}
          
          {/* Alerta de clasificación requerida para Libro */}
          {tipo === TIPO_ARCHIVO_ERP.LIBRO_REMUNERACIONES && libroRequiereAccion(archivo.estado) && (
            <div className="mt-2 p-2 bg-warning-500/10 border border-warning-500/30 rounded-lg">
              <div className="flex items-center gap-2">
                <Tag className="h-4 w-4 text-warning-400 flex-shrink-0" />
                <div className="flex-1">
                  <p className="text-sm text-warning-300 font-medium">
                    Clasificación de conceptos pendiente
                  </p>
                  <p className="text-xs text-secondary-400">
                    Clasifica los conceptos antes de procesar el libro
                  </p>
                </div>
                {onClasificar && (
                  <Button
                    size="sm"
                    variant="warning"
                    onClick={() => onClasificar(archivo)}
                    className="flex items-center gap-1"
                  >
                    <Settings className="h-3 w-3" />
                    Clasificar
                  </Button>
                )}
              </div>
            </div>
          )}
          
          {/* Indicador de listo para procesar */}
          {tipo === TIPO_ARCHIVO_ERP.LIBRO_REMUNERACIONES && archivo.estado === ESTADO_ARCHIVO_LIBRO.LISTO && (
            <div className="mt-2 p-2 bg-success-500/10 border border-success-500/30 rounded-lg">
              <div className="flex items-center gap-2">
                <Check className="h-4 w-4 text-success-400" />
                <p className="text-sm text-success-300">
                  Conceptos clasificados. Listo para procesar.
                </p>
              </div>
            </div>
          )}
          
          {/* Alerta de mapeo requerido para Novedades */}
          {tipo === TIPO_ARCHIVO_ANALISTA.NOVEDADES && novedadesRequiereAccion(archivo.estado) && (
            <div className="mt-2 p-2 bg-warning-500/10 border border-warning-500/30 rounded-lg">
              <div className="flex items-center gap-2">
                <Link2 className="h-4 w-4 text-warning-400 flex-shrink-0" />
                <div className="flex-1">
                  <p className="text-sm text-warning-300 font-medium">
                    Mapeo de conceptos pendiente
                  </p>
                  <p className="text-xs text-secondary-400">
                    Mapea los conceptos de novedades al libro
                  </p>
                </div>
                {onClasificar && (
                  <Button
                    size="sm"
                    variant="warning"
                    onClick={() => onClasificar(archivo)}
                    className="flex items-center gap-1"
                  >
                    <Link2 className="h-3 w-3" />
                    Mapear
                  </Button>
                )}
              </div>
            </div>
          )}
          
          {/* Indicador de novedades listo */}
          {tipo === TIPO_ARCHIVO_ANALISTA.NOVEDADES && archivo.estado === ESTADO_ARCHIVO_NOVEDADES.LISTO && (
            <div className="mt-2 p-2 bg-success-500/10 border border-success-500/30 rounded-lg">
              <div className="flex items-center gap-2">
                <Check className="h-4 w-4 text-success-400" />
                <p className="text-sm text-success-300">
                  Conceptos mapeados. Listo para procesar.
                </p>
              </div>
            </div>
          )}
        </div>
      ) : (
        /* Zona de drop */
        <div
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          onClick={handleClick}
          className={cn(
            "relative flex flex-col items-center justify-center p-6 rounded-lg border-2 border-dashed transition-all",
            disabled && "cursor-not-allowed opacity-50 border-secondary-700 bg-secondary-900/30",
            !disabled && isDragging && "border-primary-500 bg-primary-500/10 cursor-pointer",
            !disabled && !isDragging && !isUploading && "border-secondary-700 hover:border-secondary-500 hover:bg-secondary-800/50 cursor-pointer",
            !disabled && isUploading && "border-primary-500 bg-primary-500/5 cursor-not-allowed",
          )}
        >
          {disabled ? (
            <div className="flex flex-col items-center gap-2">
              <Upload className="h-8 w-8 text-secondary-600" />
              <p className="text-sm text-secondary-500 text-center">
                {disabledMessage || 'No disponible'}
              </p>
            </div>
          ) : isUploading ? (
            <div className="flex flex-col items-center gap-2 w-full">
              <Loader2 className="h-8 w-8 text-primary-400 animate-spin" />
              <p className="text-sm text-secondary-300">Subiendo archivo...</p>
              {/* Barra de progreso */}
              <div className="w-full max-w-xs bg-secondary-700 rounded-full h-2 overflow-hidden">
                <div 
                  className="bg-primary-500 h-full transition-all duration-300"
                  style={{ width: `${progress}%` }}
                />
              </div>
              <p className="text-xs text-secondary-400">{progress}%</p>
            </div>
          ) : (
            <>
              <Upload className={cn(
                "h-8 w-8 mb-2 transition-colors",
                isDragging ? "text-primary-400" : "text-secondary-500"
              )} />
              <p className="text-sm text-secondary-300 text-center">
                {isDragging ? 'Suelta el archivo aquí' : 'Arrastra un archivo o haz clic para seleccionar'}
              </p>
              <p className="text-xs text-secondary-500 mt-1">
                Formatos: {FORMATOS_PERMITIDOS.join(', ')}
              </p>
            </>
          )}
        </div>
      )}

      {/* Input oculto */}
      <input
        ref={fileInputRef}
        type="file"
        accept={FORMATOS_PERMITIDOS.join(',')}
        onChange={handleFileSelect}
        className="hidden"
      />

      {/* Error de mensaje (específico del libro) */}
      {archivo?.error_mensaje && (
        <div className="p-2 bg-red-500/10 border border-red-500/20 rounded-lg">
          <div className="flex items-start gap-2">
            <AlertCircle className="h-4 w-4 text-red-400 flex-shrink-0 mt-0.5" />
            <div>
              <p className="text-xs font-medium text-red-400">Error:</p>
              <p className="text-xs text-red-300">{archivo.error_mensaje}</p>
            </div>
          </div>
        </div>
      )}

      {/* Errores de procesamiento (lista) */}
      {archivo?.errores_procesamiento?.length > 0 && (
        <div className="p-2 bg-red-500/10 border border-red-500/20 rounded-lg">
          <p className="text-xs font-medium text-red-400 mb-1">Errores de procesamiento:</p>
          <ul className="text-xs text-red-300 list-disc list-inside space-y-0.5">
            {archivo.errores_procesamiento.slice(0, 3).map((error, idx) => (
              <li key={idx}>{error}</li>
            ))}
            {archivo.errores_procesamiento.length > 3 && (
              <li>...y {archivo.errores_procesamiento.length - 3} errores más</li>
            )}
          </ul>
        </div>
      )}
    </div>
  )
}

/**
 * Componente principal de Carga de Archivos (HUB)
 * 
 * Props:
 * - cierreId: ID del cierre
 * - cierre: Objeto cierre completo (con cliente_id, cliente_erp, etc.)
 * - onUpdate: Callback para refrescar datos del cierre
 */
const CargaArchivos = ({ cierreId, cierre, onUpdate }) => {
  const queryClient = useQueryClient()
  
  // Estados locales para progreso de subida
  const [uploadingERP, setUploadingERP] = useState({})
  const [uploadingAnalista, setUploadingAnalista] = useState({})
  const [progressERP, setProgressERP] = useState({})
  const [progressAnalista, setProgressAnalista] = useState({})
  
  // Estado para modales
  const [clasificacionModalOpen, setClasificacionModalOpen] = useState(false)
  const [archivoParaClasificar, setArchivoParaClasificar] = useState(null)
  const [mapeoModalOpen, setMapeoModalOpen] = useState(false)
  const [archivoParaMapeo, setArchivoParaMapeo] = useState(null)

  // Queries para obtener archivos existentes
  const { data: archivosERP, isLoading: loadingERP, refetch: refetchERP } = useArchivosERP(cierreId)
  const { data: archivosAnalista, isLoading: loadingAnalista, refetch: refetchAnalista } = useArchivosAnalista(cierreId)

  // Mutations
  const uploadERP = useUploadArchivoERP()
  const uploadAnalista = useUploadArchivoAnalista()
  const deleteERP = useDeleteArchivoERP()
  const deleteAnalista = useDeleteArchivoAnalista()

  // Archivos específicos
  const libroERP = archivosERP?.libro_remuneraciones

  // Handlers para modales
  const handleOpenClasificacion = useCallback((archivo) => {
    setArchivoParaClasificar(archivo)
    setClasificacionModalOpen(true)
  }, [])

  const handleCloseClasificacion = useCallback(() => {
    setClasificacionModalOpen(false)
    setArchivoParaClasificar(null)
    refetchERP()
  }, [refetchERP])

  const handleOpenMapeo = useCallback((archivo) => {
    setArchivoParaMapeo(archivo)
    setMapeoModalOpen(true)
  }, [])

  const handleCloseMapeo = useCallback(() => {
    setMapeoModalOpen(false)
    setArchivoParaMapeo(null)
    refetchAnalista()
  }, [refetchAnalista])

  // Handlers para archivos ERP
  const handleUploadERP = useCallback((tipo, archivo) => {
    setUploadingERP(prev => ({ ...prev, [tipo]: true }))
    setProgressERP(prev => ({ ...prev, [tipo]: 0 }))

    uploadERP.mutate(
      { 
        cierreId, 
        tipo, 
        archivo,
        onProgress: (progress) => setProgressERP(prev => ({ ...prev, [tipo]: progress }))
      },
      {
        onSettled: () => {
          setUploadingERP(prev => ({ ...prev, [tipo]: false }))
          setProgressERP(prev => ({ ...prev, [tipo]: 0 }))
        },
      }
    )
  }, [cierreId, uploadERP])

  const handleDeleteERP = useCallback((archivoId) => {
    if (confirm('¿Estás seguro de eliminar este archivo?')) {
      deleteERP.mutate({ archivoId, cierreId })
    }
  }, [cierreId, deleteERP])

  // Handlers para archivos Analista
  const handleUploadAnalista = useCallback((tipo, archivo) => {
    setUploadingAnalista(prev => ({ ...prev, [tipo]: true }))
    setProgressAnalista(prev => ({ ...prev, [tipo]: 0 }))

    uploadAnalista.mutate(
      { 
        cierreId, 
        tipo, 
        archivo,
        onProgress: (progress) => setProgressAnalista(prev => ({ ...prev, [tipo]: progress }))
      },
      {
        onSettled: () => {
          setUploadingAnalista(prev => ({ ...prev, [tipo]: false }))
          setProgressAnalista(prev => ({ ...prev, [tipo]: 0 }))
        },
      }
    )
  }, [cierreId, uploadAnalista])

  const handleDeleteAnalista = useCallback((archivoId) => {
    if (confirm('¿Estás seguro de eliminar este archivo?')) {
      deleteAnalista.mutate({ archivoId, cierreId })
    }
  }, [cierreId, deleteAnalista])

  const isLoading = loadingERP || loadingAnalista

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-8 w-8 animate-spin text-primary-400" />
      </div>
    )
  }

  // Libro procesado para habilitar novedades
  const libroOk = libroERP?.estado === ESTADO_ARCHIVO_LIBRO.PROCESADO

  // Calcular progreso total
  const totalERP = TIPOS_ERP.length
  const uploadedERP = TIPOS_ERP.filter(t => archivosERP?.[t.value]).length
  const totalAnalista = TIPOS_ANALISTA.length
  const uploadedAnalista = TIPOS_ANALISTA.filter(t => archivosAnalista?.[t.value]).length

  return (
    <div className="space-y-6">
      {/* Resumen de progreso */}
      <Card>
        <CardContent className="py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2">
                <FileSpreadsheet className="h-5 w-5 text-primary-400" />
                <span className="text-sm text-secondary-300">
                  Archivos ERP: <span className="font-medium text-secondary-100">{uploadedERP}/{totalERP}</span>
                </span>
              </div>
              <div className="flex items-center gap-2">
                <File className="h-5 w-5 text-green-400" />
                <span className="text-sm text-secondary-300">
                  Archivos Analista: <span className="font-medium text-secondary-100">{uploadedAnalista}/{totalAnalista}</span>
                </span>
              </div>
            </div>
            <Button 
              variant="outline" 
              size="sm"
              onClick={() => { refetchERP(); refetchAnalista() }}
            >
              <RefreshCw className="h-4 w-4 mr-2" />
              Actualizar
            </Button>
          </div>
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Archivos ERP */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <FileSpreadsheet className="h-5 w-5 text-primary-400" />
                <CardTitle>Archivos del ERP</CardTitle>
              </div>
              {cierre?.cliente_erp ? (
                <Badge variant="info" className="flex items-center gap-1.5">
                  <Database className="h-3.5 w-3.5" />
                  {cierre.cliente_erp.nombre}
                </Badge>
              ) : (
                <Badge variant="secondary" className="flex items-center gap-1.5">
                  <Database className="h-3.5 w-3.5" />
                  Sin ERP
                </Badge>
              )}
            </div>
            <p className="text-sm text-secondary-400 mt-1">
              {cierre?.cliente_erp 
                ? `Archivos generados desde ${cierre.cliente_erp.nombre}`
                : 'Archivos generados desde el sistema de nómina'
              }
            </p>
          </CardHeader>
          <CardContent className="space-y-4">
            {TIPOS_ERP.map((tipo) => (
              <DropZone
                key={tipo.value}
                tipo={tipo.value}
                label={tipo.label}
                descripcion={tipo.descripcion}
                archivo={archivosERP?.[tipo.value]}
                onUpload={(file) => handleUploadERP(tipo.value, file)}
                onDelete={handleDeleteERP}
                isUploading={uploadingERP[tipo.value]}
                progress={progressERP[tipo.value] || 0}
                categoria="erp"
                onClasificar={tipo.value === TIPO_ARCHIVO_ERP.LIBRO_REMUNERACIONES ? handleOpenClasificacion : undefined}
              />
            ))}
          </CardContent>
        </Card>

        {/* Archivos del Analista */}
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <File className="h-5 w-5 text-green-400" />
              <CardTitle>Archivos del Cliente</CardTitle>
            </div>
            <p className="text-sm text-secondary-400 mt-1">
              Archivos proporcionados por el cliente para validación
            </p>
          </CardHeader>
          <CardContent className="space-y-4">
            {TIPOS_ANALISTA.map((tipo) => (
              <DropZone
                key={tipo.value}
                tipo={tipo.value}
                label={tipo.label}
                descripcion={tipo.descripcion}
                archivo={archivosAnalista?.[tipo.value]}
                onUpload={(file) => handleUploadAnalista(tipo.value, file)}
                onDelete={handleDeleteAnalista}
                isUploading={uploadingAnalista[tipo.value]}
                progress={progressAnalista[tipo.value] || 0}
                categoria="analista"
                onClasificar={tipo.value === 'novedades' ? handleOpenMapeo : undefined}
                disabled={tipo.value === 'novedades' && !libroOk}
                disabledMessage="Primero procesa el Libro de Remuneraciones"
              />
            ))}
          </CardContent>
        </Card>
      </div>

      {/* Instrucciones */}
      <Card className="bg-secondary-800/30">
        <CardContent className="py-4">
          <div className="flex items-start gap-3">
            <AlertCircle className="h-5 w-5 text-yellow-400 flex-shrink-0 mt-0.5" />
            <div className="text-sm text-secondary-300">
              <p className="font-medium text-secondary-200 mb-1">Instrucciones:</p>
              <ul className="list-disc list-inside space-y-1 text-secondary-400">
                <li>Los archivos deben estar en formato Excel (.xlsx, .xls) o CSV (.csv)</li>
                <li>Puedes reemplazar un archivo subiendo una nueva versión</li>
                <li>El <strong>Libro de Remuneraciones</strong> debe estar procesado para subir Novedades</li>
              </ul>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Modal de Clasificación del Libro */}
      <ClasificacionLibroModal
        isOpen={clasificacionModalOpen}
        onClose={handleCloseClasificacion}
        archivo={archivoParaClasificar}
        cierreId={cierreId}
        onClasificacionComplete={() => {
          refetchERP()
        }}
        onProcesoIniciado={() => {
          refetchERP()
        }}
      />

      {/* Modal de Mapeo de Novedades */}
      <MapeoNovedadesModal
        isOpen={mapeoModalOpen}
        onClose={handleCloseMapeo}
        archivo={archivoParaMapeo}
        cierreId={cierreId}
        clienteId={cierre?.cliente}
        erpId={cierre?.cliente_erp?.id}
        onMapeoComplete={() => {
          refetchAnalista()
        }}
      />
    </div>
  )
}

/**
 * Item del checklist
 */
export default CargaArchivos
