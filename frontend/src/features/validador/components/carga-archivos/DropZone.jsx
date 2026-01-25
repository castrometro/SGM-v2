/**
 * Componente de zona de drop para un tipo de archivo específico
 * Maneja drag & drop, selección de archivos, y estados visuales
 */
import { useState, useCallback, useRef } from 'react'
import { 
  Upload, 
  FileSpreadsheet, 
  Check, 
  AlertCircle, 
  Loader2, 
  Trash2,
  RefreshCw,
  Settings,
  Tag,
  Link2
} from 'lucide-react'
import Badge from '../../../../components/ui/Badge'
import Button from '../../../../components/ui/Button'
import { cn } from '../../../../utils/cn'
import { ESTADO_STYLES, FORMATOS_PERMITIDOS } from './constants/estadoStyles'
import ProgresoProcesamientoLibro from './ProgresoProcesamientoLibro'
import { 
  TIPO_ARCHIVO_ERP, 
  TIPO_ARCHIVO_ANALISTA,
  ESTADO_ARCHIVO,
  ESTADO_ARCHIVO_LIBRO,
  ESTADO_ARCHIVO_NOVEDADES,
  libroRequiereAccion,
  puedeClasificarLibro,
  novedadesRequiereAccion,
  puedeMapearNovedades,
} from '../../../../constants'

/**
 * @param {Object} props
 * @param {string} props.tipo - Tipo de archivo (libro_remuneraciones, novedades, etc.)
 * @param {string} props.label - Etiqueta visible del tipo de archivo
 * @param {string} props.descripcion - Descripción breve del tipo de archivo
 * @param {Object} props.archivo - Datos del archivo existente (si hay)
 * @param {Function} props.onUpload - Callback cuando se sube un archivo
 * @param {Function} props.onDelete - Callback cuando se elimina un archivo
 * @param {boolean} props.isUploading - Si está subiendo actualmente
 * @param {number} props.progress - Progreso de subida (0-100)
 * @param {string} props.categoria - 'erp' o 'analista'
 * @param {Function} [props.onClasificar] - Callback para abrir modal de clasificación/mapeo
 * @param {boolean} [props.disabled] - Si la zona está deshabilitada
 * @param {string} [props.disabledMessage] - Mensaje cuando está deshabilitada
 * @param {Function} [props.onNoAplica] - Callback para marcar como "No Aplica"
 * @param {Function} [props.onDesmarcarNoAplica] - Callback para desmarcar "No Aplica"
 * @param {boolean} [props.isMarkingNoAplica] - Si está procesando el marcado de "No Aplica"
 */
const DropZone = ({ 
  tipo, 
  label, 
  descripcion, 
  archivo, 
  onUpload, 
  onDelete, 
  isUploading, 
  progress, 
  categoria, 
  onClasificar, 
  disabled, 
  disabledMessage, 
  onNoAplica, 
  onDesmarcarNoAplica, 
  isMarkingNoAplica 
}) => {
  const [isDragging, setIsDragging] = useState(false)
  const fileInputRef = useRef(null)

  // Un archivo está en estado NO_APLICA
  const isNoAplica = archivo?.estado === ESTADO_ARCHIVO_NOVEDADES.NO_APLICA

  const handleDragOver = useCallback((e) => {
    if (disabled || isNoAplica) return
    e.preventDefault()
    setIsDragging(true)
  }, [disabled, isNoAplica])

  const handleDragLeave = useCallback((e) => {
    e.preventDefault()
    setIsDragging(false)
  }, [])

  const handleDrop = useCallback((e) => {
    e.preventDefault()
    setIsDragging(false)
    
    if (disabled || isNoAplica) return
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
  }, [onUpload, disabled, isNoAplica])

  const handleFileSelect = useCallback((e) => {
    const file = e.target.files[0]
    if (file) {
      onUpload(file)
    }
    // Limpiar el input para permitir seleccionar el mismo archivo de nuevo
    e.target.value = ''
  }, [onUpload])

  const handleClick = () => {
    if (!isUploading && !archivo && !disabled && !isNoAplica) {
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

      {/* Archivo existente o NO_APLICA */}
      {archivo && !isUploading ? (
        isNoAplica ? (
          /* Estado NO_APLICA - UI simplificada */
          <div className="p-3 bg-secondary-800/30 rounded-lg border border-secondary-700/50">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-secondary-700/50 rounded-lg">
                  <Check className="h-5 w-5 text-secondary-400" />
                </div>
                <div>
                  <p className="text-sm font-medium text-secondary-300">No aplica este mes</p>
                  <p className="text-xs text-secondary-500">Sin datos para este período</p>
                </div>
              </div>
              {onDesmarcarNoAplica && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => onDesmarcarNoAplica(tipo)}
                  className="text-secondary-400 hover:text-primary-400"
                >
                  <RefreshCw className="h-4 w-4 mr-1" />
                  Desmarcar
                </Button>
              )}
            </div>
          </div>
        ) : (
          /* Archivo normal subido */
          <div className="p-3 bg-secondary-800/50 rounded-lg border border-secondary-700">
            <div className="flex items-center gap-3">
              <FileSpreadsheet className="h-8 w-8 text-primary-400 flex-shrink-0" />
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-secondary-100 truncate">
                  {archivo.nombre_original}
                </p>
                <div className="flex items-center gap-2 text-xs text-secondary-400">
                  <span>v{archivo.version}</span>
                  {archivo.estado !== ESTADO_ARCHIVO.PROCESANDO && archivo.filas_procesadas > 0 && (
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
        )
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
          ) : isMarkingNoAplica ? (
            <div className="flex flex-col items-center gap-2">
              <Loader2 className="h-8 w-8 text-secondary-400 animate-spin" />
              <p className="text-sm text-secondary-300">Marcando como "No Aplica"...</p>
            </div>
          ) : (
            <div className="flex flex-col items-center gap-3">
              <Upload className={cn(
                "h-8 w-8 transition-colors",
                isDragging ? "text-primary-400" : "text-secondary-500"
              )} />
              <div className="text-center">
                <p className="text-sm text-secondary-300">
                  {isDragging ? 'Suelta el archivo aquí' : 'Arrastra un archivo o haz clic para seleccionar'}
                </p>
                <p className="text-xs text-secondary-500 mt-1">
                  Formatos: {FORMATOS_PERMITIDOS.join(', ')}
                </p>
              </div>
              {/* Botón "No hay este mes" solo para archivos del analista */}
              {categoria === 'analista' && onNoAplica && (
                <button
                  onClick={(e) => {
                    e.stopPropagation()
                    onNoAplica(tipo)
                  }}
                  className="mt-2 px-3 py-1.5 text-xs text-secondary-400 hover:text-secondary-200 bg-secondary-800 hover:bg-secondary-700 rounded-lg border border-secondary-700 transition-colors"
                >
                  No hay este mes
                </button>
              )}
            </div>
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

export default DropZone
