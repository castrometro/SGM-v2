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
import { Loader2, Check, AlertCircle, Users } from 'lucide-react'
import { cn } from '../../../../utils/cn'
import { useProgresoLibro } from '../../hooks/useArchivos'

/**
 * @param {Object} props
 * @param {number} props.archivoId - ID del archivo del libro
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

export default ProgresoProcesamientoLibro
