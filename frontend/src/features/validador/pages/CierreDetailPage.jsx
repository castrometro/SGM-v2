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
  carga_archivos: { label: 'Carga de Archivos', color: 'info', step: 1 },
  clasificacion: { label: 'Clasificación', color: 'info', step: 2 },
  mapeo_novedades: { label: 'Mapeo Novedades', color: 'info', step: 3 },
  comparacion: { label: 'Comparación', color: 'warning', step: 4 },
  consolidacion: { label: 'Consolidación', color: 'warning', step: 5 },
  revision_incidencias: { label: 'Revisión Incidencias', color: 'warning', step: 6 },
  aprobacion_supervisor: { label: 'Aprobación Supervisor', color: 'primary', step: 7 },
  generacion_reportes: { label: 'Generación Reportes', color: 'info', step: 8 },
  completado: { label: 'Completado', color: 'success', step: 9 },
  rechazado: { label: 'Rechazado', color: 'danger', step: 0 },
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
        return <CargaArchivos cierreId={id} />
      
      case 'clasificacion':
        return (
          <PlaceholderStep 
            icon={Settings} 
            title="Clasificación de Conceptos" 
            description="Clasificando los conceptos del libro de remuneraciones..."
          />
        )
      
      case 'mapeo_novedades':
        return (
          <PlaceholderStep 
            icon={GitCompare} 
            title="Mapeo de Novedades" 
            description="Mapeando las novedades con los conceptos del ERP..."
          />
        )
      
      case 'comparacion':
        return (
          <PlaceholderStep 
            icon={GitCompare} 
            title="Comparación" 
            description="Comparando datos entre archivos ERP y del cliente..."
          />
        )
      
      case 'consolidacion':
        return (
          <PlaceholderStep 
            icon={FileText} 
            title="Consolidación" 
            description="Consolidando resultados de la comparación..."
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
      
      case 'aprobacion_supervisor':
        return (
          <PlaceholderStep 
            icon={CheckCircle} 
            title="Aprobación del Supervisor" 
            description="El cierre está pendiente de aprobación del supervisor..."
          />
        )
      
      case 'generacion_reportes':
        return (
          <PlaceholderStep 
            icon={FileBarChart} 
            title="Generación de Reportes" 
            description="Generando reportes finales del cierre..."
          />
        )
      
      case 'completado':
        return (
          <PlaceholderStep 
            icon={CheckCircle} 
            title="Cierre Completado" 
            description="El proceso de cierre ha finalizado exitosamente."
            variant="success"
          />
        )
      
      case 'rechazado':
        return (
          <PlaceholderStep 
            icon={AlertTriangle} 
            title="Cierre Rechazado" 
            description="El cierre ha sido rechazado y requiere correcciones."
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
          <h1 className="text-2xl font-bold text-secondary-100">
            {cierre.cliente_nombre}
          </h1>
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
