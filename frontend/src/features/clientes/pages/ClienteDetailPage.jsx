/**
 * Página de detalle de cliente
 * Muestra información del cliente, KPIs del último cierre y accesos rápidos
 */
import { useParams, useNavigate, Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { 
  ArrowLeft, 
  Building2, 
  Users, 
  DollarSign, 
  TrendingUp, 
  TrendingDown,
  FileCheck,
  History,
  PlusCircle,
  BarChart3,
  Mail,
  Phone,
  User,
  Globe,
  Calendar,
  Database
} from 'lucide-react'
import api from '../../../api/axios'
import { Card, CardContent, CardHeader, CardTitle, Badge, Button } from '../../../components/ui'

// Mock data para KPIs (último cierre)
const MOCK_KPIS = {
  periodo: 'Diciembre 2025',
  cantidadEmpleados: 1247,
  totalHaberesImponibles: 892450000,
  totalHaberesNoImponibles: 156780000,
  totalAportesPatronales: 178490000,
  totalDescuentosLegales: 223112500,
  totalOtrosDescuentos: 45670000,
}

// Formateador de moneda CLP
const formatCurrency = (value) => {
  return new Intl.NumberFormat('es-CL', {
    style: 'currency',
    currency: 'CLP',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(value)
}

// Formateador de números
const formatNumber = (value) => {
  return new Intl.NumberFormat('es-CL').format(value)
}

const ClienteDetailPage = () => {
  const { id } = useParams()
  const navigate = useNavigate()

  const { data: cliente, isLoading } = useQuery({
    queryKey: ['cliente', id],
    queryFn: async () => {
      const { data } = await api.get(`/v1/core/clientes/${id}/`)
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

  if (!cliente) {
    return (
      <div className="flex flex-col items-center justify-center h-64 text-secondary-400">
        <Building2 className="h-12 w-12 mb-4 opacity-50" />
        <p className="text-lg">Cliente no encontrado</p>
        <Button variant="ghost" onClick={() => navigate(-1)} className="mt-4">
          <ArrowLeft className="h-4 w-4 mr-2" />
          Volver
        </Button>
      </div>
    )
  }

  // KPIs Cards Data
  const kpiCards = [
    {
      title: 'Empleados',
      value: formatNumber(MOCK_KPIS.cantidadEmpleados),
      icon: Users,
      color: 'text-blue-400',
      bgColor: 'bg-blue-500/20',
    },
    {
      title: 'Haberes Imponibles',
      value: formatCurrency(MOCK_KPIS.totalHaberesImponibles),
      icon: TrendingUp,
      color: 'text-green-400',
      bgColor: 'bg-green-500/20',
    },
    {
      title: 'Haberes No Imponibles',
      value: formatCurrency(MOCK_KPIS.totalHaberesNoImponibles),
      icon: DollarSign,
      color: 'text-emerald-400',
      bgColor: 'bg-emerald-500/20',
    },
    {
      title: 'Aportes Patronales',
      value: formatCurrency(MOCK_KPIS.totalAportesPatronales),
      icon: Building2,
      color: 'text-purple-400',
      bgColor: 'bg-purple-500/20',
    },
    {
      title: 'Descuentos Legales',
      value: formatCurrency(MOCK_KPIS.totalDescuentosLegales),
      icon: TrendingDown,
      color: 'text-orange-400',
      bgColor: 'bg-orange-500/20',
    },
    {
      title: 'Otros Descuentos',
      value: formatCurrency(MOCK_KPIS.totalOtrosDescuentos),
      icon: TrendingDown,
      color: 'text-red-400',
      bgColor: 'bg-red-500/20',
    },
  ]

  // Acciones rápidas
  const quickActions = [
    {
      title: 'Cierre Actual',
      description: 'Ir al validador del cierre en proceso',
      icon: FileCheck,
      href: `/validador/cliente/${id}/cierre-actual`,
      color: 'bg-primary-600 hover:bg-primary-700',
    },
    {
      title: 'Historial de Cierres',
      description: 'Ver cierres anteriores',
      icon: History,
      href: `/validador/cliente/${id}/historial`,
      color: 'bg-secondary-700 hover:bg-secondary-600',
    },
    {
      title: 'Dashboard de Nómina',
      description: 'Análisis del último cierre',
      icon: BarChart3,
      href: `/validador/cliente/${id}/dashboard`,
      color: 'bg-teal-600 hover:bg-teal-700',
    },
    {
      title: 'Reportería',
      description: 'Informes ERP y exports',
      icon: PlusCircle,
      href: `/reporteria/cliente/${id}`,
      color: 'bg-indigo-600 hover:bg-indigo-700',
    },
  ]

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <button 
            onClick={() => navigate(-1)}
            className="p-2 rounded-lg hover:bg-secondary-800 transition-colors"
          >
            <ArrowLeft className="h-5 w-5 text-secondary-400" />
          </button>
          <div className="flex items-center gap-4">
            <div className="p-3 rounded-lg bg-primary-600/20">
              <Building2 className="h-6 w-6 text-primary-400" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-secondary-100">
                {cliente.nombre_display || cliente.nombre_comercial || cliente.razon_social}
              </h1>
              <div className="flex items-center gap-3 mt-1">
                <code className="text-sm bg-secondary-800 px-2 py-0.5 rounded text-secondary-300">
                  {cliente.rut}
                </code>
                <Badge variant={cliente.activo ? 'success' : 'secondary'}>
                  {cliente.activo ? 'Activo' : 'Inactivo'}
                </Badge>
                {cliente.bilingue && (
                  <Badge variant="info">
                    <Globe className="h-3 w-3 mr-1" />
                    Bilingüe
                  </Badge>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Acciones Rápidas */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {quickActions.map((action) => (
          <Link
            key={action.title}
            to={action.href}
            className={`${action.color} rounded-xl p-4 transition-all duration-200 transform hover:scale-[1.02] hover:shadow-lg`}
          >
            <div className="flex items-start gap-3">
              <action.icon className="h-6 w-6 text-white/90" />
              <div>
                <h3 className="font-semibold text-white">{action.title}</h3>
                <p className="text-sm text-white/70 mt-0.5">{action.description}</p>
              </div>
            </div>
          </Link>
        ))}
      </div>

      {/* Info del Cliente */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Building2 className="h-5 w-5 text-primary-400" />
            Información del Cliente
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {/* Datos de Identificación */}
            <div className="space-y-4">
              <h4 className="text-sm font-medium text-secondary-400 uppercase tracking-wide">
                Identificación
              </h4>
              <div className="space-y-3">
                <div>
                  <p className="text-xs text-secondary-500">Razón Social</p>
                  <p className="text-secondary-100">{cliente.razon_social || '-'}</p>
                </div>
                {cliente.nombre_comercial && cliente.nombre_comercial !== cliente.razon_social && (
                  <div>
                    <p className="text-xs text-secondary-500">Nombre Comercial</p>
                    <p className="text-secondary-100">{cliente.nombre_comercial}</p>
                  </div>
                )}
                <div>
                  <p className="text-xs text-secondary-500">Industria</p>
                  <p className="text-secondary-100">
                    {cliente.industria?.nombre || cliente.industria_nombre || '-'}
                  </p>
                </div>
                <div>
                  <p className="text-xs text-secondary-500">Sistema ERP</p>
                  <div className="flex items-center gap-2">
                    <Database className="h-4 w-4 text-secondary-500" />
                    <p className="text-secondary-100">
                      {cliente.erp_activo?.nombre || 
                        <span className="text-secondary-500 italic">Sin ERP asignado</span>
                      }
                    </p>
                  </div>
                </div>
              </div>
            </div>

            {/* Contacto */}
            <div className="space-y-4">
              <h4 className="text-sm font-medium text-secondary-400 uppercase tracking-wide">
                Contacto
              </h4>
              <div className="space-y-3">
                {cliente.contacto_nombre ? (
                  <>
                    <div className="flex items-center gap-2">
                      <User className="h-4 w-4 text-secondary-500" />
                      <span className="text-secondary-100">{cliente.contacto_nombre}</span>
                    </div>
                    {cliente.contacto_email && (
                      <div className="flex items-center gap-2">
                        <Mail className="h-4 w-4 text-secondary-500" />
                        <a 
                          href={`mailto:${cliente.contacto_email}`}
                          className="text-primary-400 hover:text-primary-300 transition-colors"
                        >
                          {cliente.contacto_email}
                        </a>
                      </div>
                    )}
                    {cliente.contacto_telefono && (
                      <div className="flex items-center gap-2">
                        <Phone className="h-4 w-4 text-secondary-500" />
                        <a 
                          href={`tel:${cliente.contacto_telefono}`}
                          className="text-secondary-100 hover:text-primary-400 transition-colors"
                        >
                          {cliente.contacto_telefono}
                        </a>
                      </div>
                    )}
                  </>
                ) : (
                  <p className="text-secondary-500 italic">Sin información de contacto</p>
                )}
              </div>
            </div>

            {/* Asignación */}
            <div className="space-y-4">
              <h4 className="text-sm font-medium text-secondary-400 uppercase tracking-wide">
                Asignación
              </h4>
              <div className="space-y-3">
                {cliente.usuario_asignado_info ? (
                  <div>
                    <p className="text-xs text-secondary-500">Analista Asignado</p>
                    <p className="text-secondary-100">{cliente.usuario_asignado_info.nombre}</p>
                    <p className="text-xs text-secondary-500">{cliente.usuario_asignado_info.email}</p>
                  </div>
                ) : (
                  <p className="text-secondary-500 italic">Sin analista asignado</p>
                )}
                {cliente.supervisor_heredado_info && (
                  <div>
                    <p className="text-xs text-secondary-500">Supervisor</p>
                    <p className="text-secondary-100">{cliente.supervisor_heredado_info.nombre}</p>
                  </div>
                )}
                {cliente.fecha_registro && (
                  <div className="flex items-center gap-2 text-secondary-500 text-sm">
                    <Calendar className="h-4 w-4" />
                    <span>Cliente desde {new Date(cliente.fecha_registro).toLocaleDateString('es-CL')}</span>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Notas */}
          {cliente.notas && (
            <div className="mt-6 pt-6 border-t border-secondary-700">
              <h4 className="text-sm font-medium text-secondary-400 uppercase tracking-wide mb-2">
                Notas
              </h4>
              <p className="text-secondary-300 whitespace-pre-wrap">{cliente.notas}</p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* KPIs del Último Cierre */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2">
              <BarChart3 className="h-5 w-5 text-primary-400" />
              KPIs del Último Cierre
            </CardTitle>
            <Badge variant="secondary">
              {MOCK_KPIS.periodo}
            </Badge>
          </div>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
            {kpiCards.map((kpi) => (
              <div
                key={kpi.title}
                className="bg-secondary-800/50 rounded-lg p-4 border border-secondary-700/50"
              >
                <div className="flex items-center gap-2 mb-2">
                  <div className={`p-1.5 rounded ${kpi.bgColor}`}>
                    <kpi.icon className={`h-4 w-4 ${kpi.color}`} />
                  </div>
                </div>
                <p className="text-xs text-secondary-500 mb-1">{kpi.title}</p>
                <p className={`text-lg font-bold ${kpi.color}`}>{kpi.value}</p>
              </div>
            ))}
          </div>
          
          {/* Nota sobre datos mock */}
          <div className="mt-4 p-3 bg-amber-500/10 border border-amber-500/30 rounded-lg">
            <p className="text-xs text-amber-400">
              ⚠️ Datos de ejemplo. Los KPIs reales se mostrarán una vez se procese el primer cierre del cliente.
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

export default ClienteDetailPage
