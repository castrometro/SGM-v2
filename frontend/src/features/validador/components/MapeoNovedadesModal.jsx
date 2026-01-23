/**
 * Modal de Mapeo de Conceptos de Novedades
 * 
 * Diseño similar al ClasificacionLibroModal:
 * - Layout 2 columnas
 * - Panel izquierdo: conceptos pendientes de mapear
 * - Panel derecho: conceptos del libro agrupados por categoría (drop zones)
 * - Selección múltiple y drag & drop
 */
import { useState, useEffect, useMemo, useCallback } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { 
  Loader2, 
  AlertCircle,
  Check,
  Search,
  Tag,
  GripVertical,
  CheckSquare,
  Square,
  ChevronDown,
  ChevronRight,
  Link2Off,
  MousePointerClick,
  Ban,
  X,
  ArrowRight,
  Edit3,
  List,
  PlayCircle
} from 'lucide-react'
import Modal from '../../../components/ui/Modal'
import Button from '../../../components/ui/Button'
import Badge from '../../../components/ui/Badge'
import { Card, CardContent } from '../../../components/ui'
import api from '../../../api/axios'
import { cn } from '../../../utils/cn'
import { CATEGORIA_CONCEPTO_LIBRO, ESTADO_ARCHIVO_NOVEDADES, puedeProcesarNovedades } from '../../../constants'

// Colores para cada categoría (igual que ClasificacionLibroV2)
const CATEGORIA_COLORS = {
  haberes_imponibles: { bg: 'bg-emerald-500/20', border: 'border-emerald-500/50', text: 'text-emerald-400', badge: 'success' },
  haberes_no_imponibles: { bg: 'bg-teal-500/20', border: 'border-teal-500/50', text: 'text-teal-400', badge: 'info' },
  descuentos_legales: { bg: 'bg-red-500/20', border: 'border-red-500/50', text: 'text-red-400', badge: 'danger' },
  otros_descuentos: { bg: 'bg-orange-500/20', border: 'border-orange-500/50', text: 'text-orange-400', badge: 'warning' },
  aportes_patronales: { bg: 'bg-purple-500/20', border: 'border-purple-500/50', text: 'text-purple-400', badge: 'primary' },
  info_adicional: { bg: 'bg-blue-500/20', border: 'border-blue-500/50', text: 'text-blue-400', badge: 'info' },
}

/**
 * Hook para obtener los conceptos de novedades sin mapear
 */
const useConceptosNovedadesSinMapear = (clienteId, erpId, options = {}) => {
  return useQuery({
    queryKey: ['conceptos-novedades-sin-mapear', clienteId, erpId],
    queryFn: async () => {
      const { data } = await api.get('/v1/validador/mapeos/sin_mapear/', {
        params: { cliente_id: clienteId, erp_id: erpId }
      })
      return data
    },
    enabled: !!clienteId,
    ...options
  })
}

/**
 * Hook para obtener los conceptos de novedades ya mapeados
 */
const useConceptosNovedadesMapeados = (clienteId, erpId, options = {}) => {
  return useQuery({
    queryKey: ['conceptos-novedades-mapeados', clienteId, erpId],
    queryFn: async () => {
      const { data } = await api.get('/v1/validador/mapeos/mapeados/', {
        params: { cliente_id: clienteId, erp_id: erpId }
      })
      return data
    },
    enabled: !!clienteId,
    ...options
  })
}

/**
 * Hook para obtener los conceptos del libro disponibles para mapeo
 */
const useConceptosLibro = (clienteId, erpId, options = {}) => {
  return useQuery({
    queryKey: ['conceptos-libro-mapeo', clienteId, erpId],
    queryFn: async () => {
      const { data } = await api.get('/v1/validador/mapeos/conceptos_libro/', {
        params: { cliente_id: clienteId, erp_id: erpId }
      })
      return data
    },
    enabled: !!clienteId,
    ...options
  })
}

/**
 * Componente de concepto de novedades (panel izquierdo)
 */
