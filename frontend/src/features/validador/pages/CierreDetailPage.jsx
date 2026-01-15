/**
 * Página de detalle de cierre
 * Muestra el progreso del cierre y permite ejecutar las acciones según el estado
 * 
 * Flujo de 7 estados:
 *   1. CARGA_ARCHIVOS (hub) → 2. CON/SIN_DISCREPANCIAS → 3. CONSOLIDADO →
 *   4. CON/SIN_INCIDENCIAS → 5. FINALIZADO
 */
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { ArrowLeft, FileCheck2, Upload, GitCompare, FileText, CheckCircle, AlertTriangle, AlertCircle, Loader2, RotateCcw } from 'lucide-react'
import api from '../../../api/axios'
import { Card, CardContent, CardHeader, CardTitle } from '../../../components/ui'
import Badge from '../../../components/ui/Badge'
import { CargaArchivos } from '../components'

// Mapa de estados con labels, colores y paso en el stepper (7 pasos)
const ESTADOS = {
  carga_archivos: { label: 'Carga de Archivos', color: 'info', step: 1, icon: Upload },
  con_discrepancias: { label: 'Con Discrepancias', color: 'danger', step: 2, icon: AlertTriangle },
  sin_discrepancias: { label: 'Sin Discrepancias', color: 'success', step: 3, icon: CheckCircle },
  consolidado: { label: 'Consolidado', color: 'info', step: 4, icon: FileText },
  con_incidencias: { label: 'Con Incidencias', color: 'danger', step: 5, icon: AlertCircle },
  sin_incidencias: { label: 'Sin Incidencias', color: 'success', step: 6, icon: CheckCircle },
  finalizado: { label: 'Finalizado', color: 'success', step: 7, icon: FileCheck2 },
  cancelado: { label: 'Cancelado', color: 'secondary', step: 0, icon: AlertTriangle },
  error: { label: 'Error', color: 'danger', step: 0, icon: AlertTriangle },
}

// Pasos del stepper (solo los 7 principales)
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
    case 'carga_archivos': return 1
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
      
      // Estado 2: Con discrepancias - mostrar tabla de discrepancias
      case 'con_discrepancias':
        return (
          <DiscrepanciasPanel 
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
    }
  }

  const handleConsolidar = async () => {
    try {
      await api.post(`/v1/validador/cierres/${id}/consolidar/`)
      refetch()
    } catch (error) {
      console.error('Error al consolidar:', error)
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
 */
const DiscrepanciasPanel = ({ cierre, onVolver }) => {
  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            <AlertTriangle className="h-5 w-5 text-red-400" />
            Discrepancias Encontradas
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
        <div className="text-center py-8 text-secondary-400">
          <AlertTriangle className="h-12 w-12 mx-auto mb-4 opacity-50" />
          <p>Se encontraron diferencias entre el libro ERP y las novedades.</p>
          <p className="text-sm mt-2">Tabla de discrepancias (implementación pendiente)</p>
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
