/**
 * Sección que contiene todas las tarjetas de archivos ERP
 */
import { FileSpreadsheet, Database } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '../../../../components/ui'
import Badge from '../../../../components/ui/Badge'
import ArchivoERPCard from './ArchivoERPCard'
import { TIPOS_ERP } from '../../hooks/useArchivos'

/**
 * @param {Object} props
 * @param {Object} props.archivosERP - Objeto con archivos ERP existentes por tipo
 * @param {Object} props.cierre - Datos del cierre (para mostrar info del ERP)
 * @param {Object} props.uploadingERP - Estado de subida por tipo
 * @param {Object} props.progressERP - Progreso de subida por tipo
 * @param {Function} props.onUpload - Callback cuando se sube un archivo
 * @param {Function} props.onDelete - Callback cuando se elimina un archivo
 * @param {Function} props.onClasificar - Callback para abrir modal de clasificación
 */
const ArchivosERPSection = ({
  archivosERP,
  cierre,
  uploadingERP,
  progressERP,
  onUpload,
  onDelete,
  onClasificar
}) => {
  return (
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
          <ArchivoERPCard
            key={tipo.value}
            tipoConfig={tipo}
            archivo={archivosERP?.[tipo.value]}
            onUpload={onUpload}
            onDelete={onDelete}
            isUploading={uploadingERP[tipo.value]}
            progress={progressERP[tipo.value] || 0}
            onClasificar={onClasificar}
          />
        ))}
      </CardContent>
    </Card>
  )
}

export default ArchivosERPSection
