/**
 * Componente para Clasificación de Headers del Libro de Remuneraciones
 * Permite clasificar conceptos manualmente o de forma automática usando historial
 */
import { useState, useEffect } from 'react'
import { 
  BookOpen, 
  Sparkles, 
  Check, 
  AlertCircle, 
  Loader2, 
  Copy,
  Search,
  ChevronRight,
  Tag
} from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '../../../components/ui'
import Badge from '../../../components/ui/Badge'
import Button from '../../../components/ui/Button'
import { cn } from '../../../utils/cn'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import api from '../../../api/axios'
import { CATEGORIA_CONCEPTO_LIBRO } from '../../../constants'

/**
 * Componente principal de clasificación del libro
 */
const ClasificacionLibro = ({ archivoId, clienteId, cierreId, onComplete }) => {
  const [busqueda, setBusqueda] = useState('')
  const [clasificaciones, setClasificaciones] = useState({})
  const [mostrarSugerencias, setMostrarSugerencias] = useState(true)
  const queryClient = useQueryClient()

  // Obtener headers y conceptos
  const { data: headersData, isLoading, error } = useQuery({
    queryKey: ['libro-headers', archivoId],
    queryFn: async () => {
      const { data } = await api.get(`/v1/validador/libro/${archivoId}/headers/`)
      return data
    },
    enabled: !!archivoId,
  })

  // Obtener pendientes con sugerencias
  const { data: pendientesData, refetch: refetchPendientes } = useQuery({
    queryKey: ['libro-pendientes', archivoId],
    queryFn: async () => {
      const { data } = await api.get(`/v1/validador/libro/${archivoId}/pendientes/`)
      return data
    },
    enabled: !!archivoId,
  })

  // Mutation para clasificación manual
  const clasificarMutation = useMutation({
    mutationFn: async (clasificacionesData) => {
      const { data } = await api.post(
        `/v1/validador/libro/${archivoId}/clasificar/`,
        { clasificaciones: clasificacionesData }
      )
      return data
    },
    onSuccess: () => {
      queryClient.invalidateQueries(['libro-headers', archivoId])
      queryClient.invalidateQueries(['libro-pendientes', archivoId])
      setClasificaciones({})
    },
  })

  // Mutation para clasificación automática
  const clasificarAutoMutation = useMutation({
    mutationFn: async () => {
      const { data } = await api.post(`/v1/validador/libro/${archivoId}/clasificar-auto/`)
      return data
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries(['libro-headers', archivoId])
      queryClient.invalidateQueries(['libro-pendientes', archivoId])
    },
  })

  // Aplicar sugerencia a un concepto
  const aplicarSugerencia = (concepto) => {
    if (concepto.sugerencia) {
      setClasificaciones(prev => ({
        ...prev,
        [concepto.header_pandas || concepto.header_original]: {
          header: concepto.header_pandas || concepto.header_original,
          ocurrencia: concepto.ocurrencia,
          categoria: concepto.sugerencia.categoria,
          es_identificador: concepto.sugerencia.es_identificador,
        }
      }))
    }
  }

  // Aplicar todas las sugerencias
  const aplicarTodasSugerencias = () => {
    if (!pendientesData?.conceptos) return
    
    const nuevasClasificaciones = {}
    pendientesData.conceptos.forEach(concepto => {
      if (concepto.sugerencia) {
        nuevasClasificaciones[concepto.header_pandas || concepto.header_original] = {
          header: concepto.header_pandas || concepto.header_original,
          ocurrencia: concepto.ocurrencia,
          categoria: concepto.sugerencia.categoria,
          es_identificador: concepto.sugerencia.es_identificador,
        }
      }
    })
    setClasificaciones(prev => ({ ...prev, ...nuevasClasificaciones }))
  }

  // Cambiar clasificación de un concepto
  const cambiarClasificacion = (concepto, categoria, esIdentificador = false) => {
    const key = concepto.header_pandas || concepto.header_original
    setClasificaciones(prev => ({
      ...prev,
      [key]: {
        header: key,
        ocurrencia: concepto.ocurrencia,
        categoria,
        es_identificador: esIdentificador,
      }
    }))
  }

  // Guardar clasificaciones
  const handleGuardar = () => {
    const clasificacionesArray = Object.values(clasificaciones)
    if (clasificacionesArray.length > 0) {
      clasificarMutation.mutate(clasificacionesArray)
    }
  }

  // Filtrar conceptos pendientes
  const conceptosPendientes = (pendientesData?.conceptos || []).filter(c => {
    if (!busqueda) return true
    return c.header_original.toLowerCase().includes(busqueda.toLowerCase())
  })

  if (isLoading) {
    return (
      <Card>
        <CardContent className="flex items-center justify-center py-8">
          <Loader2 className="h-6 w-6 animate-spin text-primary-400" />
          <span className="ml-2 text-secondary-300">Cargando clasificación...</span>
        </CardContent>
      </Card>
    )
  }

  if (error) {
    return (
      <Card>
        <CardContent className="flex items-center justify-center py-8 text-danger-400">
          <AlertCircle className="h-6 w-6 mr-2" />
          Error al cargar clasificación: {error.message}
        </CardContent>
      </Card>
    )
  }

  const progreso = headersData?.progreso || 0
  const tieneDuplicados = headersData?.tiene_duplicados || false
  const tieneClasificacionesPendientes = Object.keys(clasificaciones).length > 0
  const tieneSugerencias = (pendientesData?.conceptos || []).some(c => c.sugerencia)

  return (
    <div className="space-y-4">
      {/* Header con progreso */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <BookOpen className="h-6 w-6 text-primary-400" />
              <div>
                <CardTitle>Clasificación de Conceptos</CardTitle>
                <p className="text-sm text-secondary-400 mt-1">
                  {headersData?.headers_clasificados || 0} de {headersData?.headers_total || 0} conceptos clasificados
                </p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              {tieneDuplicados && (
                <Badge color="warning" className="flex items-center gap-1">
                  <Copy className="h-3 w-3" />
                  Tiene duplicados
                </Badge>
              )}
              <div className="flex items-center gap-2">
                <div className="text-right">
                  <div className="text-2xl font-bold text-primary-400">{progreso}%</div>
                  <div className="text-xs text-secondary-400">Progreso</div>
                </div>
              </div>
            </div>
          </div>
          
          {/* Barra de progreso */}
          <div className="mt-4">
            <div className="w-full bg-secondary-700 rounded-full h-2">
              <div 
                className="bg-gradient-to-r from-primary-500 to-accent-500 h-2 rounded-full transition-all duration-500"
                style={{ width: `${progreso}%` }}
              />
            </div>
          </div>
        </CardHeader>
      </Card>

      {/* Acciones rápidas */}
      {conceptosPendientes.length > 0 && (
        <Card>
          <CardContent className="py-4">
            <div className="flex items-center justify-between gap-4">
              <div className="flex items-center gap-2">
                {tieneSugerencias && (
                  <>
                    <Button
                      onClick={() => clasificarAutoMutation.mutate()}
                      disabled={clasificarAutoMutation.isPending}
                      variant="primary"
                      className="flex items-center gap-2"
                    >
                      {clasificarAutoMutation.isPending ? (
                        <Loader2 className="h-4 w-4 animate-spin" />
                      ) : (
                        <Sparkles className="h-4 w-4" />
                      )}
                      Clasificar Automáticamente
                    </Button>
                    <Button
                      onClick={aplicarTodasSugerencias}
                      variant="secondary"
                      className="flex items-center gap-2"
                    >
                      <Check className="h-4 w-4" />
                      Aplicar Todas las Sugerencias
                    </Button>
                  </>
                )}
              </div>
              
              {tieneClasificacionesPendientes && (
                <Button
                  onClick={handleGuardar}
                  disabled={clasificarMutation.isPending}
                  variant="success"
                  className="flex items-center gap-2"
                >
                  {clasificarMutation.isPending ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <Check className="h-4 w-4" />
                  )}
                  Guardar Clasificaciones ({Object.keys(clasificaciones).length})
                </Button>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Lista de conceptos pendientes */}
      {conceptosPendientes.length > 0 ? (
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="text-lg">
                Conceptos Pendientes ({conceptosPendientes.length})
              </CardTitle>
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-secondary-400" />
                <input
                  type="text"
                  placeholder="Buscar concepto..."
                  value={busqueda}
                  onChange={(e) => setBusqueda(e.target.value)}
                  className="pl-10 pr-4 py-2 bg-secondary-800 border border-secondary-700 rounded-lg text-sm focus:outline-none focus:border-primary-500"
                />
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-2 max-h-[600px] overflow-y-auto">
              {conceptosPendientes.map((concepto) => (
                <ConceptoItem
                  key={`${concepto.header_pandas || concepto.header_original}-${concepto.ocurrencia}`}
                  concepto={concepto}
                  clasificacion={clasificaciones[concepto.header_pandas || concepto.header_original]}
                  onClasificar={(categoria, esIdentificador) => 
                    cambiarClasificacion(concepto, categoria, esIdentificador)
                  }
                  onAplicarSugerencia={() => aplicarSugerencia(concepto)}
                />
              ))}
            </div>
          </CardContent>
        </Card>
      ) : (
        <Card>
          <CardContent className="py-8 text-center text-secondary-400">
            <Check className="h-12 w-12 mx-auto mb-3 text-success-400" />
            <p className="text-lg font-medium">¡Todos los conceptos están clasificados!</p>
            <p className="text-sm mt-1">Puedes proceder al procesamiento del libro.</p>
            {onComplete && (
              <Button onClick={onComplete} variant="primary" className="mt-4">
                Procesar Libro
              </Button>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  )
}

/**
 * Componente para un concepto individual
 */
const ConceptoItem = ({ concepto, clasificacion, onClasificar, onAplicarSugerencia }) => {
  const [expanded, setExpanded] = useState(false)
  
  const categoriaActual = clasificacion?.categoria || concepto.categoria
  const tieneSugerencia = !!concepto.sugerencia

  return (
    <div className={cn(
      "border border-secondary-700 rounded-lg p-3 transition-all",
      expanded && "bg-secondary-800/50"
    )}>
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3 flex-1">
          <button
            onClick={() => setExpanded(!expanded)}
            className="text-secondary-400 hover:text-secondary-200"
          >
            <ChevronRight className={cn(
              "h-4 w-4 transition-transform",
              expanded && "rotate-90"
            )} />
          </button>
          
          <div className="flex-1">
            <div className="flex items-center gap-2">
              <span className="font-medium text-secondary-200">
                {concepto.header_original}
              </span>
              {concepto.es_duplicado && (
                <Badge color="warning" size="sm">
                  #{concepto.ocurrencia}
                </Badge>
              )}
              {tieneSugerencia && (
                <Badge color="info" size="sm" className="flex items-center gap-1">
                  <Sparkles className="h-3 w-3" />
                  Sugerencia
                </Badge>
              )}
            </div>
            {concepto.header_pandas && concepto.header_pandas !== concepto.header_original && (
              <p className="text-xs text-secondary-500 mt-1">
                Pandas: {concepto.header_pandas}
              </p>
            )}
          </div>
        </div>

        <div className="flex items-center gap-2">
          {categoriaActual ? (
            <Badge color="success">
              {CATEGORIA_CONCEPTO_LIBRO[categoriaActual] || categoriaActual}
            </Badge>
          ) : (
            <Badge color="secondary">Sin clasificar</Badge>
          )}
        </div>
      </div>

      {expanded && (
        <div className="mt-4 pl-7 space-y-3">
          {/* Sugerencia */}
          {tieneSugerencia && (
            <div className="bg-info-500/10 border border-info-500/30 rounded-lg p-3">
              <div className="flex items-center justify-between">
                <div>
                  <div className="flex items-center gap-2 mb-1">
                    <Sparkles className="h-4 w-4 text-info-400" />
                    <span className="text-sm font-medium text-info-300">
                      Sugerencia basada en historial
                    </span>
                  </div>
                  <p className="text-sm text-secondary-300">
                    Categoría: <span className="font-medium">
                      {CATEGORIA_CONCEPTO_LIBRO[concepto.sugerencia.categoria]}
                    </span>
                  </p>
                  <p className="text-xs text-secondary-400 mt-1">
                    Usado {concepto.sugerencia.frecuencia} {concepto.sugerencia.frecuencia === 1 ? 'vez' : 'veces'} antes
                  </p>
                </div>
                <Button
                  onClick={onAplicarSugerencia}
                  size="sm"
                  variant="primary"
                  className="flex items-center gap-1"
                >
                  <Check className="h-3 w-3" />
                  Aplicar
                </Button>
              </div>
            </div>
          )}

          {/* Selector de categoría */}
          <div>
            <label className="block text-sm font-medium text-secondary-300 mb-2">
              Seleccionar Categoría
            </label>
            <div className="grid grid-cols-2 gap-2">
              {Object.entries(CATEGORIA_CONCEPTO_LIBRO).map(([value, label]) => (
                <button
                  key={value}
                  onClick={() => onClasificar(value, false)}
                  className={cn(
                    "px-3 py-2 rounded-lg text-sm font-medium transition-all text-left",
                    "border hover:border-primary-500",
                    categoriaActual === value
                      ? "border-primary-500 bg-primary-500/20 text-primary-300"
                      : "border-secondary-700 bg-secondary-800 text-secondary-300"
                  )}
                >
                  <div className="flex items-center gap-2">
                    <Tag className="h-3 w-3" />
                    {label}
                  </div>
                </button>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default ClasificacionLibro