const ConceptoNovedadCard = ({ 
  concepto, 
  isSelected, 
  onSelect, 
  onDragStart,
  onDragEnd,
  isDragging,
}) => {
  return (
    <div
      draggable
      onDragStart={(e) => onDragStart(e, [concepto])}
      onDragEnd={onDragEnd}
      className={cn(
        "group flex items-center gap-2 p-2 rounded-lg border transition-all cursor-grab active:cursor-grabbing",
        isDragging && "opacity-50",
        isSelected 
          ? "border-primary-500 bg-primary-500/10" 
          : "border-secondary-700 bg-secondary-800/50 hover:border-secondary-600 hover:bg-secondary-800"
      )}
    >
      <GripVertical className="h-4 w-4 text-secondary-600 group-hover:text-secondary-400 flex-shrink-0" />
      
      <button
        onClick={(e) => {
          e.stopPropagation()
          onSelect(concepto)
        }}
        className="flex-shrink-0"
      >
        {isSelected ? (
          <CheckSquare className="h-4 w-4 text-primary-400" />
        ) : (
          <Square className="h-4 w-4 text-secondary-500 hover:text-secondary-300" />
        )}
      </button>

      <div className="flex-1 min-w-0">
        <p className="text-sm text-secondary-200 truncate">{concepto.header_original}</p>
        <p className="text-xs text-secondary-500">Columna {concepto.orden}</p>
      </div>
    </div>
  )
}

/**
 * Item individual del libro (drop target)
 */
const ConceptoLibroItem = ({ 
  concepto, 
  isSelected,
  isDragOver,
  isUsado,
  onSelect,
  onDragOver,
  onDragLeave,
  onDrop
}) => {
  // Si está usado, no permitir interacción
  if (isUsado) {
    return (
      <div className="w-full text-left px-2 py-1.5 rounded text-sm border border-transparent opacity-40 cursor-not-allowed line-through text-secondary-500">
        {concepto.header_original}
      </div>
    )
  }

  return (
    <div
      onDragOver={(e) => onDragOver(e, concepto)}
      onDragLeave={onDragLeave}
      onDrop={(e) => onDrop(e, concepto)}
      onClick={() => onSelect(concepto)}
      className={cn(
        "w-full text-left px-2 py-1.5 rounded text-sm transition-all cursor-pointer border",
        isDragOver 
          ? "bg-primary-500/30 border-primary-500 text-primary-200"
          : isSelected
            ? "bg-primary-500/20 border-primary-500/50 text-primary-300"
            : "hover:bg-secondary-700 text-secondary-300 border-transparent"
      )}
    >
      {concepto.header_original}
    </div>
  )
}

/**
 * Componente de categoría con conceptos del libro (panel derecho)
 */
const CategoriaGroup = ({ 
  categoria, 
  label, 
  conceptos,
  conceptosUsados,
  isExpanded,
  onToggleExpand,
  onSelectConcepto,
  selectedConceptoLibro,
  dragOverConcepto,
  onDragOver,
  onDragLeave,
  onDrop
}) => {
  const colors = CATEGORIA_COLORS[categoria] || CATEGORIA_COLORS.info_adicional
  const disponibles = conceptos.filter(c => !conceptosUsados.has(c.id)).length

  return (
    <div className="rounded-lg border border-secondary-700">
      <button
        onClick={onToggleExpand}
        className="w-full flex items-center justify-between p-3 text-left hover:bg-secondary-800/50 rounded-t-lg"
      >
        <div className="flex items-center gap-2">
          {isExpanded ? (
            <ChevronDown className={cn("h-4 w-4", colors.text)} />
          ) : (
            <ChevronRight className={cn("h-4 w-4", colors.text)} />
          )}
          <span className={cn("font-medium text-sm", colors.text)}>{label}</span>
          <Badge variant={colors.badge} size="sm">{disponibles}/{conceptos.length}</Badge>
        </div>
      </button>

      {isExpanded && conceptos.length > 0 && (
        <div className="px-3 pb-3 space-y-1 max-h-[200px] overflow-y-auto">
          {conceptos.map(concepto => (
            <ConceptoLibroItem
              key={concepto.id}
              concepto={concepto}
              isSelected={selectedConceptoLibro?.id === concepto.id}
              isDragOver={dragOverConcepto?.id === concepto.id}
              isUsado={conceptosUsados.has(concepto.id)}
              onSelect={onSelectConcepto}
              onDragOver={onDragOver}
              onDragLeave={onDragLeave}
              onDrop={onDrop}
            />
          ))}
        </div>
      )}

      {isExpanded && conceptos.length === 0 && (
        <p className="px-3 pb-3 text-xs text-secondary-500 italic">
          Sin conceptos en esta categoría
        </p>
      )}
    </div>
  )
}

