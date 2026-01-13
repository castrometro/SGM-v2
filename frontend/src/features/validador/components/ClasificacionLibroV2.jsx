/**
 * Componente de Clasificación de Headers del Libro de Remuneraciones v2
 * 
 * Features:
 * - Vista en tabs: Pendientes / Clasificados
 * - Selección múltiple para clasificación masiva
 * - Drag & Drop para clasificar arrastrando a categorías
 * - Clasificación automática con sugerencias
 * - Atajos de teclado (Ctrl+A seleccionar todo, Escape deseleccionar)
 */
import { useState, useEffect, useCallback, useMemo } from 'react'
import { 
  BookOpen, 
  Sparkles, 
  Check, 
  AlertCircle, 
  Loader2, 
  Search,
  Tag,
  GripVertical,
  CheckSquare,
  Square,
  ChevronDown,
  Undo2,
  Filter,
  X,
  Keyboard,
  MousePointerClick
} from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '../../../components/ui'
import Badge from '../../../components/ui/Badge'
import Button from '../../../components/ui/Button'
import { cn } from '../../../utils/cn'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import api from '../../../api/axios'
import { CATEGORIA_CONCEPTO_LIBRO } from '../../../constants'

// Colores para cada categoría
const CATEGORIA_COLORS = {
  haberes_imponibles: { bg: 'bg-emerald-500/20', border: 'border-emerald-500/50', text: 'text-emerald-400', badge: 'success' },
  haberes_no_imponibles: { bg: 'bg-teal-500/20', border: 'border-teal-500/50', text: 'text-teal-400', badge: 'info' },
  descuentos_legales: { bg: 'bg-red-500/20', border: 'border-red-500/50', text: 'text-red-400', badge: 'danger' },
  otros_descuentos: { bg: 'bg-orange-500/20', border: 'border-orange-500/50', text: 'text-orange-400', badge: 'warning' },
  aportes_patronales: { bg: 'bg-purple-500/20', border: 'border-purple-500/50', text: 'text-purple-400', badge: 'primary' },
  info_adicional: { bg: 'bg-blue-500/20', border: 'border-blue-500/50', text: 'text-blue-400', badge: 'info' },
  identificador: { bg: 'bg-cyan-500/20', border: 'border-cyan-500/50', text: 'text-cyan-400', badge: 'info' },
  ignorar: { bg: 'bg-gray-500/20', border: 'border-gray-500/50', text: 'text-gray-400', badge: 'secondary' },
}

/**
 * Hook para manejar drag and drop
 */
const useDragAndDrop = (onDrop) => {
  const [draggedItems, setDraggedItems] = useState([])
  const [dragOverCategory, setDragOverCategory] = useState(null)

  const handleDragStart = useCallback((e, items) => {
    setDraggedItems(items)
    e.dataTransfer.effectAllowed = 'move'
    // Para Firefox
    e.dataTransfer.setData('text/plain', JSON.stringify(items.map(i => i.id)))
  }, [])

  const handleDragOver = useCallback((e, categoria) => {
    e.preventDefault()
    e.dataTransfer.dropEffect = 'move'
    setDragOverCategory(categoria)
  }, [])

  const handleDragLeave = useCallback(() => {
    setDragOverCategory(null)
  }, [])

  const handleDrop = useCallback((e, categoria) => {
    e.preventDefault()
    setDragOverCategory(null)
    if (draggedItems.length > 0) {
      onDrop(draggedItems, categoria)
      setDraggedItems([])
    }
  }, [draggedItems, onDrop])

  const handleDragEnd = useCallback(() => {
    setDraggedItems([])
    setDragOverCategory(null)
  }, [])

  return {
    draggedItems,
    dragOverCategory,
    handleDragStart,
    handleDragOver,
    handleDragLeave,
    handleDrop,
    handleDragEnd,
  }
}

/**
 * Componente de concepto arrastrable
 */
