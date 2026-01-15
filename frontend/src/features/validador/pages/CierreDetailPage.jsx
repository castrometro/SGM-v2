/**
 * Página de detalle de cierre
 * Muestra el progreso del cierre y permite ejecutar las acciones según el estado
 */
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { ArrowLeft, FileCheck2, Upload, GitCompare, FileText, CheckCircle, AlertTriangle, FileBarChart, Settings } from 'lucide-react'
import api from '../../../api/axios'
import { Card, CardContent, CardHeader, CardTitle } from '../../../components/ui'
import Badge from '../../../components/ui/Badge'
import { CargaArchivos } from '../components'

const ESTADOS = {
  carga_archivos: { label: 'Carga Libro ERP', color: 'info', step: 1 },
  clasificacion_conceptos: { label: 'Clasificación', color: 'info', step: 2 },
  carga_novedades: { label: 'Carga Novedades', color: 'info', step: 3 },
  mapeo_items: { label: 'Mapeo Items', color: 'info', step: 4 },
  comparacion: { label: 'Comparación', color: 'warning', step: 5 },
  con_discrepancias: { label: 'Con Discrepancias', color: 'danger', step: 5 },
  consolidado: { label: 'Consolidado', color: 'success', step: 6 },
  deteccion_incidencias: { label: 'Detectando Incidencias', color: 'warning', step: 7 },
  revision_incidencias: { label: 'Revisión Incidencias', color: 'warning', step: 8 },
  finalizado: { label: 'Finalizado', color: 'success', step: 9 },
  cancelado: { label: 'Cancelado', color: 'secondary', step: 0 },
  error: { label: 'Error', color: 'danger', step: 0 },
}

const CierreDetailPage = () => {
  const { id } = useParams()
  const navigate = useNavigate()

  const { data: cierre, isLoading } = useQuery({
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

  // Renderizar contenido según el paso actual
  const renderStepContent = () => {
    switch (cierre.estado) {
      case 'carga_archivos':
        return <CargaArchivos cierreId={id} clienteErp={cierre.cliente_erp} soloERP={true} />
      
      case 'clasificacion_conceptos':
        return (
          <PlaceholderStep 
            icon={Settings} 
            title="Clasificación de Conceptos" 
            description="Clasificando los conceptos del libro de remuneraciones..."
          />
        )
      
      case 'carga_novedades':
        return (
          <PlaceholderStep 
            icon={Upload} 
            title="Carga de Novedades del Cliente" 
            description="Suba el archivo de novedades proporcionado por el cliente para validar contra el libro..."
          />
        )
      
      case 'mapeo_items':
        return (
          <PlaceholderStep 
            icon={GitCompare} 
            title="Mapeo de Items" 
            description="Mapeando los items de novedades con los conceptos del ERP..."
          />
        )
      
      case 'comparacion':
        return (
          <PlaceholderStep 
            icon={GitCompare} 
            title="Comparación" 
            description="Comparando datos entre el Libro ERP y las Novedades del cliente..."
          />
        )
      
      case 'con_discrepancias':
        return (
          <PlaceholderStep 
            icon={AlertTriangle} 
            title="Con Discrepancias" 
            description="Se encontraron diferencias entre el libro y las novedades. Revise y corrija."
            variant="danger"
          />
        )
      
      case 'consolidado':
        return (
          <PlaceholderStep 
            icon={FileText} 
            title="Consolidado" 
            description="Los datos han sido validados y consolidados exitosamente."
            variant="success"
          />
        )
      
      case 'deteccion_incidencias':
        return (
          <PlaceholderStep 
            icon={AlertTriangle} 
            title="Detectando Incidencias" 
            description="Analizando variaciones respecto a períodos anteriores..."
          />
        )
      
      case 'revision_incidencias':
        return (
          <PlaceholderStep 
            icon={AlertTriangle} 
            title="Revisión de Incidencias" 
            description="Revise y gestione las incidencias encontradas..."
          />
        )
      
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
            description="Implementación pendiente de este paso..."
          />
        )
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

      {/* Progress Steps */}
      <Card>
        <CardHeader>
          <CardTitle>Progreso del Cierre</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-between">
            {Object.entries(ESTADOS)
              .filter(([key]) => !['rechazado'].includes(key))
              .map(([key, info], index) => (
                <div key={key} className="flex items-center">
                  <div className={`
                    flex items-center justify-center w-8 h-8 rounded-full text-sm font-medium
                    ${info.step <= estadoInfo.step 
                      ? 'bg-primary-600 text-white' 
                      : 'bg-secondary-700 text-secondary-400'
                    }
                  `}>
                    {info.step}
                  </div>
                  {index < 8 && (
                    <div className={`
                      w-12 h-0.5 mx-1
                      ${info.step < estadoInfo.step 
                        ? 'bg-primary-600' 
                        : 'bg-secondary-700'
                      }
                    `} />
                  )}
                </div>
              ))}
          </div>
          <div className="mt-4 text-center">
            <p className="text-secondary-400 text-sm">
              Paso actual: <span className="text-secondary-100 font-medium">{estadoInfo.label}</span>
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

export default CierreDetailPage
