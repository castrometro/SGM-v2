/**
 * Página de detalle de cierre
 * Muestra el progreso del cierre y permite ejecutar las acciones según el estado
 * 
 * Flujo de 9 estados:
 *   1. CARGA_ARCHIVOS (hub) → 1b. ARCHIVOS_LISTOS → 1c. COMPARANDO →
 *   2. CON/SIN_DISCREPANCIAS → 3. CONSOLIDADO → 4. CON/SIN_INCIDENCIAS → 5. FINALIZADO
 */
import { useState, useMemo } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { ArrowLeft, FileCheck2, Upload, GitCompare, FileText, CheckCircle, AlertTriangle, AlertCircle, Loader2, RotateCcw, Search, ChevronLeft, ChevronRight, Filter } from 'lucide-react'
import api from '../../../api/axios'
import { Card, CardContent, CardHeader, CardTitle } from '../../../components/ui'
import Badge from '../../../components/ui/Badge'
import { CargaArchivos } from '../components'
import { useGenerarDiscrepancias, useDiscrepancias, TIPOS_DISCREPANCIA, ORIGENES_DISCREPANCIA } from '../hooks'

// Mapa de estados con labels, colores y paso en el stepper (9 estados)
const ESTADOS = {
  carga_archivos: { label: 'Carga de Archivos', color: 'info', step: 1, icon: Upload },
  archivos_listos: { label: 'Archivos Listos', color: 'info', step: 1, icon: FileCheck2 },
  comparando: { label: 'Generando Discrepancias', color: 'warning', step: 2, icon: Search },
  con_discrepancias: { label: 'Con Discrepancias', color: 'danger', step: 2, icon: AlertTriangle },
  sin_discrepancias: { label: 'Sin Discrepancias', color: 'success', step: 3, icon: CheckCircle },
  consolidado: { label: 'Consolidado', color: 'info', step: 4, icon: FileText },
  con_incidencias: { label: 'Con Incidencias', color: 'danger', step: 5, icon: AlertCircle },
  sin_incidencias: { label: 'Sin Incidencias', color: 'success', step: 6, icon: CheckCircle },
  finalizado: { label: 'Finalizado', color: 'success', step: 7, icon: FileCheck2 },
  cancelado: { label: 'Cancelado', color: 'secondary', step: 0, icon: AlertTriangle },
  error: { label: 'Error', color: 'danger', step: 0, icon: AlertTriangle },
}

// Pasos del stepper (solo los 5 principales)
const STEPPER_STEPS = [
  { key: 'carga_archivos', label: 'Carga', step: 1 },
  { key: 'discrepancias', label: 'Discrepancias', step: 2 },
  { key: 'consolidado', label: 'Consolidado', step: 3 },
  { key: 'incidencias', label: 'Incidencias', step: 4 },
  { key: 'finalizado', label: 'Finalizado', step: 5 },
]

// Mapeo de estados a paso del stepper
const getStepperStep = (estado) => {
  switch (estado) {
    case 'carga_archivos':
    case 'archivos_listos': return 1
    case 'comparando':
    case 'con_discrepancias':
    case 'sin_discrepancias': return 2
    case 'consolidado': return 3
    case 'con_incidencias':
    case 'sin_incidencias': return 4
    case 'finalizado': return 5
    default: return 0
  }
}