const ConceptoCard = ({ 
  concepto, 
  isSelected, 
  onSelect, 
  onDragStart,
  isDragging,
  showSuggestion = true,
  showCategory = false,
  compact = false,
  isMovedFromClassified = false,
  onRestore = null
}) => {
  const colors = concepto.categoria ? CATEGORIA_COLORS[concepto.categoria] : null

  return (
    <div
      draggable
      onDragStart={(e) => onDragStart(e, [concepto])}
      className={cn(
        "group flex items-center gap-2 p-2 rounded-lg border transition-all cursor-grab active:cursor-grabbing",
        isDragging && "opacity-50",
        isSelected 
          ? "border-primary-500 bg-primary-500/10" 
          : isMovedFromClassified
            ? "border-warning-500/50 bg-warning-500/10"
            : "border-secondary-700 bg-secondary-800/50 hover:border-secondary-600 hover:bg-secondary-800",
        compact && "py-1.5"
      )}
    >
      {/* Grip handle */}
      <GripVertical className="h-4 w-4 text-secondary-600 group-hover:text-secondary-400 flex-shrink-0" />
      
      {/* Checkbox */}
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

      {/* Content */}
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <span className={cn(
            "font-medium truncate",
            compact ? "text-sm" : "text-sm",
            isSelected ? "text-primary-200" : "text-secondary-200"
          )}>
            {concepto.header_original}
          </span>
          {concepto.es_duplicado && (
            <Badge color="warning" size="sm">#{concepto.ocurrencia}</Badge>
          )}
          {isMovedFromClassified && (
            <Badge color="warning" size="sm" className="flex items-center gap-1">
              <Undo2 className="h-3 w-3" />
              Reclasificar
            </Badge>
          )}
        </div>
        {!compact && concepto.header_pandas && concepto.header_pandas !== concepto.header_original && (
          <p className="text-xs text-secondary-500 truncate">
            {concepto.header_pandas}
          </p>
        )}
      </div>

      {/* Sugerencia o Categoría actual */}
      {showSuggestion && concepto.sugerencia && !concepto.categoria && (
        <Badge color="info" size="sm" className="flex-shrink-0 flex items-center gap-1">
          <Sparkles className="h-3 w-3" />
          {CATEGORIA_CONCEPTO_LIBRO[concepto.sugerencia.categoria]?.split(' ')[0]}
        </Badge>
      )}
      {showCategory && concepto.categoria && colors && (
        <Badge color={colors.badge} size="sm" className="flex-shrink-0">
          {CATEGORIA_CONCEPTO_LIBRO[concepto.categoria]?.split(' ')[0]}
        </Badge>
      )}
      
      {/* Botón restaurar para conceptos movidos */}
      {isMovedFromClassified && onRestore && (
        <button
          onClick={(e) => {
            e.stopPropagation()
            onRestore(concepto)
          }}
          className="p-1 text-secondary-500 hover:text-success-400 transition-colors flex-shrink-0"
          title="Restaurar clasificación original"
        >
          <Undo2 className="h-4 w-4" />
        </button>
      )}
    </div>
  )
}

/**
 * Categoría como drop zone
 */
const CategoriaDropZone = ({ 
  categoria, 
  label, 
  conceptos = [], 
  isDragOver, 
  onDragOver, 
  onDragLeave, 
  onDrop,
  onRemove,
  isExpanded,
  onToggleExpand
}) => {
  const colors = CATEGORIA_COLORS[categoria]
  const count = conceptos.length

  return (
    <div
      onDragOver={(e) => onDragOver(e, categoria)}
      onDragLeave={onDragLeave}
      onDrop={(e) => onDrop(e, categoria)}
      className={cn(
        "rounded-lg border-2 border-dashed transition-all",
        isDragOver 
          ? `${colors.border} ${colors.bg} scale-[1.02]` 
          : "border-secondary-700 hover:border-secondary-600",
        "p-3"
      )}
    >
      <div 
        className="flex items-center justify-between cursor-pointer"
        onClick={onToggleExpand}
      >
        <div className="flex items-center gap-2">
          <Tag className={cn("h-4 w-4", colors.text)} />
          <span className={cn("font-medium text-sm", colors.text)}>{label}</span>
          <Badge color={colors.badge} size="sm">{count}</Badge>
        </div>
        {count > 0 && (
          <ChevronDown className={cn(
            "h-4 w-4 text-secondary-400 transition-transform",
            isExpanded && "rotate-180"
          )} />
        )}
      </div>

      {/* Lista de conceptos clasificados en esta categoría */}
      {isExpanded && count > 0 && (
        <div className="mt-2 space-y-1 max-h-32 overflow-y-auto">
          {conceptos.map((concepto) => (
            <div 
              key={`${concepto.header_pandas || concepto.header_original}-${concepto.ocurrencia}`}
              className="flex items-center justify-between py-1 px-2 bg-secondary-800/50 rounded text-xs"
            >
              <span className="text-secondary-300 truncate flex-1">
                {concepto.header_original}
                {concepto.es_duplicado && ` #${concepto.ocurrencia}`}
              </span>
              <button
                onClick={(e) => {
                  e.stopPropagation()
                  onRemove(concepto)
                }}
                className="p-1 text-secondary-500 hover:text-red-400 transition-colors"
                title="Quitar clasificación"
              >
                <X className="h-3 w-3" />
              </button>
            </div>
          ))}
        </div>
      )}

      {/* Mensaje cuando está vacío y hay drag */}
      {isDragOver && (
        <p className={cn("text-xs mt-2 text-center", colors.text)}>
          Suelta aquí para clasificar como {label}
        </p>
      )}
    </div>
  )
}