/**
 * Componente para mostrar un mapeo existente
 */
const MapeoExistenteItem = ({ 
  item, 
  isSelected,
  onSelect,
  onDesmapear
}) => {
  const colors = item.concepto_libro 
    ? CATEGORIA_COLORS[item.concepto_libro.categoria] || CATEGORIA_COLORS.info_adicional
    : null

  return (
    <div
      className={cn(
        "flex items-center gap-2 p-2 rounded-lg border transition-all",
        isSelected 
          ? "border-primary-500 bg-primary-500/10" 
          : "border-secondary-700 bg-secondary-800/50"
      )}
    >
      <button
        onClick={() => onSelect(item)}
        className="flex-shrink-0"
      >
        {isSelected ? (
          <CheckSquare className="h-4 w-4 text-primary-400" />
        ) : (
          <Square className="h-4 w-4 text-secondary-500 hover:text-secondary-300" />
        )}
      </button>

      <div className="flex-1 min-w-0 flex items-center gap-2">
        <span className="text-sm text-secondary-200 truncate">{item.header_original}</span>
        <ArrowRight className="h-3 w-3 text-secondary-500 flex-shrink-0" />
        {item.sin_asignacion ? (
          <Badge variant="warning" size="sm" className="flex-shrink-0">
            <Ban className="h-3 w-3 mr-1" />
            Sin asignación
          </Badge>
        ) : item.concepto_libro ? (
          <Badge variant={colors?.badge || 'secondary'} size="sm" className="truncate">
            {item.concepto_libro.header_original}
          </Badge>
        ) : null}
      </div>

      <button
        onClick={() => onDesmapear(item)}
        className="p-1 text-secondary-500 hover:text-red-400 transition-colors"
        title="Quitar mapeo"
      >
        <X className="h-4 w-4" />
      </button>
    </div>
  )
}

/**
 * Modal principal de mapeo
 */