const CierreDetailPage = () => {
  const { id } = useParams()
  const navigate = useNavigate()

  const { data: cierre, isLoading, refetch } = useQuery({
    queryKey: ['cierre', id],
    queryFn: async () => {
      const { data } = await api.get(`/v1/validador/cierres/${id}/`)
      return data
    },
  })

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-500"></div>
      </div>
    )
  }

  if (!cierre) {
    return <div>Cierre no encontrado</div>
  }

  const estadoInfo = ESTADOS[cierre.estado] || { label: cierre.estado, color: 'default', step: 0 }
  const currentStep = getStepperStep(cierre.estado)

  // Renderizar contenido según el estado actual
  const renderStepContent = () => {
    switch (cierre.estado) {
      // Estado 1: Hub de carga de archivos (ERP + Clasificación + Novedades + Mapeo)
      case 'carga_archivos':
        return <CargaArchivos cierreId={id} cierre={cierre} onUpdate={refetch} />
      
      // Estado 1b: Archivos listos - mostrar panel para generar discrepancias
      case 'archivos_listos':
        return (
          <ArchivosListosPanel 
            cierreId={id}
            cierre={cierre}
            onVolver={() => handleVolverACarga()}
          />
        )
      
      // Estado 1c: Comparando - mostrar progreso del task
      case 'comparando':
        return (
          <ComparandoPanel 
            cierreId={id}
            cierre={cierre}
          />
        )
      
      // Estado 2: Con discrepancias - mostrar tabla de discrepancias
      case 'con_discrepancias':
        return (
          <DiscrepanciasPanel 
            cierreId={id}
            cierre={cierre}
            onVolver={() => handleVolverACarga()}
          />
        )
      
      // Estado 3: Sin discrepancias - botón manual para consolidar
      case 'sin_discrepancias':
        return (
          <ConsolidarPanel 
            cierre={cierre}
            onConsolidar={() => handleConsolidar()}
            onVolver={() => handleVolverACarga()}
          />
        )
      
      // Estado 4: Consolidado - botón para detectar incidencias
      case 'consolidado':
        return (
          <ConsolidadoPanel 
            cierre={cierre}
            onDetectarIncidencias={() => handleDetectarIncidencias()}
          />
        )
      
      // Estado 5: Con incidencias - tabla de incidencias
      case 'con_incidencias':
        return (
          <IncidenciasPanel 
            cierre={cierre}
            variant="con_incidencias"
          />
        )
      
      // Estado 6: Sin incidencias - botón para finalizar
      case 'sin_incidencias':
        return (
          <FinalizarPanel 
            cierre={cierre}
            onFinalizar={() => handleFinalizar()}
          />
        )
      
      // Estado 7: Finalizado
      case 'finalizado':
        return (
          <PlaceholderStep 
            icon={CheckCircle} 
            title="Cierre Finalizado" 
            description="El proceso de cierre ha finalizado exitosamente."
            variant="success"
          />
        )
      
      case 'cancelado':
        return (
          <PlaceholderStep 
            icon={AlertTriangle} 
            title="Cierre Cancelado" 
            description="El cierre ha sido cancelado."
            variant="secondary"
          />
        )
      
      case 'error':
        return (
          <PlaceholderStep 
            icon={AlertTriangle} 
            title="Error en el Proceso" 
            description="Ha ocurrido un error. Revise los logs y reintente."
            variant="danger"
          />
        )
      
      default:
        return (
          <PlaceholderStep 
            icon={FileCheck2} 
            title={estadoInfo.label} 
            description="Estado no reconocido."
          />
        )
    }
  }

  // Handlers para acciones
  const handleVolverACarga = async () => {
    try {
      await api.post(`/v1/validador/cierres/${id}/volver-a-carga/`)
      refetch()
    } catch (error) {
      console.error('Error al volver a carga:', error)
      alert(error.response?.data?.error || 'Error al volver a carga de archivos')
    }
  }

  const handleConsolidar = async () => {
    try {
      await api.post(`/v1/validador/cierres/${id}/consolidar/`)
      refetch()
    } catch (error) {
      console.error('Error al consolidar:', error)
      alert(error.response?.data?.error || 'Error al consolidar')
    }
  }

  const handleDetectarIncidencias = async () => {
    try {
      await api.post(`/v1/validador/cierres/${id}/detectar-incidencias/`)
      refetch()
    } catch (error) {
      console.error('Error al detectar incidencias:', error)
    }
  }

  const handleFinalizar = async () => {
    try {
      await api.post(`/v1/validador/cierres/${id}/finalizar/`)
      refetch()
    } catch (error) {
      console.error('Error al finalizar:', error)
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <button 
          onClick={() => navigate(-1)}
          className="p-2 rounded-lg hover:bg-secondary-800 transition-colors"
        >
          <ArrowLeft className="h-5 w-5 text-secondary-400" />
        </button>
        <div className="flex-1">
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold text-secondary-100">
              {cierre.cliente_nombre}
            </h1>
            <code className="text-sm bg-secondary-800 px-2 py-0.5 rounded text-secondary-300">
              {cierre.cliente_rut}
            </code>
          </div>
          <p className="text-secondary-400 mt-1">
            {cierre.mes_nombre} {cierre.anio}
          </p>
        </div>
        <Badge variant={estadoInfo.color} className="text-sm px-3 py-1">
          {estadoInfo.label}
        </Badge>
      </div>

      {/* Progress Steps - Stepper Visual de 5 pasos */}
      <Card>
        <CardHeader>
          <CardTitle>Progreso del Cierre</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-between">
            {STEPPER_STEPS.map((step, index) => (
              <div key={step.key} className="flex items-center flex-1">
                <div className="flex flex-col items-center">
                  <div className={`
                    flex items-center justify-center w-10 h-10 rounded-full text-sm font-medium
                    transition-all duration-300
                    ${step.step <= currentStep 
                      ? 'bg-primary-600 text-white shadow-lg shadow-primary-600/30' 
                      : 'bg-secondary-700 text-secondary-400'
                    }
                    ${step.step === currentStep ? 'ring-2 ring-primary-400 ring-offset-2 ring-offset-secondary-900' : ''}
                  `}>
                    {step.step < currentStep ? (
                      <CheckCircle className="h-5 w-5" />
                    ) : (
                      step.step
                    )}
                  </div>
                  <span className={`
                    mt-2 text-xs font-medium
                    ${step.step <= currentStep ? 'text-primary-400' : 'text-secondary-500'}
                  `}>
                    {step.label}
                  </span>
                </div>
                {index < STEPPER_STEPS.length - 1 && (
                  <div className={`
                    flex-1 h-1 mx-2 rounded-full transition-all duration-300
                    ${step.step < currentStep 
                      ? 'bg-primary-600' 
                      : 'bg-secondary-700'
                    }
                  `} />
                )}
              </div>
            ))}
          </div>
          <div className="mt-6 text-center">
            <p className="text-secondary-400 text-sm">
              Estado actual: <span className="text-secondary-100 font-medium">{estadoInfo.label}</span>
            </p>
          </div>
        </CardContent>
      </Card>

      {/* Content based on state */}
      {renderStepContent()}
    </div>
  )
}

