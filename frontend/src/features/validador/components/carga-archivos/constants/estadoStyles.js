/**
 * Estilos y configuración para estados de archivos
 */
import { 
  FileCheck, 
  Loader2, 
  Check, 
  AlertCircle,
  Tag,
  Link2
} from 'lucide-react'

/**
 * Mapeo de estados de archivo a estilos visuales
 * @type {Object.<string, {color: string, icon: Function, label: string, animate?: boolean}>}
 */
export const ESTADO_STYLES = {
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
  // Estado "No Aplica" para archivos del analista
  no_aplica: { color: 'secondary', icon: Check, label: 'No Aplica' },
}

/**
 * Formatos de archivo permitidos para carga
 */
export const FORMATOS_PERMITIDOS = ['.xlsx', '.xls', '.csv']