const MapeoNovedadesModal = ({ 
  isOpen, 
  onClose, 
  archivo, 
  cierreId,
  clienteId,
  erpId,
  onMapeoComplete
}) => {
  const queryClient = useQueryClient()
  
  // Estado local
  const [activeTab, setActiveTab] = useState('pendientes') // 'pendientes' | 'mapeados'
  const [selectedItems, setSelectedItems] = useState(new Set())
  const [selectedMapeados, setSelectedMapeados] = useState(new Set())
  const [selectedConceptoLibro, setSelectedConceptoLibro] = useState(null)
  const [busqueda, setBusqueda] = useState('')
  const [busquedaLibro, setBusquedaLibro] = useState('')
  const [busquedaMapeados, setBusquedaMapeados] = useState('')
  const [expandedCategories, setExpandedCategories] = useState(new Set(['haberes_imponibles', 'descuentos_legales']))
  const [mapeosPendientes, setMapeosPendientes] = useState({}) // { conceptoNovedadesId: conceptoLibroId | 'sin_asignacion' }
  const [draggedItems, setDraggedItems] = useState([])
  const [dragOverConcepto, setDragOverConcepto] = useState(null)

  // Queries
  const { data: conceptosSinMapear, isLoading: loadingConceptos } = useConceptosNovedadesSinMapear(
    clienteId, erpId, { enabled: isOpen && !!clienteId }
  )
  
  const { data: conceptosMapeados, isLoading: loadingMapeados } = useConceptosNovedadesMapeados(
    clienteId, erpId, { enabled: isOpen && !!clienteId }
  )
  
  const { data: conceptosLibro, isLoading: loadingLibro } = useConceptosLibro(
    clienteId, erpId, { enabled: isOpen && !!clienteId }
  )

  // Mutation para guardar
  const guardarMutation = useMutation({
    mutationFn: async (mapeosData) => {
      const { data } = await api.post('/v1/validador/mapeos/mapear_batch/', mapeosData)
      return data
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries(['conceptos-novedades-sin-mapear', clienteId])
      queryClient.invalidateQueries(['conceptos-novedades-mapeados', clienteId])
      queryClient.invalidateQueries(['conceptos-libro-mapeo', clienteId, erpId])
      queryClient.invalidateQueries(['archivos-analista', cierreId])
      queryClient.invalidateQueries(['cierre', cierreId])
      
      setMapeosPendientes({})
      setSelectedItems(new Set())
      setSelectedConceptoLibro(null)
      
      if (onMapeoComplete) onMapeoComplete(data)
      if (data.sin_mapear === 0) onClose()
    }
  })

  // Mutation para desmapear
  const desmapearMutation = useMutation({
    mutationFn: async (conceptoIds) => {
      const { data } = await api.post('/v1/validador/mapeos/desmapear/', {
        concepto_ids: conceptoIds,
        archivo_id: archivo?.id
      })
      return data
    },
    onSuccess: () => {
      queryClient.invalidateQueries(['conceptos-novedades-sin-mapear', clienteId])
      queryClient.invalidateQueries(['conceptos-novedades-mapeados', clienteId])
      queryClient.invalidateQueries(['conceptos-libro-mapeo', clienteId, erpId])
      queryClient.invalidateQueries(['archivos-analista', cierreId])
      queryClient.invalidateQueries(['cierre', cierreId])
      
      setSelectedMapeados(new Set())
    }
  })

  // Mutation para procesar novedades
  const procesarMutation = useMutation({
    mutationFn: async () => {
      const { data } = await api.post(`/v1/validador/archivos-analista/${archivo.id}/procesar/`)
      return data
    },
    onSuccess: () => {
      queryClient.invalidateQueries(['archivos-analista', cierreId])
      queryClient.invalidateQueries(['cierre', cierreId])
      if (onMapeoComplete) onMapeoComplete()
      onClose()
    }
  })

  // Reset al abrir
  useEffect(() => {
    if (isOpen) {
      setActiveTab('pendientes')
      setSelectedItems(new Set())
      setSelectedMapeados(new Set())
      setSelectedConceptoLibro(null)
      setBusqueda('')
      setBusquedaLibro('')
      setBusquedaMapeados('')
      setMapeosPendientes({})
    }
  }, [isOpen])

  // Datos procesados
  const conceptosSinMapearList = conceptosSinMapear?.items || []
  const conceptosMapeadosList = conceptosMapeados?.items || []
  const conceptosLibroList = conceptosLibro?.conceptos || []
  
  // Set de conceptos del libro ya usados (del backend + pendientes en esta sesión)
  const conceptosUsados = useMemo(() => {
    const usados = new Set(
      conceptosLibroList.filter(c => c.usado).map(c => c.id)
    )
    // Agregar los que se mapearon en esta sesión
    Object.values(mapeosPendientes).forEach(val => {
      if (val !== 'sin_asignacion') usados.add(val)
    })
    return usados
  }, [conceptosLibroList, mapeosPendientes])
  
  // Filtrar por búsqueda y excluir los ya mapeados en esta sesión
  const conceptosFiltrados = useMemo(() => {
    return conceptosSinMapearList
      .filter(c => !mapeosPendientes[c.id])
      .filter(c => 
        !busqueda || c.header_original.toLowerCase().includes(busqueda.toLowerCase())
      )
  }, [conceptosSinMapearList, busqueda, mapeosPendientes])

  // Filtrar mapeados por búsqueda
  const mapeadosFiltrados = useMemo(() => {
    return conceptosMapeadosList.filter(c => 
      !busquedaMapeados || 
      c.header_original.toLowerCase().includes(busquedaMapeados.toLowerCase()) ||
      (c.concepto_libro?.header_original?.toLowerCase().includes(busquedaMapeados.toLowerCase()))
    )
  }, [conceptosMapeadosList, busquedaMapeados])

  // Agrupar conceptos del libro por categoría (con filtro de búsqueda)
  const conceptosPorCategoria = useMemo(() => {
    const grupos = {}
    Object.keys(CATEGORIA_CONCEPTO_LIBRO).forEach(cat => {
      grupos[cat] = []
    })
    conceptosLibroList.forEach(concepto => {
      const cat = concepto.categoria || 'info_adicional'
      // Filtrar por búsqueda
      if (busquedaLibro && !concepto.header_original.toLowerCase().includes(busquedaLibro.toLowerCase())) {
        return
      }
      if (grupos[cat]) grupos[cat].push(concepto)
    })
    return grupos
  }, [conceptosLibroList, busquedaLibro])

  // Handlers de selección
  const handleSelect = useCallback((concepto) => {
    setSelectedItems(prev => {
      const newSet = new Set(prev)
      if (newSet.has(concepto.id)) {
        newSet.delete(concepto.id)
      } else {
        newSet.add(concepto.id)
      }
      return newSet
    })
  }, [])

  const handleSelectAll = useCallback(() => {
    if (selectedItems.size === conceptosFiltrados.length) {
      setSelectedItems(new Set())
    } else {
      setSelectedItems(new Set(conceptosFiltrados.map(c => c.id)))
    }
  }, [conceptosFiltrados, selectedItems.size])

  // Handlers para mapeos existentes
  const handleSelectMapeado = useCallback((item) => {
    setSelectedMapeados(prev => {
      const newSet = new Set(prev)
      if (newSet.has(item.id)) {
        newSet.delete(item.id)
      } else {
        newSet.add(item.id)
      }
      return newSet
    })
  }, [])

  const handleSelectAllMapeados = useCallback(() => {
    if (selectedMapeados.size === mapeadosFiltrados.length) {
      setSelectedMapeados(new Set())
    } else {
      setSelectedMapeados(new Set(mapeadosFiltrados.map(c => c.id)))
    }
  }, [mapeadosFiltrados, selectedMapeados.size])

  const handleDesmapear = useCallback((item) => {
    desmapearMutation.mutate([item.id])
  }, [desmapearMutation])

  const handleDesmapearSeleccionados = useCallback(() => {
    if (selectedMapeados.size === 0) return
    desmapearMutation.mutate(Array.from(selectedMapeados))
  }, [selectedMapeados, desmapearMutation])

  const handleDragEnd = useCallback(() => {
    setDraggedItems([])
    setDragOverConcepto(null)
  }, [])

  // Handlers de drag & drop
  const handleDragStart = useCallback((e, items) => {
    setDraggedItems(items)
    e.dataTransfer.effectAllowed = 'move'
  }, [])

  const handleDragOver = useCallback((e, conceptoLibro) => {
    e.preventDefault()
    setDragOverConcepto(conceptoLibro)
  }, [])

  const handleDragLeave = useCallback(() => {
    setDragOverConcepto(null)
  }, [])

  const handleDrop = useCallback((e, conceptoLibro) => {
    e.preventDefault()
    setDragOverConcepto(null)
    
    if (draggedItems.length > 0 && conceptoLibro) {
      // Mapear items arrastrados al concepto del libro
      const newMapeos = { ...mapeosPendientes }
      draggedItems.forEach(item => {
        newMapeos[item.id] = conceptoLibro.id
      })
      setMapeosPendientes(newMapeos)
      setSelectedItems(new Set())
    }
    setDraggedItems([])
  }, [draggedItems, mapeosPendientes])

  // Mapear seleccionados al concepto del libro seleccionado
  const handleMapearSeleccionados = useCallback(() => {
    if (selectedItems.size === 0 || !selectedConceptoLibro) return
    
    const newMapeos = { ...mapeosPendientes }
    selectedItems.forEach(id => {
      newMapeos[id] = selectedConceptoLibro.id
    })
    setMapeosPendientes(newMapeos)
    setSelectedItems(new Set())
    setSelectedConceptoLibro(null)
  }, [selectedItems, selectedConceptoLibro, mapeosPendientes])

  // Marcar seleccionados como "sin asignación"
  const handleMarcarSinAsignacion = useCallback(() => {
    if (selectedItems.size === 0) return
    
    const newMapeos = { ...mapeosPendientes }
    selectedItems.forEach(id => {
      newMapeos[id] = 'sin_asignacion'
    })
    setMapeosPendientes(newMapeos)
    setSelectedItems(new Set())
  }, [selectedItems, mapeosPendientes])

  // Guardar todos los mapeos
  const handleGuardar = () => {
    const mapeosArray = Object.entries(mapeosPendientes).map(([id, valor]) => {
      if (valor === 'sin_asignacion') {
        return { concepto_novedades_id: parseInt(id), sin_asignacion: true }
      }
      return { concepto_novedades_id: parseInt(id), concepto_libro_id: valor }
    })
    
    guardarMutation.mutate({ 
      mapeos: mapeosArray,
      archivo_id: archivo?.id 
    })
  }

  // Toggle categoría expandida
  const handleToggleCategory = (categoria) => {
    setExpandedCategories(prev => {
      const newSet = new Set(prev)
      if (newSet.has(categoria)) {
        newSet.delete(categoria)
      } else {
        newSet.add(categoria)
      }
      return newSet
    })
  }

  if (!clienteId) return null
  
  const isLoading = loadingConceptos || loadingLibro || loadingMapeados
  const hayMapeosPendientes = Object.keys(mapeosPendientes).length > 0
  const pendientesCount = conceptosSinMapearList.length
  const mapeadosCount = conceptosMapeadosList.length
  
  // Determinar si se puede procesar: archivo en estado LISTO y sin pendientes
  const puedeProcesar = archivo && 
    puedeProcesarNovedades(archivo.estado) && 
    pendientesCount === 0 && 
    !hayMapeosPendientes

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Mapeo de Conceptos de Novedades"
      size="full"
    >
      <div className="max-h-[75vh] overflow-y-auto -mx-6 px-6">
        {/* Loading */}
        {isLoading && (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="h-8 w-8 text-primary-500 animate-spin" />
            <span className="ml-3 text-secondary-400">Cargando datos...</span>
          </div>
        )}

        {!isLoading && (
          <>
            {/* Tabs */}
            <div className="flex gap-2 mb-4 border-b border-secondary-700 pb-2">
              <button
                onClick={() => setActiveTab('pendientes')}
                className={cn(
                  "flex items-center gap-2 px-4 py-2 rounded-t-lg text-sm font-medium transition-colors",
                  activeTab === 'pendientes'
                    ? "bg-primary-500/20 text-primary-300 border-b-2 border-primary-500"
                    : "text-secondary-400 hover:text-secondary-200"
                )}
              >
                <Edit3 className="h-4 w-4" />
                Pendientes
                {pendientesCount > 0 && (
                  <Badge variant="warning" size="sm">{pendientesCount}</Badge>
                )}
              </button>
              <button
                onClick={() => setActiveTab('mapeados')}
                className={cn(
                  "flex items-center gap-2 px-4 py-2 rounded-t-lg text-sm font-medium transition-colors",
                  activeTab === 'mapeados'
                    ? "bg-primary-500/20 text-primary-300 border-b-2 border-primary-500"
                    : "text-secondary-400 hover:text-secondary-200"
                )}
              >
                <List className="h-4 w-4" />
                Mapeados
                {mapeadosCount > 0 && (
                  <Badge variant="success" size="sm">{mapeadosCount}</Badge>
                )}
              </button>
            </div>

            {/* Tab: Pendientes */}
            {activeTab === 'pendientes' && (
              <>
                {/* Todos mapeados */}
                {pendientesCount === 0 && (
                  <div className="flex flex-col items-center justify-center py-12">
                    <Check className="h-12 w-12 text-green-400 mb-4" />
                    <p className="text-secondary-300 text-lg">¡Todos los conceptos están mapeados!</p>
                    <p className="text-secondary-500 text-sm mt-2">
                      {puedeProcesar 
                        ? 'Presiona "Procesar Novedades" para continuar'
                        : 'El archivo de novedades está listo para procesar'}
                    </p>
                  </div>
                )}

                {/* Layout principal para mapear */}
                {pendientesCount > 0 && (
                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                    {/* Panel izquierdo: Conceptos de novedades pendientes */}
                    <div className="space-y-3">
                      {/* Tip */}
                      {conceptosFiltrados.length > 0 && selectedItems.size === 0 && (
                        <div className="flex items-center gap-2 p-2 bg-info-500/10 border border-info-500/20 rounded-lg text-xs text-info-300">
                  <MousePointerClick className="h-4 w-4 flex-shrink-0" />
                  <span>
                    <strong>Tip:</strong> Selecciona conceptos de novedades, luego elige un concepto del libro 
                    en el panel derecho y presiona "Asignar".
                  </span>
                </div>
              )}

              {/* Toolbar */}
              <div className="flex items-center gap-2 flex-wrap">
                <div className="relative flex-1 min-w-[200px]">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-secondary-400" />
                  <input
                    type="text"
                    placeholder="Buscar concepto..."
                    value={busqueda}
                    onChange={(e) => setBusqueda(e.target.value)}
                    className="w-full pl-10 pr-4 py-2 bg-secondary-800 border border-secondary-700 rounded-lg text-sm focus:outline-none focus:border-primary-500"
                  />
                </div>
                
                <Button
                  size="sm"
                  variant="secondary"
                  onClick={handleSelectAll}
                  className="flex items-center gap-1"
                >
                  {selectedItems.size === conceptosFiltrados.length && conceptosFiltrados.length > 0 ? (
                    <CheckSquare className="h-4 w-4" />
                  ) : (
                    <Square className="h-4 w-4" />
                  )}
                  Todos
                </Button>
              </div>

              {/* Lista de conceptos */}
              <div className="space-y-2 max-h-[350px] overflow-y-auto pr-1">
                {conceptosFiltrados.length === 0 ? (
                  <div className="text-center py-8">
                    <Check className="h-12 w-12 mx-auto mb-3 text-success-400" />
                    <p className="text-secondary-300">¡Todos los conceptos asignados!</p>
                    <p className="text-secondary-500 text-sm mt-1">Guarda los cambios para confirmar</p>
                  </div>
                ) : (
                  conceptosFiltrados.map(concepto => (
                    <ConceptoNovedadCard
                      key={concepto.id}
                      concepto={concepto}
                      isSelected={selectedItems.has(concepto.id)}
                      onSelect={handleSelect}
                      onDragStart={(e) => {
                        const items = selectedItems.has(concepto.id)
                          ? conceptosFiltrados.filter(c => selectedItems.has(c.id))
                          : [concepto]
                        handleDragStart(e, items)
                      }}
                      onDragEnd={handleDragEnd}
                      isDragging={draggedItems.some(d => d.id === concepto.id)}
                    />
                  ))
                )}
              </div>

              {/* Acciones con selección */}
              {selectedItems.size > 0 && (
                <Card className="bg-primary-500/10 border-primary-500/30">
                  <CardContent className="py-3">
                    <p className="text-sm text-primary-300 mb-2">
                      {selectedItems.size} concepto(s) seleccionado(s)
                    </p>
                    <div className="flex flex-wrap gap-2">
                      {selectedConceptoLibro ? (
                        <Button
                          size="sm"
                          variant="primary"
                          onClick={handleMapearSeleccionados}
                          className="flex items-center gap-1"
                        >
                          <Check className="h-4 w-4" />
                          Asignar a "{selectedConceptoLibro.header_original.substring(0, 20)}..."
                        </Button>
                      ) : (
                        <span className="text-xs text-secondary-400">
                          Selecciona un concepto del libro →
                        </span>
                      )}
                      <Button
                        size="sm"
                        variant="secondary"
                        onClick={handleMarcarSinAsignacion}
                        className="flex items-center gap-1 text-warning-400"
                      >
                        <Ban className="h-4 w-4" />
                        Sin asignación
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* Resumen de mapeos pendientes */}
              {hayMapeosPendientes && (
                <div className="bg-green-500/10 border border-green-500/30 rounded-lg p-3">
                  <p className="text-sm text-green-300">
                    <strong>{Object.keys(mapeosPendientes).length}</strong> mapeos listos para guardar
                  </p>
                </div>
              )}
            </div>

            {/* Panel derecho: Conceptos del libro por categoría */}
            <div className="space-y-2">
              <h4 className="text-sm font-medium text-secondary-300 flex items-center gap-2">
                <Tag className="h-4 w-4" />
                Conceptos del Libro (haz clic o arrastra)
              </h4>
              
              {/* Buscador de conceptos del libro */}
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-secondary-400" />
                <input
                  type="text"
                  placeholder="Buscar en libro..."
                  value={busquedaLibro}
                  onChange={(e) => setBusquedaLibro(e.target.value)}
                  className="w-full pl-10 pr-4 py-2 bg-secondary-800 border border-secondary-700 rounded-lg text-sm focus:outline-none focus:border-primary-500"
                />
              </div>
              
              <div className="space-y-2 max-h-[400px] overflow-y-auto pr-1">
                {Object.entries(CATEGORIA_CONCEPTO_LIBRO).map(([value, label]) => (
                  <CategoriaGroup
                    key={value}
                    categoria={value}
                    label={label}
                    conceptos={conceptosPorCategoria[value] || []}
                    conceptosUsados={conceptosUsados}
                    isExpanded={expandedCategories.has(value)}
                    onToggleExpand={() => handleToggleCategory(value)}
                    onSelectConcepto={setSelectedConceptoLibro}
                    selectedConceptoLibro={selectedConceptoLibro}
                    dragOverConcepto={dragOverConcepto}
                    onDragOver={handleDragOver}
                    onDragLeave={handleDragLeave}
                    onDrop={handleDrop}
                  />
                ))}
              </div>
            </div>
          </div>
                )}
              </>
            )}

            {/* Tab: Mapeados */}
            {activeTab === 'mapeados' && (
              <div className="space-y-3">
                {mapeadosCount === 0 ? (
                  <div className="flex flex-col items-center justify-center py-12">
                    <Link2Off className="h-12 w-12 text-secondary-500 mb-4" />
                    <p className="text-secondary-300 text-lg">No hay mapeos existentes</p>
                    <p className="text-secondary-500 text-sm mt-2">Los conceptos mapeados aparecerán aquí</p>
                  </div>
                ) : (
                  <>
                    {/* Toolbar */}
                    <div className="flex items-center gap-2 flex-wrap">
                      <div className="relative flex-1 min-w-[200px]">
                        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-secondary-400" />
                        <input
                          type="text"
                          placeholder="Buscar mapeo..."
                          value={busquedaMapeados}
                          onChange={(e) => setBusquedaMapeados(e.target.value)}
                          className="w-full pl-10 pr-4 py-2 bg-secondary-800 border border-secondary-700 rounded-lg text-sm focus:outline-none focus:border-primary-500"
                        />
                      </div>
                      
                      <Button
                        size="sm"
                        variant="secondary"
                        onClick={handleSelectAllMapeados}
                        className="flex items-center gap-1"
                      >
                        {selectedMapeados.size === mapeadosFiltrados.length && mapeadosFiltrados.length > 0 ? (
                          <CheckSquare className="h-4 w-4" />
                        ) : (
                          <Square className="h-4 w-4" />
                        )}
                        Todos
                      </Button>

                      {selectedMapeados.size > 0 && (
                        <Button
                          size="sm"
                          variant="danger"
                          onClick={handleDesmapearSeleccionados}
                          disabled={desmapearMutation.isPending}
                          className="flex items-center gap-1"
                        >
                          {desmapearMutation.isPending ? (
                            <Loader2 className="h-4 w-4 animate-spin" />
                          ) : (
                            <X className="h-4 w-4" />
                          )}
                          Quitar {selectedMapeados.size} mapeos
                        </Button>
                      )}
                    </div>

                    {/* Lista de mapeos existentes */}
                    <div className="space-y-2 max-h-[450px] overflow-y-auto pr-1">
                      {mapeadosFiltrados.map(item => (
                        <MapeoExistenteItem
                          key={item.id}
                          item={item}
                          isSelected={selectedMapeados.has(item.id)}
                          onSelect={handleSelectMapeado}
                          onDesmapear={handleDesmapear}
                        />
                      ))}
                    </div>

                    {mapeadosFiltrados.length === 0 && busquedaMapeados && (
                      <p className="text-center text-secondary-500 py-4">
                        No se encontraron mapeos con "{busquedaMapeados}"
                      </p>
                    )}
                  </>
                )}
              </div>
            )}
          </>
        )}

        {/* Error */}
        {(guardarMutation.isError || desmapearMutation.isError) && (
          <div className="mt-4 bg-red-900/20 border border-red-500/30 rounded-lg p-3">
            <p className="text-sm text-red-400 flex items-center gap-2">
              <AlertCircle className="h-4 w-4" />
              Error: {guardarMutation.error?.message || desmapearMutation.error?.message || 'Error desconocido'}
            </p>
          </div>
        )}
      </div>

      {/* Footer */}
      <Modal.Footer>
        <Button variant="secondary" onClick={onClose}>
          Cerrar
        </Button>
        
        {hayMapeosPendientes && activeTab === 'pendientes' && (
          <Button
            variant="primary"
            onClick={handleGuardar}
            disabled={guardarMutation.isPending}
            className="flex items-center gap-2"
          >
            {guardarMutation.isPending ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                Guardando...
              </>
            ) : (
              <>
                <Check className="h-4 w-4" />
                Guardar {Object.keys(mapeosPendientes).length} mapeos
              </>
            )}
          </Button>
        )}

        {puedeProcesar && (
          <Button
            variant="primary"
            onClick={() => procesarMutation.mutate()}
            disabled={procesarMutation.isPending}
            className="flex items-center gap-2"
          >
            {procesarMutation.isPending ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                Iniciando procesamiento...
              </>
            ) : (
              <>
                <PlayCircle className="h-4 w-4" />
                Procesar Novedades
              </>
            )}
          </Button>
        )}
      </Modal.Footer>
    </Modal>
  )
}

export default MapeoNovedadesModal
