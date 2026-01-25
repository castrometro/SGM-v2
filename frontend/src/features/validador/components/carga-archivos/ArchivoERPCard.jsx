/**
 * Tarjeta para un archivo ERP individual
 * Wrapper sobre DropZone con configuración específica para archivos ERP
 */
import DropZone from './DropZone'
import { TIPO_ARCHIVO_ERP } from '../../../../constants'

/**
 * @param {Object} props
 * @param {Object} props.tipoConfig - Configuración del tipo de archivo {value, label, descripcion}
 * @param {Object} props.archivo - Datos del archivo existente (si hay)
 * @param {Function} props.onUpload - Callback cuando se sube un archivo
 * @param {Function} props.onDelete - Callback cuando se elimina un archivo
 * @param {boolean} props.isUploading - Si está subiendo actualmente
 * @param {number} props.progress - Progreso de subida (0-100)
 * @param {Function} [props.onClasificar] - Callback para abrir modal de clasificación
 */
const ArchivoERPCard = ({ 
  tipoConfig, 
  archivo, 
  onUpload, 
  onDelete, 
  isUploading, 
  progress,
  onClasificar 
}) => {
  return (
    <DropZone
      tipo={tipoConfig.value}
      label={tipoConfig.label}
      descripcion={tipoConfig.descripcion}
      archivo={archivo}
      onUpload={(file) => onUpload(tipoConfig.value, file)}
      onDelete={onDelete}
      isUploading={isUploading}
      progress={progress}
      categoria="erp"
      onClasificar={tipoConfig.value === TIPO_ARCHIVO_ERP.LIBRO_REMUNERACIONES ? onClasificar : undefined}
    />
  )
}

export default ArchivoERPCard
