/**
 * Componente Hub de Carga de Archivos para el Validador de Nómina
 * 
 * Este es el componente principal del estado CARGA_ARCHIVOS.
 * Muestra las dos secciones de archivos:
 * - Archivos del ERP (Libro de Remuneraciones, Movimientos)
 * - Archivos del Cliente (Novedades, Ingresos, Finiquitos, etc.)
 * 
 * @module features/validador/components/CargaArchivos
 */
import { useState, useCallback } from 'react'
import { 
  FileSpreadsheet, 
  File, 
  AlertCircle, 
  Loader2, 
  RefreshCw
} from 'lucide-react'
import { Card, CardContent } from '../../../components/ui'
import Button from '../../../components/ui/Button'
import {
  useArchivosERP,
  useArchivosAnalista,
  useUploadArchivoERP,
  useUploadArchivoAnalista,
  useDeleteArchivoERP,
  useDeleteArchivoAnalista,
  useMarcarNoAplica,
  useDesmarcarNoAplica,
  useConfirmarArchivosListos,
  TIPOS_ERP,
  TIPOS_ANALISTA,
} from '../hooks/useArchivos'
import ClasificacionLibroModal from './ClasificacionLibroModal'
import MapeoNovedadesModal from './MapeoNovedadesModal'
import {
  ArchivosERPSection,
  ArchivosAnalistaSection,
  ChecklistArchivos
} from './carga-archivos'

/**
 * Componente principal de Carga de Archivos (HUB)
 * 
 * @param {Object} props
 * @param {number} props.cierreId - ID del cierre
 * @param {Object} props.cierre - Objeto cierre completo (con cliente_id, cliente_erp, etc.)
 * @param {Function} props.onUpdate - Callback para refrescar datos del cierre
 */
const CargaArchivos = ({ cierreId, cierre, onUpdate }) => {
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

  // Estado para tracking de marcado no aplica
  const [markingNoAplica, setMarkingNoAplica] = useState({})

  // Queries para obtener archivos existentes
  const { data: archivosERP, isLoading: loadingERP, refetch: refetchERP } = useArchivosERP(cierreId)
  const { data: archivosAnalista, isLoading: loadingAnalista, refetch: refetchAnalista } = useArchivosAnalista(cierreId)

  // Mutations
  const uploadERP = useUploadArchivoERP()
  const uploadAnalista = useUploadArchivoAnalista()
  const deleteERP = useDeleteArchivoERP()
  const deleteAnalista = useDeleteArchivoAnalista()
  const marcarNoAplica = useMarcarNoAplica()
  const desmarcarNoAplica = useDesmarcarNoAplica()
  const confirmarArchivosListos = useConfirmarArchivosListos()

  // Archivos específicos
  const libroERP = archivosERP?.libro_remuneraciones

  // Handler para confirmar y continuar
  const handleConfirmarYContinuar = useCallback(() => {
    confirmarArchivosListos.mutate(
      { cierreId },
      {
        onSuccess: () => onUpdate?.(),
        onError: (error) => console.error('Error al confirmar archivos:', error),
      }
    )
  }, [cierreId, confirmarArchivosListos, onUpdate])

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

  // Handlers para "No Aplica"
  const handleNoAplica = useCallback((tipo) => {
    setMarkingNoAplica(prev => ({ ...prev, [tipo]: true }))
    marcarNoAplica.mutate(
      { cierreId, tipo },
      { onSettled: () => setMarkingNoAplica(prev => ({ ...prev, [tipo]: false })) }
    )
  }, [cierreId, marcarNoAplica])

  const handleDesmarcarNoAplica = useCallback((tipo) => {
    desmarcarNoAplica.mutate({ cierreId, tipo })
  }, [cierreId, desmarcarNoAplica])

  // Loading state
  if (loadingERP || loadingAnalista) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-8 w-8 animate-spin text-primary-400" />
      </div>
    )
  }

  // Calcular progreso total
  const uploadedERP = TIPOS_ERP.filter(t => archivosERP?.[t.value]).length
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
                  Archivos ERP: <span className="font-medium text-secondary-100">{uploadedERP}/{TIPOS_ERP.length}</span>
                </span>
              </div>
              <div className="flex items-center gap-2">
                <File className="h-5 w-5 text-green-400" />
                <span className="text-sm text-secondary-300">
                  Archivos Analista: <span className="font-medium text-secondary-100">{uploadedAnalista}/{TIPOS_ANALISTA.length}</span>
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

      {/* Secciones de archivos */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <ArchivosERPSection
          archivosERP={archivosERP}
          cierre={cierre}
          uploadingERP={uploadingERP}
          progressERP={progressERP}
          onUpload={handleUploadERP}
          onDelete={handleDeleteERP}
          onClasificar={handleOpenClasificacion}
        />

        <ArchivosAnalistaSection
          archivosAnalista={archivosAnalista}
          libroERP={libroERP}
          uploadingAnalista={uploadingAnalista}
          progressAnalista={progressAnalista}
          markingNoAplica={markingNoAplica}
          onUpload={handleUploadAnalista}
          onDelete={handleDeleteAnalista}
          onMapeo={handleOpenMapeo}
          onNoAplica={handleNoAplica}
          onDesmarcarNoAplica={handleDesmarcarNoAplica}
        />
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

      {/* Checklist de progreso y botón Continuar */}
      <ChecklistArchivos
        cierre={cierre}
        onContinuar={handleConfirmarYContinuar}
        isPending={confirmarArchivosListos.isPending}
      />

      {/* Modal de Clasificación del Libro */}
      <ClasificacionLibroModal
        isOpen={clasificacionModalOpen}
        onClose={handleCloseClasificacion}
        archivo={archivoParaClasificar}
        cierreId={cierreId}
        onClasificacionComplete={refetchERP}
        onProcesoIniciado={refetchERP}
      />

      {/* Modal de Mapeo de Novedades */}
      <MapeoNovedadesModal
        isOpen={mapeoModalOpen}
        onClose={handleCloseMapeo}
        archivo={archivoParaMapeo}
        cierreId={cierreId}
        clienteId={cierre?.cliente}
        erpId={cierre?.cliente_erp?.id}
        onMapeoComplete={refetchAnalista}
      />
    </div>
  )
}

export default CargaArchivos