/**
 * Componente placeholder para pasos no implementados
 */
const PlaceholderStep = ({ icon: Icon, title, description, variant = 'default' }) => {
  const variantStyles = {
    default: 'text-secondary-400',
    success: 'text-green-400',
    danger: 'text-red-400',
    secondary: 'text-secondary-500',
  }

  return (
    <Card>
      <CardContent className="py-12">
        <div className="flex flex-col items-center justify-center text-secondary-400">
          <Icon className={`h-12 w-12 mb-4 opacity-50 ${variantStyles[variant]}`} />
          <p className={`text-lg font-medium ${variant === 'default' ? 'text-secondary-200' : variantStyles[variant]}`}>
            {title}
          </p>
          <p className="text-sm mt-2 text-center max-w-md">
            {description}
          </p>
        </div>
      </CardContent>
    </Card>
  )
}

/**
 * Panel de discrepancias - Estado: CON_DISCREPANCIAS
 * Muestra tabs separadas para Montos y Movimientos
 */
const DiscrepanciasPanel = ({ cierreId, cierre, onVolver }) => {
  const [activeTab, setActiveTab] = useState('montos')
  
  // Cargar discrepancias separadas por origen
  const { data: discrepanciasMontos, isLoading: loadingMontos } = useDiscrepancias(cierreId, {
    origen: 'libro_vs_novedades'
  })
  
  const { data: discrepanciasMovimientos, isLoading: loadingMovimientos } = useDiscrepancias(cierreId, {
    origen: 'movimientos_vs_analista'
  })

  const countMontos = discrepanciasMontos?.results?.length || 0
  const countMovimientos = discrepanciasMovimientos?.results?.length || 0

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            <AlertTriangle className="h-5 w-5 text-red-400" />
            Discrepancias Encontradas
            <Badge variant="danger" className="ml-2">{countMontos + countMovimientos}</Badge>
          </CardTitle>
          <button
            onClick={onVolver}
            className="flex items-center gap-2 px-3 py-1.5 text-sm bg-secondary-700 hover:bg-secondary-600 rounded-lg transition-colors"
          >
            <RotateCcw className="h-4 w-4" />
            Volver a Carga
          </button>
        </div>
      </CardHeader>
      <CardContent>
        {/* Tabs */}
        <div className="flex gap-2 mb-6 border-b border-secondary-700">
          <button
            onClick={() => setActiveTab('montos')}
            className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
              activeTab === 'montos'
                ? 'border-primary-500 text-primary-400'
                : 'border-transparent text-secondary-400 hover:text-secondary-200'
            }`}
          >
            Novedades vs Libro
            <Badge variant={countMontos > 0 ? 'warning' : 'secondary'} className="ml-2 text-xs">
              {countMontos}
            </Badge>
          </button>
          <button
            onClick={() => setActiveTab('movimientos')}
            className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
              activeTab === 'movimientos'
                ? 'border-primary-500 text-primary-400'
                : 'border-transparent text-secondary-400 hover:text-secondary-200'
            }`}
          >
            Movimientos
            <Badge variant={countMovimientos > 0 ? 'warning' : 'secondary'} className="ml-2 text-xs">
              {countMovimientos}
            </Badge>
          </button>
        </div>

        {/* Contenido según tab activa */}
        {activeTab === 'montos' ? (
          <TablaMontos discrepancias={discrepanciasMontos?.results} isLoading={loadingMontos} />
        ) : (
          <TablaMovimientos discrepancias={discrepanciasMovimientos?.results} isLoading={loadingMovimientos} />
        )}
      </CardContent>
    </Card>
  )
}

