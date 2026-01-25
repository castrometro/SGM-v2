/**
 * Tarjeta para un archivo del analista/cliente
 * Wrapper sobre DropZone con soporte para "No Aplica"
 */
import DropZone from './DropZone'

/**
 * @param {Object} props
 * @param {Object} props.tipoConfig - Configuración del tipo de archivo {value, label, descripcion}
 * @param {Object} props.archivo - Datos del archivo existente (si hay)
 * @param {Function} props.onUpload - Callback cuando se sube un archivo
 * @param {Function} props.onDelete - Callback cuando se elimina un archivo
 * @param {boolean} props.isUploading - Si está subiendo actualmente
 * @param {number} props.progress - Progreso de subida (0-100)
 * @param {Function} [props.onClasificar] - Callback para abrir modal de mapeo
 * @param {boolean} [props.disabled] - Si la zona está deshabilitada
 * @param {string} [props.disabledMessage] - Mensaje cuando está deshabilitada
 * @param {Function} [props.onNoAplica] - Callback para marcar como "No Aplica"
 * @param {Function} [props.onDesmarcarNoAplica] - Callback para desmarcar "No Aplica"
 * @param {boolean} [props.isMarkingNoAplica] - Si está procesando el marcado
 */
const ArchivoAnalistaCard = ({ 
  tipoConfig, 
  archivo, 
  onUpload, 
  onDelete, 
  isUploading, 
  progress,
  onClasificar,
  disabled,
  disabledMessage,
  onNoAplica,
  onDesmarcarNoAplica,
  isMarkingNoAplica
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
      categoria="analista"
      onClasificar={tipoConfig.value === 'novedades' ? onClasificar : undefined}
      disabled={disabled}
      disabledMessage={disabledMessage}
      onNoAplica={onNoAplica}
      onDesmarcarNoAplica={onDesmarcarNoAplica}
      isMarkingNoAplica={isMarkingNoAplica}
    />
  )
}

export default ArchivoAnalistaCard
