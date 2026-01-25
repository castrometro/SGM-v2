/**
 * Sección que contiene todas las tarjetas de archivos del analista/cliente
 */
import { File } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '../../../../components/ui'
import ArchivoAnalistaCard from './ArchivoAnalistaCard'
import { TIPOS_ANALISTA } from '../../hooks/useArchivos'
import { ESTADO_ARCHIVO_LIBRO } from '../../../../constants'

/**
 * @param {Object} props
 * @param {Object} props.archivosAnalista - Objeto con archivos del analista por tipo
 * @param {Object} props.libroERP - Archivo del libro de remuneraciones (para validar habilitación de novedades)
 * @param {Object} props.uploadingAnalista - Estado de subida por tipo
 * @param {Object} props.progressAnalista - Progreso de subida por tipo
 * @param {Object} props.markingNoAplica - Estado de marcado "No Aplica" por tipo
 * @param {Function} props.onUpload - Callback cuando se sube un archivo
 * @param {Function} props.onDelete - Callback cuando se elimina un archivo
 * @param {Function} props.onMapeo - Callback para abrir modal de mapeo de novedades
 * @param {Function} props.onNoAplica - Callback para marcar como "No Aplica"
 * @param {Function} props.onDesmarcarNoAplica - Callback para desmarcar "No Aplica"
 */
const ArchivosAnalistaSection = ({
  archivosAnalista,
  libroERP,
  uploadingAnalista,
  progressAnalista,
  markingNoAplica,
  onUpload,
  onDelete,
  onMapeo,
  onNoAplica,
  onDesmarcarNoAplica
}) => {
  // Libro procesado para habilitar novedades
  const libroOk = libroERP?.estado === ESTADO_ARCHIVO_LIBRO.PROCESADO

  return (
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
          <ArchivoAnalistaCard
            key={tipo.value}
            tipoConfig={tipo}
            archivo={archivosAnalista?.[tipo.value]}
            onUpload={onUpload}
            onDelete={onDelete}
            isUploading={uploadingAnalista[tipo.value]}
            progress={progressAnalista[tipo.value] || 0}
            onClasificar={onMapeo}
            disabled={tipo.value === 'novedades' && !libroOk}
            disabledMessage="Primero procesa el Libro de Remuneraciones"
            onNoAplica={onNoAplica}
            onDesmarcarNoAplica={onDesmarcarNoAplica}
            isMarkingNoAplica={markingNoAplica[tipo.value]}
          />
        ))}
      </CardContent>
    </Card>
  )
}

export default ArchivosAnalistaSection
