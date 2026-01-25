/**
 * Exportaciones de hooks del validador
 */
export {
  useArchivosERP,
  useArchivosAnalista,
  useUploadArchivoERP,
  useUploadArchivoAnalista,
  useDeleteArchivoERP,
  useDeleteArchivoAnalista,
  useProgresoLibro,
  useMarcarNoAplica,
  useDesmarcarNoAplica,
  useConfirmarArchivosListos,
  TIPOS_ERP,
  TIPOS_ANALISTA,
} from './useArchivos'

export {
  useGenerarDiscrepancias,
  useDiscrepancias,
  useResumenDiscrepancias,
  useResolverDiscrepancia,
  TIPOS_DISCREPANCIA,
  ORIGENES_DISCREPANCIA,
  getTipoDiscrepanciaInfo,
  getOrigenDiscrepanciaInfo,
} from './useDiscrepancias'