/**
 * Componente principal de clasificación v2
 */
const ClasificacionLibroV2 = ({ archivoId, clienteId, cierreId, onComplete, onAllClassifiedChange }) => {
  // Estados
  const [activeTab, setActiveTab] = useState('pendientes')
  const [busqueda, setBusqueda] = useState('')
  const [selectedItems, setSelectedItems] = useState(new Set())
  const [expandedCategories, setExpandedCategories] = useState(new Set())
  const [pendingChanges, setPendingChanges] = useState({}) // {conceptoKey: categoria}
  const [movedToPending, setMovedToPending] = useState(new Set()) // conceptos clasificados movidos a pendientes para reclasificar
  
  const queryClient = useQueryClient()

  // Query: Headers y conceptos
  const { data: headersData, isLoading: loadingHeaders, error } = useQuery({
    queryKey: ['libro-headers', archivoId],
    queryFn: async () => {
      const { data } = await api.get(`/v1/validador/libro/${archivoId}/headers/`)
      return data
    },
    enabled: !!archivoId,
  })

  // Query: Pendientes con sugerencias
  const { data: pendientesData, isLoading: loadingPendientes } = useQuery({
    queryKey: ['libro-pendientes', archivoId],
    queryFn: async () => {
      const { data } = await api.get(`/v1/validador/libro/${archivoId}/pendientes/`)
      return data
    },
    enabled: !!archivoId,
  })

  // Mutation: Clasificar conceptos
  const clasificarMutation = useMutation({
    mutationFn: async (clasificaciones) => {
      const { data } = await api.post(
        `/v1/validador/libro/${archivoId}/clasificar/`,
        { clasificaciones }
      )
      return data
    },
    onSuccess: () => {
      queryClient.invalidateQueries(['libro-headers', archivoId])
      queryClient.invalidateQueries(['libro-pendientes', archivoId])
      setSelectedItems(new Set())
      setPendingChanges({})
      setMovedToPending(new Set()) // Limpiar conceptos movidos
    },
  })

  // Mutation: Clasificación automática
  const clasificarAutoMutation = useMutation({
    mutationFn: async () => {
      const { data } = await api.post(`/v1/validador/libro/${archivoId}/clasificar-auto/`)
      return data
    },
    onSuccess: () => {
      queryClient.invalidateQueries(['libro-headers', archivoId])
      queryClient.invalidateQueries(['libro-pendientes', archivoId])
    },
  })

  // Datos procesados
  const conceptos = useMemo(() => {
    if (!headersData?.conceptos) return []
    return headersData.conceptos
  }, [headersData])

  const conceptosPendientes = useMemo(() => {
    let result = []
    
    // 1. Conceptos realmente pendientes (sin categoría en BD)
    if (pendientesData?.conceptos) {
      const filtered = pendientesData.conceptos.filter(c => {
        const key = c.header_pandas || c.header_original
        // Excluir los que ya clasificamos localmente
        return !pendingChanges[key]
      })
      result = [...filtered]
    }
    
    // 2. Agregar conceptos clasificados que fueron "movidos a pendientes" para reclasificar
    if (movedToPending.size > 0 && conceptos.length > 0) {
      const movedConceptos = conceptos.filter(c => {
        const key = c.header_pandas || c.header_original
        // Solo incluir si está en movedToPending Y no tiene ya una nueva clasificación pendiente
        return movedToPending.has(key) && !pendingChanges[key]
      }).map(c => ({
        ...c,
        _movedFromClassified: true // Marcador para UI
      }))
      result = [...result, ...movedConceptos]
    }
    
    // 3. Filtrar por búsqueda
    if (busqueda) {
      result = result.filter(c => 
        c.header_original.toLowerCase().includes(busqueda.toLowerCase())
      )
    }
    
    return result
  }, [pendientesData, busqueda, pendingChanges, movedToPending, conceptos])

  const conceptosClasificados = useMemo(() => {
    return conceptos.filter(c => c.categoria || pendingChanges[c.header_pandas || c.header_original])
  }, [conceptos, pendingChanges])

  // Agrupar clasificados por categoría (incluyendo cambios pendientes)
  const conceptosPorCategoria = useMemo(() => {
    const grupos = {}
    Object.keys(CATEGORIA_CONCEPTO_LIBRO).forEach(cat => {
      grupos[cat] = []
    })
    
    // Conceptos ya clasificados en BD (excluyendo los movidos a pendientes)
    conceptosClasificados.forEach(c => {
      const key = c.header_pandas || c.header_original
      // Excluir si está movido a pendientes
      if (movedToPending.has(key)) return
      
      const categoria = pendingChanges[key] || c.categoria
      if (categoria && grupos[categoria]) {
        grupos[categoria].push({ ...c, categoria })
      }
    })
    
    // Agregar conceptos pendientes que hemos clasificado localmente
    Object.entries(pendingChanges).forEach(([key, categoria]) => {
      const yaExiste = grupos[categoria].some(c => (c.header_pandas || c.header_original) === key)
      if (!yaExiste) {
        // Buscar en pendientes originales o en conceptos clasificados que fueron movidos
        const concepto = pendientesData?.conceptos?.find(c => (c.header_pandas || c.header_original) === key)
          || conceptos.find(c => (c.header_pandas || c.header_original) === key)
        if (concepto) {
          grupos[categoria].push({ ...concepto, categoria })
        }
      }
    })
    
    return grupos
  }, [conceptosClasificados, pendingChanges, pendientesData, movedToPending, conceptos])

  // Handlers
  const handleSelect = useCallback((concepto) => {
    const key = concepto.header_pandas || concepto.header_original
    setSelectedItems(prev => {
      const next = new Set(prev)
      if (next.has(key)) {
        next.delete(key)
      } else {
        next.add(key)
      }
      return next
    })
  }, [])

  const handleSelectAll = useCallback(() => {
    if (selectedItems.size === conceptosPendientes.length) {
      setSelectedItems(new Set())
    } else {
      setSelectedItems(new Set(conceptosPendientes.map(c => c.header_pandas || c.header_original)))
    }
  }, [conceptosPendientes, selectedItems])

  const handleDrop = useCallback((items, categoria) => {
    const changes = {}
    items.forEach(item => {
      const key = item.header_pandas || item.header_original
      changes[key] = categoria
    })
    setPendingChanges(prev => ({ ...prev, ...changes }))
    setSelectedItems(new Set())
  }, [])

  // Mover concepto clasificado a pendientes para reclasificar
  const handleMoveToReclassify = useCallback((concepto) => {
    const key = concepto.header_pandas || concepto.header_original
    
    // Si el concepto tiene categoría en BD, agregarlo a movedToPending
    if (concepto.categoria) {
      setMovedToPending(prev => new Set([...prev, key]))
    }
    
    // Si tenía un cambio pendiente, eliminarlo
    setPendingChanges(prev => {
      const next = { ...prev }
      delete next[key]
      return next
    })
  }, [])
  
  // Restaurar concepto movido a su categoría original
  const handleRestoreClassification = useCallback((concepto) => {
    const key = concepto.header_pandas || concepto.header_original
    setMovedToPending(prev => {
      const next = new Set(prev)
      next.delete(key)
      return next
    })
  }, [])

  const handleClassifySelected = useCallback((categoria) => {
    if (selectedItems.size === 0) return
    
    const changes = {}
    selectedItems.forEach(key => {
      changes[key] = categoria
    })
    setPendingChanges(prev => ({ ...prev, ...changes }))
    setSelectedItems(new Set())
  }, [selectedItems])

  const handleApplySuggestions = useCallback(() => {
    if (!pendientesData?.conceptos) return
    
    const changes = {}
    pendientesData.conceptos.forEach(c => {
      if (c.sugerencia) {
        const key = c.header_pandas || c.header_original
        changes[key] = c.sugerencia.categoria
      }
    })
    setPendingChanges(prev => ({ ...prev, ...changes }))
  }, [pendientesData])

  const handleSaveChanges = useCallback(() => {
    const clasificaciones = Object.entries(pendingChanges).map(([header, categoria]) => {
      const concepto = pendientesData?.conceptos?.find(c => (c.header_pandas || c.header_original) === header)
        || conceptos.find(c => (c.header_pandas || c.header_original) === header)
      return {
        header,
        ocurrencia: concepto?.ocurrencia || 1,
        categoria,
      }
    })
    
    if (clasificaciones.length > 0) {
      clasificarMutation.mutate(clasificaciones)
    }
  }, [pendingChanges, pendientesData, conceptos, clasificarMutation])

  const handleToggleCategory = useCallback((categoria) => {
    setExpandedCategories(prev => {
      const next = new Set(prev)
      if (next.has(categoria)) {
        next.delete(categoria)
      } else {
        next.add(categoria)
      }
      return next
    })
  }, [])

  // Atajos de teclado
  useEffect(() => {
    const handleKeyDown = (e) => {
      // Ctrl/Cmd + A: Seleccionar todo
      if ((e.ctrlKey || e.metaKey) && e.key === 'a' && activeTab === 'pendientes') {
        e.preventDefault()
        handleSelectAll()
      }
      // Escape: Deseleccionar todo
      if (e.key === 'Escape') {
        setSelectedItems(new Set())
      }
      // Ctrl/Cmd + S: Guardar cambios
      if ((e.ctrlKey || e.metaKey) && e.key === 's' && Object.keys(pendingChanges).length > 0) {
        e.preventDefault()
        handleSaveChanges()
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [activeTab, handleSelectAll, handleSaveChanges, pendingChanges])

  // Drag and drop
  const {
    draggedItems,
    dragOverCategory,
    handleDragStart,
    handleDragOver,
    handleDragLeave,
    handleDrop: handleDropEvent,
    handleDragEnd,
  } = useDragAndDrop(handleDrop)

  // Calcular estadísticas
  const stats = useMemo(() => {
    const total = headersData?.headers_total || 0
    // Clasificados = los de BD + cambios pendientes - los movidos a pendientes
    const clasificadosEnBD = headersData?.headers_clasificados || 0
    const nuevasClasificaciones = Object.keys(pendingChanges).length
    const movidosAPendientes = movedToPending.size
    const clasificados = clasificadosEnBD + nuevasClasificaciones - movidosAPendientes
    const pendientes = Math.max(0, total - clasificados)
    const progreso = total > 0 ? Math.round((clasificados / total) * 100) : 0
    const tieneSugerencias = (pendientesData?.conceptos || []).some(c => c.sugerencia && !pendingChanges[c.header_pandas || c.header_original])
    return { total, clasificados, pendientes, progreso, tieneSugerencias }
  }, [headersData, pendientesData, pendingChanges, movedToPending])

  // Notificar al padre cuando cambia el estado de "todos clasificados"
  useEffect(() => {
    if (onAllClassifiedChange) {
      // Solo considerar "todo clasificado" si no hay pendientes Y no hay cambios sin guardar
      const allClassified = stats.pendientes === 0 && Object.keys(pendingChanges).length === 0 && movedToPending.size === 0
      onAllClassifiedChange(allClassified)
    }
  }, [stats.pendientes, pendingChanges, movedToPending, onAllClassifiedChange])

  // Loading
  if (loadingHeaders || loadingPendientes) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="h-8 w-8 animate-spin text-primary-400" />
        <span className="ml-3 text-secondary-300">Cargando conceptos...</span>
      </div>
    )
  }

  // Error
  if (error) {
    return (
      <div className="flex items-center justify-center py-12 text-danger-400">
        <AlertCircle className="h-6 w-6 mr-2" />
        Error al cargar: {error.message}
      </div>
    )
  }

  const hasPendingChanges = Object.keys(pendingChanges).length > 0 || movedToPending.size > 0
  const selectedConceptos = conceptosPendientes.filter(c => selectedItems.has(c.header_pandas || c.header_original))

  return (
    <div className="space-y-4" onDragEnd={handleDragEnd}>
      {/* Header con progreso */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <BookOpen className="h-6 w-6 text-primary-400" />
          <div>
            <h3 className="text-lg font-semibold text-secondary-100">
              Clasificación de Conceptos
            </h3>
            <p className="text-sm text-secondary-400">
              {stats.clasificados} de {stats.total} clasificados
            </p>
          </div>
        </div>
        
        <div className="flex items-center gap-3">
          {/* Progreso circular */}
          <div className="relative h-12 w-12">
            <svg className="h-12 w-12 -rotate-90">
              <circle
                cx="24"
                cy="24"
                r="20"
                stroke="currentColor"
                strokeWidth="4"
                fill="none"
                className="text-secondary-700"
              />
              <circle
                cx="24"
                cy="24"
                r="20"
                stroke="currentColor"
                strokeWidth="4"
                fill="none"
                strokeDasharray={`${stats.progreso * 1.256} 125.6`}
                className="text-primary-500 transition-all duration-500"
              />
            </svg>
            <span className="absolute inset-0 flex items-center justify-center text-sm font-bold text-primary-400">
              {stats.progreso}%
            </span>
          </div>
        </div>
      </div>

      {/* Barra de progreso */}
      <div className="w-full bg-secondary-700 rounded-full h-2">
        <div 
          className="bg-gradient-to-r from-primary-500 to-accent-500 h-2 rounded-full transition-all duration-500"
          style={{ width: `${stats.progreso}%` }}
        />
      </div>

      {/* Tabs */}
      <div className="flex items-center gap-1 p-1 bg-secondary-800 rounded-lg">
        <button
          onClick={() => setActiveTab('pendientes')}
          className={cn(
            "flex-1 px-4 py-2 rounded-md text-sm font-medium transition-all",
            activeTab === 'pendientes'
              ? "bg-primary-500/20 text-primary-300"
              : "text-secondary-400 hover:text-secondary-200"
          )}
        >
          Pendientes ({stats.pendientes})
        </button>
        <button
          onClick={() => setActiveTab('clasificados')}
          className={cn(
            "flex-1 px-4 py-2 rounded-md text-sm font-medium transition-all",
            activeTab === 'clasificados'
              ? "bg-primary-500/20 text-primary-300"
              : "text-secondary-400 hover:text-secondary-200"
          )}
        >
          Clasificados ({stats.clasificados})
        </button>
      </div>

      {/* Contenido según tab */}
      {activeTab === 'pendientes' ? (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {/* Panel izquierdo: Conceptos pendientes */}
          <div className="space-y-3">
            {/* Tip de ayuda */}
            {conceptosPendientes.length > 0 && selectedItems.size === 0 && (
              <div className="flex items-center gap-2 p-2 bg-info-500/10 border border-info-500/20 rounded-lg text-xs text-info-300">
                <MousePointerClick className="h-4 w-4 flex-shrink-0" />
                <span>
                  <strong>Tip:</strong> Selecciona varios conceptos y arrástralos a una categoría, 
                  o usa los botones de categoría que aparecen al seleccionar.
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
                {selectedItems.size === conceptosPendientes.length && conceptosPendientes.length > 0 ? (
                  <CheckSquare className="h-4 w-4" />
                ) : (
                  <Square className="h-4 w-4" />
                )}
                Todos
              </Button>

              {stats.tieneSugerencias && (
                <Button
                  size="sm"
                  variant="primary"
                  onClick={handleApplySuggestions}
                  className="flex items-center gap-1"
                >
                  <Sparkles className="h-4 w-4" />
                  Aplicar Sugerencias
                </Button>
              )}
            </div>

            {/* Lista de conceptos pendientes */}
            <div className="space-y-2 max-h-[400px] overflow-y-auto pr-1">
              {conceptosPendientes.length === 0 ? (
                <div className="text-center py-8">
                  <Check className="h-12 w-12 mx-auto mb-3 text-success-400" />
                  <p className="text-secondary-300">¡Todos los conceptos clasificados!</p>
                </div>
              ) : (
                conceptosPendientes.map((concepto) => {
                  const key = concepto.header_pandas || concepto.header_original
                  const isMovedFromClassified = concepto._movedFromClassified || false
                  return (
                    <ConceptoCard
                      key={`${key}-${concepto.ocurrencia}`}
                      concepto={concepto}
                      isSelected={selectedItems.has(key)}
                      onSelect={handleSelect}
                      onDragStart={(e) => {
                        const items = selectedItems.has(key) 
                          ? selectedConceptos 
                          : [concepto]
                        handleDragStart(e, items)
                      }}
                      isDragging={draggedItems.some(d => (d.header_pandas || d.header_original) === key)}
                      showSuggestion
                      compact
                      isMovedFromClassified={isMovedFromClassified}
                      onRestore={isMovedFromClassified ? handleRestoreClassification : null}
                    />
                  )
                })
              )}
            </div>

            {/* Selección múltiple: acciones */}
            {selectedItems.size > 0 && (
              <Card className="bg-primary-500/10 border-primary-500/30">
                <CardContent className="py-3">
                  <p className="text-sm text-primary-300 mb-2">
                    {selectedItems.size} concepto(s) seleccionado(s)
                  </p>
                  <div className="flex flex-wrap gap-1">
                    {Object.entries(CATEGORIA_CONCEPTO_LIBRO).map(([value, label]) => (
                      <Button
                        key={value}
                        size="sm"
                        variant="secondary"
                        onClick={() => handleClassifySelected(value)}
                        className={cn(
                          "text-xs",
                          CATEGORIA_COLORS[value]?.text
                        )}
                      >
                        {label.split(' ')[0]}
                      </Button>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}
          </div>

          {/* Panel derecho: Categorías (drop zones) */}
          <div className="space-y-2">
            <h4 className="text-sm font-medium text-secondary-300 flex items-center gap-2">
              <Tag className="h-4 w-4" />
              Arrastra conceptos a una categoría
            </h4>
            
            <div className="grid grid-cols-1 gap-2 max-h-[500px] overflow-y-auto pr-1">
              {Object.entries(CATEGORIA_CONCEPTO_LIBRO).map(([value, label]) => (
                <CategoriaDropZone
                  key={value}
                  categoria={value}
                  label={label}
                  conceptos={conceptosPorCategoria[value] || []}
                  isDragOver={dragOverCategory === value}
                  onDragOver={handleDragOver}
                  onDragLeave={handleDragLeave}
                  onDrop={handleDropEvent}
                  onRemove={handleMoveToReclassify}
                  isExpanded={expandedCategories.has(value)}
                  onToggleExpand={() => handleToggleCategory(value)}
                />
              ))}
            </div>
          </div>
        </div>
      ) : (
        /* Tab Clasificados */
        <div className="space-y-3">
          {/* Tip de ayuda */}
          <div className="flex items-center gap-2 p-2 bg-info-500/10 border border-info-500/20 rounded-lg text-xs text-info-300">
            <MousePointerClick className="h-4 w-4 flex-shrink-0" />
            <span>
              <strong>Tip:</strong> Haz clic en el botón <X className="inline h-3 w-3" /> para mover un concepto 
              a "Pendientes" y poder reclasificarlo.
            </span>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {Object.entries(CATEGORIA_CONCEPTO_LIBRO).map(([categoria, label]) => {
              const items = conceptosPorCategoria[categoria] || []
              const colors = CATEGORIA_COLORS[categoria]
              
              if (items.length === 0) return null
              
              return (
                <Card key={categoria} className={cn("border", colors.border)}>
                  <CardHeader className="py-3">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <Tag className={cn("h-4 w-4", colors.text)} />
                        <CardTitle className={cn("text-sm", colors.text)}>
                          {label}
                        </CardTitle>
                      </div>
                      <Badge color={colors.badge}>{items.length}</Badge>
                    </div>
                  </CardHeader>
                  <CardContent className="py-2">
                    <div className="space-y-1 max-h-40 overflow-y-auto">
                      {items.map((concepto) => {
                        const key = concepto.header_pandas || concepto.header_original
                        const isPendingChange = !!pendingChanges[key]
                        
                        return (
                          <div 
                            key={`${key}-${concepto.ocurrencia}`}
                            className={cn(
                              "flex items-center justify-between py-1.5 px-2 rounded text-sm group",
                              isPendingChange 
                                ? "bg-warning-500/10 border border-warning-500/30" 
                                : "bg-secondary-800/50 hover:bg-secondary-800"
                            )}
                          >
                            <span className="text-secondary-200 truncate flex-1">
                              {concepto.header_original}
                              {concepto.es_duplicado && (
                                <span className="text-secondary-500 ml-1">#{concepto.ocurrencia}</span>
                              )}
                              {isPendingChange && (
                                <span className="text-warning-400 ml-2 text-xs">(reclasificado)</span>
                              )}
                            </span>
                            <button
                              onClick={() => handleMoveToReclassify(concepto)}
                              className="p-1 text-secondary-500 opacity-0 group-hover:opacity-100 hover:text-red-400 transition-all"
                              title="Mover a pendientes para reclasificar"
                            >
                              <X className="h-3 w-3" />
                            </button>
                          </div>
                        )
                      })}
                    </div>
                  </CardContent>
                </Card>
              )
            })}
          </div>
        </div>
      )}

      {/* Botones de acción */}
      <div className="flex items-center justify-between pt-4 border-t border-secondary-800">
        <div className="flex items-center gap-4">
          {hasPendingChanges && (
            <span className="text-sm text-warning-400">
              {Object.keys(pendingChanges).length} cambio(s) pendiente(s)
            </span>
          )}
          
          {/* Ayuda de atajos */}
          <div className="hidden md:flex items-center gap-3 text-xs text-secondary-500">
            <span className="flex items-center gap-1">
              <Keyboard className="h-3 w-3" />
              <kbd className="px-1.5 py-0.5 bg-secondary-800 rounded text-secondary-400">Ctrl+A</kbd>
              Seleccionar todo
            </span>
            <span className="flex items-center gap-1">
              <kbd className="px-1.5 py-0.5 bg-secondary-800 rounded text-secondary-400">Esc</kbd>
              Deseleccionar
            </span>
            {hasPendingChanges && (
              <span className="flex items-center gap-1">
                <kbd className="px-1.5 py-0.5 bg-secondary-800 rounded text-secondary-400">Ctrl+S</kbd>
                Guardar
              </span>
            )}
          </div>
        </div>
        
        <div className="flex items-center gap-2">
          {hasPendingChanges && (
            <Button
              variant="secondary"
              onClick={() => {
                setPendingChanges({})
                setMovedToPending(new Set())
              }}
              className="flex items-center gap-2"
            >
              <Undo2 className="h-4 w-4" />
              Descartar
            </Button>
          )}
          
          <Button
            variant="primary"
            onClick={handleSaveChanges}
            disabled={!hasPendingChanges || clasificarMutation.isPending}
            className="flex items-center gap-2"
          >
            {clasificarMutation.isPending ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Check className="h-4 w-4" />
            )}
            Guardar Clasificaciones
          </Button>
        </div>
      </div>

      {/* Mensaje de éxito cuando todo está clasificado */}
      {stats.pendientes === 0 && (
        <Card className="bg-success-500/10 border-success-500/30">
          <CardContent className="py-4 text-center">
            <Check className="h-8 w-8 mx-auto mb-2 text-success-400" />
            <p className="text-success-300 font-medium">
              ¡Todos los conceptos están clasificados!
            </p>
            <p className="text-sm text-secondary-400 mt-1">
              Puedes proceder al procesamiento del libro.
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  )
}

export default ClasificacionLibroV2
