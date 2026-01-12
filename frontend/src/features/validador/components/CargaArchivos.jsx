/**
 * Componente de Carga de Archivos para el Validador de Nómina
 * Soporta drag & drop, muestra progreso y lista de archivos subidos
 */
import { useState, useCallback, useRef } from 'react'
import { 
  Upload, 
  File, 
  FileSpreadsheet, 
  X, 
  Check, 
  AlertCircle, 
  Loader2, 
  Trash2,
  RefreshCw,
  FileCheck,
  Database,
  Users
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
import { TIPO_ARCHIVO_ERP, ESTADO_ARCHIVO } from '../../../constants'

// Constantes para estados de archivo
const ESTADO_STYLES = {
  subido: { color: 'info', icon: FileCheck, label: 'Subido' },
  procesando: { color: 'warning', icon: Loader2, label: 'Procesando', animate: true },
  procesado: { color: 'success', icon: Check, label: 'Procesado' },
  error: { color: 'danger', icon: AlertCircle, label: 'Error' },
}

// Formatos de archivo permitidos
const FORMATOS_PERMITIDOS = ['.xlsx', '.xls', '.csv']

/**
 * Componente para mostrar progreso detallado del procesamiento del Libro
 * Usa el endpoint específico de progreso con polling
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

  return (
    <div className="mt-2 space-y-2">
      {/* Barra de progreso */}
      <div className="w-full bg-secondary-700 rounded-full h-2 overflow-hidden">
        <div 
          className={cn(
            "h-full transition-all duration-500 ease-out",
            estado === 'error' ? "bg-red-500" : "bg-primary-500"
          )}
          style={{ width: `${Math.min(porcentaje, 100)}%` }}
        />
      </div>
      
      {/* Info del progreso */}
      <div className="flex items-center justify-between text-xs">
        <div className="flex items-center gap-2 text-secondary-400">
          {estado === 'procesando' && (
            <>
              <Loader2 className="h-3 w-3 animate-spin text-primary-400" />
              <span>{mensaje || 'Procesando...'}</span>
            </>
          )}
          {estado === 'completado' && (
            <>
              <Check className="h-3 w-3 text-green-400" />
              <span className="text-green-400">Procesamiento completado</span>
            </>
          )}
          {estado === 'error' && (
            <>
              <AlertCircle className="h-3 w-3 text-red-400" />
              <span className="text-red-400">{mensaje || 'Error en procesamiento'}</span>
            </>
          )}
        </div>
        
        <div className="flex items-center gap-3 text-secondary-500">
          {empleados_procesados > 0 && (
            <span className="flex items-center gap-1">
              <Users className="h-3 w-3" />
              {empleados_procesados.toLocaleString()}
            </span>
          )}
          <span className="font-medium text-secondary-300">{porcentaje}%</span>
        </div>
      </div>
    </div>
  )
}

/**
 * Componente de zona de drop para un tipo de archivo específico
 */
const DropZone = ({ tipo, label, descripcion, archivo, onUpload, onDelete, isUploading, progress, categoria }) => {
  const [isDragging, setIsDragging] = useState(false)
  const fileInputRef = useRef(null)

  const handleDragOver = useCallback((e) => {
    e.preventDefault()
    setIsDragging(true)
  }, [])

  const handleDragLeave = useCallback((e) => {
    e.preventDefault()
    setIsDragging(false)
  }, [])

  const handleDrop = useCallback((e) => {
    e.preventDefault()
    setIsDragging(false)
    
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
  }, [onUpload])

  const handleFileSelect = useCallback((e) => {
    const file = e.target.files[0]
    if (file) {
      onUpload(file)
    }
    // Limpiar el input para permitir seleccionar el mismo archivo de nuevo
    e.target.value = ''
  }, [onUpload])

  const handleClick = () => {
    if (!isUploading && !archivo) {
      fileInputRef.current?.click()
    }
  }

  const estadoInfo = archivo ? ESTADO_STYLES[archivo.estado] : null
  const IconEstado = estadoInfo?.icon

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <div>
          <h4 className="text-sm font-medium text-secondary-200">{label}</h4>
          <p className="text-xs text-secondary-500">{descripcion}</p>
        </div>
        {archivo && (
          <Badge variant={estadoInfo?.color} className="text-xs">
            {estadoInfo?.label}
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
        </div>
      ) : (
        /* Zona de drop */
        <div
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          onClick={handleClick}
          className={cn(
            "relative flex flex-col items-center justify-center p-6 rounded-lg border-2 border-dashed cursor-pointer transition-all",
            isDragging && "border-primary-500 bg-primary-500/10",
            !isDragging && !isUploading && "border-secondary-700 hover:border-secondary-500 hover:bg-secondary-800/50",
            isUploading && "border-primary-500 bg-primary-500/5 cursor-not-allowed",
          )}
        >
          {isUploading ? (
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

      {/* Errores de procesamiento */}
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
 * Componente principal de Carga de Archivos
 */
const CargaArchivos = ({ cierreId, clienteErp = null }) => {
  // Estados locales para progreso de subida
  const [uploadingERP, setUploadingERP] = useState({})
  const [uploadingAnalista, setUploadingAnalista] = useState({})
  const [progressERP, setProgressERP] = useState({})
  const [progressAnalista, setProgressAnalista] = useState({})

  // Queries para obtener archivos existentes
  const { data: archivosERP, isLoading: loadingERP, refetch: refetchERP } = useArchivosERP(cierreId)
  const { data: archivosAnalista, isLoading: loadingAnalista, refetch: refetchAnalista } = useArchivosAnalista(cierreId)

  // Mutations
  const uploadERP = useUploadArchivoERP()
  const uploadAnalista = useUploadArchivoAnalista()
  const deleteERP = useDeleteArchivoERP()
  const deleteAnalista = useDeleteArchivoAnalista()

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

  // Calcular progreso total
  const totalERP = TIPOS_ERP.length
  const uploadedERP = TIPOS_ERP.filter(t => archivosERP?.[t.value]).length
  const totalAnalista = TIPOS_ANALISTA.length
  const uploadedAnalista = TIPOS_ANALISTA.filter(t => archivosAnalista?.[t.value]).length

  const isLoading = loadingERP || loadingAnalista

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-8 w-8 animate-spin text-primary-400" />
      </div>
    )
  }

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
              {clienteErp ? (
                <Badge variant="info" className="flex items-center gap-1.5">
                  <Database className="h-3.5 w-3.5" />
                  {clienteErp.nombre}
                </Badge>
              ) : (
                <Badge variant="secondary" className="flex items-center gap-1.5">
                  <Database className="h-3.5 w-3.5" />
                  Sin ERP
                </Badge>
              )}
            </div>
            <p className="text-sm text-secondary-400 mt-1">
              {clienteErp 
                ? `Archivos generados desde ${clienteErp.nombre}`
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
                <li>El <strong>Libro de Remuneraciones</strong> y <strong>Movimientos del Mes</strong> son obligatorios</li>
                <li>Los archivos del cliente son opcionales según las novedades del período</li>
                <li>Puedes reemplazar un archivo subiendo una nueva versión</li>
              </ul>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

export default CargaArchivos