/**
 * Tabla de diferencias de montos (Libro vs Novedades) con filtros y paginación
 */
const TablaMontos = ({ discrepancias, isLoading }) => {
  const [filtroRut, setFiltroRut] = useState('')
  const [filtroConcepto, setFiltroConcepto] = useState('')
  const [page, setPage] = useState(1)
  const pageSize = 20

  // Filtrar discrepancias
  const filtradas = useMemo(() => {
    if (!discrepancias) return []
    return discrepancias.filter(d => {
      const matchRut = !filtroRut || d.rut_empleado?.toLowerCase().includes(filtroRut.toLowerCase())
      const matchConcepto = !filtroConcepto || 
        d.nombre_item?.toLowerCase().includes(filtroConcepto.toLowerCase()) ||
        d.nombre_item_novedades?.toLowerCase().includes(filtroConcepto.toLowerCase())
      return matchRut && matchConcepto
    })
  }, [discrepancias, filtroRut, filtroConcepto])

  // Paginación
  const totalPages = Math.ceil(filtradas.length / pageSize)
  const paginadas = filtradas.slice((page - 1) * pageSize, page * pageSize)

  // Reset page when filters change
  useMemo(() => setPage(1), [filtroRut, filtroConcepto])

  if (isLoading) {
    return (
      <div className="text-center py-8">
        <Loader2 className="h-8 w-8 animate-spin mx-auto text-primary-400" />
      </div>
    )
  }

  if (!discrepancias?.length) {
    return (
      <div className="text-center py-8 text-secondary-400">
        No hay diferencias de montos
      </div>
    )
  }

  return (
    <div>
      {/* Filtros */}
      <div className="flex gap-4 mb-4">
        <div className="flex-1 max-w-xs">
          <input
            type="text"
            placeholder="Filtrar por RUT..."
            value={filtroRut}
            onChange={(e) => setFiltroRut(e.target.value)}
            className="w-full px-3 py-2 bg-secondary-800 border border-secondary-700 rounded-lg text-sm text-secondary-200 placeholder-secondary-500 focus:outline-none focus:border-primary-500"
          />
        </div>
        <div className="flex-1 max-w-xs">
          <input
            type="text"
            placeholder="Filtrar por concepto..."
            value={filtroConcepto}
            onChange={(e) => setFiltroConcepto(e.target.value)}
            className="w-full px-3 py-2 bg-secondary-800 border border-secondary-700 rounded-lg text-sm text-secondary-200 placeholder-secondary-500 focus:outline-none focus:border-primary-500"
          />
        </div>
        <div className="text-sm text-secondary-400 self-center">
          {filtradas.length} de {discrepancias.length} registros
        </div>
      </div>

      {/* Tabla */}
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-secondary-700">
              <th className="text-left py-3 px-4 text-secondary-400 font-medium">RUT</th>
              <th className="text-left py-3 px-4 text-secondary-400 font-medium">Nombre</th>
              <th className="text-left py-3 px-4 text-secondary-400 font-medium">Concepto Libro</th>
              <th className="text-left py-3 px-4 text-secondary-400 font-medium">Concepto Novedades</th>
              <th className="text-right py-3 px-4 text-secondary-400 font-medium">Monto Libro</th>
              <th className="text-right py-3 px-4 text-secondary-400 font-medium">Monto Novedades</th>
              <th className="text-right py-3 px-4 text-secondary-400 font-medium">Diferencia</th>
            </tr>
          </thead>
          <tbody>
            {paginadas.map((d) => (
              <tr key={d.id} className="border-b border-secondary-800 hover:bg-secondary-800/50">
                <td className="py-3 px-4 font-mono text-secondary-300">{d.rut_empleado}</td>
                <td className="py-3 px-4 text-secondary-200">{d.nombre_empleado || '-'}</td>
                <td className="py-3 px-4 text-secondary-200">{d.nombre_item || '-'}</td>
                <td className="py-3 px-4 text-secondary-200">{d.nombre_item_novedades || '-'}</td>
                <td className="py-3 px-4 text-right font-mono text-secondary-300">
                  {d.monto_erp ? `$${Number(d.monto_erp).toLocaleString('es-CL')}` : '-'}
                </td>
                <td className="py-3 px-4 text-right font-mono text-secondary-300">
                  {d.monto_cliente ? `$${Number(d.monto_cliente).toLocaleString('es-CL')}` : '-'}
                </td>
                <td className={`py-3 px-4 text-right font-mono font-medium ${
                  d.diferencia > 0 ? 'text-green-400' : d.diferencia < 0 ? 'text-red-400' : 'text-secondary-400'
                }`}>
                  {d.diferencia ? `$${Number(d.diferencia).toLocaleString('es-CL')}` : '-'}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Paginación */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between mt-4 pt-4 border-t border-secondary-700">
          <div className="text-sm text-secondary-400">
            Página {page} de {totalPages}
          </div>
          <div className="flex gap-2">
            <button
              onClick={() => setPage(p => Math.max(1, p - 1))}
              disabled={page === 1}
              className="p-2 rounded-lg bg-secondary-800 hover:bg-secondary-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <ChevronLeft className="h-4 w-4" />
            </button>
            <button
              onClick={() => setPage(p => Math.min(totalPages, p + 1))}
              disabled={page === totalPages}
              className="p-2 rounded-lg bg-secondary-800 hover:bg-secondary-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <ChevronRight className="h-4 w-4" />
            </button>
          </div>
        </div>
      )}
    </div>
  )
}

/**
 * Tabla de diferencias de movimientos con filtros y paginación
 */
const TablaMovimientos = ({ discrepancias, isLoading }) => {
  const [filtroRut, setFiltroRut] = useState('')
  const [filtroTipo, setFiltroTipo] = useState('')
  const [filtroDonde, setFiltroDonde] = useState('')
  const [page, setPage] = useState(1)
  const pageSize = 20

  const tiposMovimiento = [
    { value: '', label: 'Todos' },
    { value: 'ingreso', label: 'Ingreso' },
    { value: 'finiquito', label: 'Finiquito' },
    { value: 'vacaciones', label: 'Vacaciones' },
    { value: 'asistencia', label: 'Asistencia' },
  ]

  const opcionesDonde = [
    { value: '', label: 'Todos' },
    { value: 'falta_en_erp', label: 'Falta en ERP' },
    { value: 'falta_en_cliente', label: 'Falta en Cliente' },
  ]

  // Filtrar discrepancias
  const filtradas = useMemo(() => {
    if (!discrepancias) return []
    return discrepancias.filter(d => {
      const matchRut = !filtroRut || d.rut_empleado?.toLowerCase().includes(filtroRut.toLowerCase())
      const matchTipo = !filtroTipo || d.tipo_movimiento === filtroTipo
      const matchDonde = !filtroDonde || d.tipo === filtroDonde
      return matchRut && matchTipo && matchDonde
    })
  }, [discrepancias, filtroRut, filtroTipo, filtroDonde])

  // Paginación
  const totalPages = Math.ceil(filtradas.length / pageSize)
  const paginadas = filtradas.slice((page - 1) * pageSize, page * pageSize)

  // Reset page when filters change
  useMemo(() => setPage(1), [filtroRut, filtroTipo, filtroDonde])

  const getTipoMovimientoLabel = (tipo) => {
    const labels = {
      ingreso: 'Ingreso',
      finiquito: 'Finiquito',
      vacaciones: 'Vacaciones',
      asistencia: 'Asistencia',
    }
    return labels[tipo] || tipo
  }

  if (isLoading) {
    return (
      <div className="text-center py-8">
        <Loader2 className="h-8 w-8 animate-spin mx-auto text-primary-400" />
      </div>
    )
  }

  if (!discrepancias?.length) {
    return (
      <div className="text-center py-8 text-secondary-400">
        No hay diferencias de movimientos
      </div>
    )
  }

  return (
    <div>
      {/* Filtros */}
      <div className="flex flex-wrap gap-4 mb-4">
        <div className="flex-1 min-w-[150px] max-w-xs">
          <input
            type="text"
            placeholder="Filtrar por RUT..."
            value={filtroRut}
            onChange={(e) => setFiltroRut(e.target.value)}
            className="w-full px-3 py-2 bg-secondary-800 border border-secondary-700 rounded-lg text-sm text-secondary-200 placeholder-secondary-500 focus:outline-none focus:border-primary-500"
          />
        </div>
        <div className="min-w-[150px]">
          <select
            value={filtroTipo}
            onChange={(e) => setFiltroTipo(e.target.value)}
            className="w-full px-3 py-2 bg-secondary-800 border border-secondary-700 rounded-lg text-sm text-secondary-200 focus:outline-none focus:border-primary-500"
          >
            {tiposMovimiento.map(t => (
              <option key={t.value} value={t.value}>{t.label}</option>
            ))}
          </select>
        </div>
        <div className="min-w-[150px]">
          <select
            value={filtroDonde}
            onChange={(e) => setFiltroDonde(e.target.value)}
            className="w-full px-3 py-2 bg-secondary-800 border border-secondary-700 rounded-lg text-sm text-secondary-200 focus:outline-none focus:border-primary-500"
          >
            {opcionesDonde.map(o => (
              <option key={o.value} value={o.value}>{o.label}</option>
            ))}
          </select>
        </div>
        <div className="text-sm text-secondary-400 self-center">
          {filtradas.length} de {discrepancias.length} registros
        </div>
      </div>

      {/* Tabla */}
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-secondary-700">
              <th className="text-left py-3 px-4 text-secondary-400 font-medium">RUT</th>
              <th className="text-left py-3 px-4 text-secondary-400 font-medium">Nombre</th>
              <th className="text-left py-3 px-4 text-secondary-400 font-medium">Tipo Movimiento</th>
              <th className="text-left py-3 px-4 text-secondary-400 font-medium">Dónde Falta</th>
              <th className="text-left py-3 px-4 text-secondary-400 font-medium">Fechas</th>
              <th className="text-center py-3 px-4 text-secondary-400 font-medium">Días</th>
            </tr>
          </thead>
          <tbody>
            {paginadas.map((d) => (
              <tr key={d.id} className="border-b border-secondary-800 hover:bg-secondary-800/50">
                <td className="py-3 px-4 font-mono text-secondary-300">{d.rut_empleado}</td>
                <td className="py-3 px-4 text-secondary-200">{d.nombre_empleado || '-'}</td>
                <td className="py-3 px-4">
                  <Badge variant="info" className="text-xs">
                    {getTipoMovimientoLabel(d.tipo_movimiento)}
                  </Badge>
                </td>
                <td className="py-3 px-4">
                  <Badge 
                    variant={d.tipo === 'falta_en_cliente' ? 'warning' : 'danger'}
                    className="text-xs"
                  >
                    {d.tipo === 'falta_en_cliente' ? 'Falta en Cliente' : 'Falta en ERP'}
                  </Badge>
                </td>
                <td className="py-3 px-4 text-secondary-300 text-sm">
                  {d.detalle_movimiento?.fecha_inicio && (
                    <span>{d.detalle_movimiento.fecha_inicio}</span>
                  )}
                  {d.detalle_movimiento?.fecha_fin && (
                    <span> → {d.detalle_movimiento.fecha_fin}</span>
                  )}
                  {!d.detalle_movimiento?.fecha_inicio && !d.detalle_movimiento?.fecha_fin && '-'}
                </td>
                <td className="py-3 px-4 text-center text-secondary-300">
                  {d.detalle_movimiento?.dias || '-'}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Paginación */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between mt-4 pt-4 border-t border-secondary-700">
          <div className="text-sm text-secondary-400">
            Página {page} de {totalPages}
          </div>
          <div className="flex gap-2">
            <button
              onClick={() => setPage(p => Math.max(1, p - 1))}
              disabled={page === 1}
              className="p-2 rounded-lg bg-secondary-800 hover:bg-secondary-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <ChevronLeft className="h-4 w-4" />
            </button>
            <button
              onClick={() => setPage(p => Math.min(totalPages, p + 1))}
              disabled={page === totalPages}
              className="p-2 rounded-lg bg-secondary-800 hover:bg-secondary-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <ChevronRight className="h-4 w-4" />
            </button>
          </div>
        </div>
      )}
    </div>
  )
}

/**
 * Panel para archivos listos - Estado: ARCHIVOS_LISTOS
 * Muestra resumen y botón para generar discrepancias
 */
const ArchivosListosPanel = ({ cierreId, cierre, onVolver }) => {
  const { generarDiscrepancias, progreso, isGenerating, isStarting, error } = useGenerarDiscrepancias(cierreId)

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <FileCheck2 className="h-5 w-5 text-green-400" />
          Archivos Listos
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="text-center py-8">
          <FileCheck2 className="h-16 w-16 mx-auto mb-4 text-green-400" />
          <p className="text-lg text-secondary-200 mb-2">¡Todos los archivos están listos!</p>
          <p className="text-secondary-400 mb-6">
            Los archivos han sido cargados y procesados correctamente.
            <br />
            Puedes continuar generando las discrepancias entre el ERP y los archivos del analista.
          </p>
          
          {error && (
            <div className="mb-4 p-3 bg-red-900/30 border border-red-700 rounded-lg text-red-400 text-sm">
              {error}
            </div>
          )}
          
          <div className="flex items-center justify-center gap-4">
            <button
              onClick={onVolver}
              disabled={isGenerating || isStarting}
              className="flex items-center gap-2 px-4 py-2 text-sm bg-secondary-700 hover:bg-secondary-600 rounded-lg transition-colors disabled:opacity-50"
            >
              <RotateCcw className="h-4 w-4" />
              Volver a Carga
            </button>
            <button
              onClick={generarDiscrepancias}
              disabled={isGenerating || isStarting}
              className="flex items-center gap-2 px-6 py-2 bg-primary-600 hover:bg-primary-700 text-white rounded-lg font-medium transition-colors disabled:opacity-50"
            >
              {isStarting ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Iniciando...
                </>
              ) : (
                <>
                  <Search className="h-4 w-4" />
                  Generar Discrepancias
                </>
              )}
            </button>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

/**
 * Panel de comparación en progreso - Estado: COMPARANDO
 * Muestra barra de progreso y mensajes del task Celery
 */
const ComparandoPanel = ({ cierreId, cierre }) => {
  const queryClient = useQueryClient()
  
  // Polling de progreso mientras el cierre esté en estado comparando
  const { data: progreso } = useQuery({
    queryKey: ['progreso-comparacion', cierreId],
    queryFn: async () => {
      const { data } = await api.get(`/v1/validador/cierres/${cierreId}/progreso-comparacion/`)
      return data
    },
    enabled: !!cierreId,
    refetchInterval: (query) => {
      const data = query.state.data
      // Seguir polling mientras esté comparando
      if (data?.estado === 'comparando' || !data?.estado) {
        return 2000 // 2 segundos
      }
      // Cuando termina, invalidar cierre para que cambie de estado
      if (data?.estado === 'completado' || data?.estado === 'error') {
        queryClient.invalidateQueries({ queryKey: ['cierre', cierreId] })
        queryClient.invalidateQueries({ queryKey: ['discrepancias', cierreId] })
        return false
      }
      return 2000
    },
  })

  const progresoData = progreso || { estado: 'comparando', progreso: 0, mensaje: 'Iniciando comparación...' }

  // Mapeo de fases a iconos y colores
  const faseInfo = {
    preparacion: { label: 'Preparando datos', icon: Loader2 },
    libro_vs_novedades: { label: 'Comparando Libro vs Novedades', icon: GitCompare },
    movimientos: { label: 'Comparando Movimientos', icon: GitCompare },
    finalizando: { label: 'Finalizando', icon: CheckCircle },
    completado: { label: 'Completado', icon: CheckCircle },
  }

  const fase = faseInfo[progresoData.fase] || faseInfo.preparacion

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Search className="h-5 w-5 text-yellow-400 animate-pulse" />
          Generando Discrepancias
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="py-8">
          {/* Icono animado */}
          <div className="flex justify-center mb-6">
            <div className="relative">
              <GitCompare className="h-16 w-16 text-primary-400" />
              <div className="absolute -bottom-1 -right-1 bg-secondary-900 rounded-full p-1">
                <Loader2 className="h-5 w-5 text-yellow-400 animate-spin" />
              </div>
            </div>
          </div>

          {/* Mensaje de fase actual */}
          <p className="text-center text-lg text-secondary-200 mb-2">
            {fase.label}
          </p>
          <p className="text-center text-sm text-secondary-400 mb-6">
            {progresoData.mensaje}
          </p>

          {/* Barra de progreso */}
          <div className="max-w-md mx-auto">
            <div className="flex justify-between text-sm text-secondary-400 mb-2">
              <span>Progreso</span>
              <span>{progresoData.progreso}%</span>
            </div>
            <div className="h-3 bg-secondary-700 rounded-full overflow-hidden">
              <div 
                className="h-full bg-gradient-to-r from-primary-600 to-primary-400 rounded-full transition-all duration-500 ease-out"
                style={{ width: `${progresoData.progreso}%` }}
              />
            </div>
          </div>

          {/* Info adicional si está disponible */}
          {progresoData.resultado && (
            <div className="mt-6 p-4 bg-secondary-800 rounded-lg max-w-md mx-auto">
              <p className="text-sm text-secondary-400">
                Discrepancias encontradas: 
                <span className="font-bold text-secondary-200 ml-2">
                  {progresoData.resultado.total_discrepancias}
                </span>
              </p>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  )
}

/**
 * Panel para consolidar - Estado: SIN_DISCREPANCIAS
 */
const ConsolidarPanel = ({ cierre, onConsolidar, onVolver }) => {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <CheckCircle className="h-5 w-5 text-green-400" />
          Sin Discrepancias
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="text-center py-8">
          <CheckCircle className="h-16 w-16 mx-auto mb-4 text-green-400" />
          <p className="text-lg text-secondary-200 mb-2">¡No hay discrepancias!</p>
          <p className="text-secondary-400 mb-6">
            Los datos del libro ERP coinciden con las novedades del cliente.
          </p>
          <div className="flex items-center justify-center gap-4">
            <button
              onClick={onVolver}
              className="flex items-center gap-2 px-4 py-2 text-sm bg-secondary-700 hover:bg-secondary-600 rounded-lg transition-colors"
            >
              <RotateCcw className="h-4 w-4" />
              Volver a Carga
            </button>
            <button
              onClick={onConsolidar}
              className="flex items-center gap-2 px-6 py-2 bg-primary-600 hover:bg-primary-700 text-white rounded-lg font-medium transition-colors"
            >
              <FileText className="h-4 w-4" />
              Consolidar Cierre
            </button>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

/**
 * Panel consolidado - Estado: CONSOLIDADO
 */
const ConsolidadoPanel = ({ cierre, onDetectarIncidencias }) => {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <FileText className="h-5 w-5 text-primary-400" />
          Cierre Consolidado
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="text-center py-8">
          <FileText className="h-16 w-16 mx-auto mb-4 text-primary-400" />
          <p className="text-lg text-secondary-200 mb-2">Datos Validados</p>
          <p className="text-secondary-400 mb-6">
            Los datos han sido consolidados. Ahora puede detectar incidencias comparando con períodos anteriores.
          </p>
          <button
            onClick={onDetectarIncidencias}
            className="flex items-center gap-2 px-6 py-2 mx-auto bg-primary-600 hover:bg-primary-700 text-white rounded-lg font-medium transition-colors"
          >
            <AlertCircle className="h-4 w-4" />
            Detectar Incidencias
          </button>
        </div>
      </CardContent>
    </Card>
  )
}

/**
 * Panel de incidencias - Estados: CON_INCIDENCIAS / SIN_INCIDENCIAS
 */
const IncidenciasPanel = ({ cierre, variant }) => {
  const tieneIncidencias = variant === 'con_incidencias'
  
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <AlertCircle className={`h-5 w-5 ${tieneIncidencias ? 'text-red-400' : 'text-green-400'}`} />
          {tieneIncidencias ? 'Incidencias Encontradas' : 'Sin Incidencias'}
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="text-center py-8 text-secondary-400">
          <AlertCircle className={`h-12 w-12 mx-auto mb-4 opacity-50 ${tieneIncidencias ? 'text-red-400' : 'text-green-400'}`} />
          <p>{tieneIncidencias 
            ? 'Se encontraron incidencias que requieren revisión.' 
            : 'No se encontraron incidencias.'
          }</p>
          <p className="text-sm mt-2">Tabla de incidencias (implementación pendiente)</p>
        </div>
      </CardContent>
    </Card>
  )
}

/**
 * Panel para finalizar - Estado: SIN_INCIDENCIAS
 */
const FinalizarPanel = ({ cierre, onFinalizar }) => {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <CheckCircle className="h-5 w-5 text-green-400" />
          Listo para Finalizar
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="text-center py-8">
          <CheckCircle className="h-16 w-16 mx-auto mb-4 text-green-400" />
          <p className="text-lg text-secondary-200 mb-2">¡Todo listo!</p>
          <p className="text-secondary-400 mb-6">
            No hay incidencias pendientes. El cierre está listo para ser finalizado.
          </p>
          <button
            onClick={onFinalizar}
            className="flex items-center gap-2 px-6 py-2 mx-auto bg-green-600 hover:bg-green-700 text-white rounded-lg font-medium transition-colors"
          >
            <FileCheck2 className="h-4 w-4" />
            Finalizar Cierre
          </button>
        </div>
      </CardContent>
    </Card>
  )
}

export default CierreDetailPage
