/**
 * Dashboard de Movimientos de Personal
 * Ingresos, finiquitos, ausencias y ausentismo
 * 
 * TODO: Implementar con datos reales del backend
 * - Tarjetas de métricas (ingresos, finiquitos, días ausencia, vacaciones)
 * - Gráficos de distribución
 * - Tabla de movimientos con filtros
 * - Top empleados con más ausencias
 */
import { useParams, useNavigate, useSearchParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { 
  ArrowLeft, 
  Users,
  UserPlus,
  UserMinus,
  Calendar,
  Clock,
  AlertCircle,
} from 'lucide-react'
import api from '@/api/axios'
import { Card, CardContent, CardHeader, CardTitle, Badge } from '@/components/ui'
import { VariacionBadge } from '../components'
import { formatNumber, formatPeriodo } from '../utils'

// Mock data (TODO: obtener del backend)
const MOCK_MOVIMIENTOS = {
  periodo: '2025-12',
  periodoAnterior: '2025-11',
  metricas: {
    ingresos: { actual: 32, anterior: 28 },
    finiquitos: { actual: 15, anterior: 18 },
    diasAusenciaJustificada: { actual: 245, anterior: 220 },
    diasVacaciones: { actual: 180, anterior: 165 },
    ausSinJustificar: { actual: 12, anterior: 8 },
  }
}

const MovimientosDashboardPage = () => {
  const { clienteId } = useParams()
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const periodo = searchParams.get('periodo') || MOCK_MOVIMIENTOS.periodo

  // Obtener info del cliente
  const { data: cliente } = useQuery({
    queryKey: ['cliente', clienteId],
    queryFn: async () => {
      const { data } = await api.get(`/v1/core/clientes/${clienteId}/`)
      return data
    },
  })

  const { metricas } = MOCK_MOVIMIENTOS

  // Tarjetas de métricas
  const tarjetas = [
    {
      key: 'ingresos',
      title: 'Ingresos',
      icon: UserPlus,
      color: 'text-green-400',
      bgColor: 'bg-green-500/20',
      borderColor: 'border-green-500/30',
      actual: metricas.ingresos.actual,
      anterior: metricas.ingresos.anterior,
      tipo: 'personas',
    },
    {
      key: 'finiquitos',
      title: 'Finiquitos',
      icon: UserMinus,
      color: 'text-red-400',
      bgColor: 'bg-red-500/20',
      borderColor: 'border-red-500/30',
      actual: metricas.finiquitos.actual,
      anterior: metricas.finiquitos.anterior,
      tipo: 'personas',
      invertColor: true,
    },
    {
      key: 'ausenciaJustificada',
      title: 'Días Ausencia Justificada',
      icon: Calendar,
      color: 'text-amber-400',
      bgColor: 'bg-amber-500/20',
      borderColor: 'border-amber-500/30',
      actual: metricas.diasAusenciaJustificada.actual,
      anterior: metricas.diasAusenciaJustificada.anterior,
      tipo: 'días',
    },
    {
      key: 'vacaciones',
      title: 'Días Vacaciones',
      icon: Clock,
      color: 'text-blue-400',
      bgColor: 'bg-blue-500/20',
      borderColor: 'border-blue-500/30',
      actual: metricas.diasVacaciones.actual,
      anterior: metricas.diasVacaciones.anterior,
      tipo: 'días',
    },
    {
      key: 'sinJustificar',
      title: 'Ausencias Sin Justificar',
      icon: AlertCircle,
      color: 'text-rose-400',
      bgColor: 'bg-rose-500/20',
      borderColor: 'border-rose-500/30',
      actual: metricas.ausSinJustificar.actual,
      anterior: metricas.ausSinJustificar.anterior,
      tipo: 'eventos',
      invertColor: true,
    },
  ]

  // Calcular balance neto
  const balanceNeto = metricas.ingresos.actual - metricas.finiquitos.actual
  const balanceNetoAnterior = metricas.ingresos.anterior - metricas.finiquitos.anterior

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <button 
            onClick={() => navigate(`/validador/cliente/${clienteId}/dashboard`)}
            className="p-2 rounded-lg hover:bg-secondary-800 transition-colors"
          >
            <ArrowLeft className="h-5 w-5 text-secondary-400" />
          </button>
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-blue-500/20">
              <Users className="h-6 w-6 text-blue-400" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-secondary-100">Movimientos de Personal</h1>
              <p className="text-secondary-400">
                {cliente?.nombre_display || cliente?.razon_social || 'Cliente'}
              </p>
            </div>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant="secondary">{formatPeriodo(MOCK_MOVIMIENTOS.periodoAnterior)}</Badge>
          <span className="text-secondary-500">→</span>
          <Badge variant="primary">{formatPeriodo(periodo)}</Badge>
        </div>
      </div>

      {/* Tarjetas de Métricas */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
        {tarjetas.map((t) => (
          <Card key={t.key} className={`${t.borderColor} hover:border-opacity-60 transition-colors cursor-pointer`}>
            <CardContent className="p-4">
              <div className="flex items-center gap-2 mb-3">
                <div className={`p-1.5 rounded ${t.bgColor}`}>
                  <t.icon className={`h-4 w-4 ${t.color}`} />
                </div>
              </div>
              <p className="text-xs text-secondary-500 uppercase tracking-wide mb-1">{t.title}</p>
              <p className={`text-2xl font-bold ${t.color} mb-1`}>{formatNumber(t.actual)}</p>
              <div className="flex items-center justify-between">
                <span className="text-xs text-secondary-500">{t.tipo}</span>
                <VariacionBadge actual={t.actual} anterior={t.anterior} invertColor={t.invertColor} />
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Balance Neto */}
      <Card className={`border-2 ${balanceNeto >= 0 ? 'border-green-500/30 bg-green-500/5' : 'border-red-500/30 bg-red-500/5'}`}>
        <CardContent className="p-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className={`p-3 rounded-lg ${balanceNeto >= 0 ? 'bg-green-500/20' : 'bg-red-500/20'}`}>
                <Users className={`h-8 w-8 ${balanceNeto >= 0 ? 'text-green-400' : 'text-red-400'}`} />
              </div>
              <div>
                <p className="text-sm text-secondary-400 uppercase tracking-wide">Balance Neto (Ingresos - Finiquitos)</p>
                <p className={`text-3xl font-bold ${balanceNeto >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                  {balanceNeto >= 0 ? '+' : ''}{formatNumber(balanceNeto)} empleados
                </p>
              </div>
            </div>
            <div className="text-right">
              <p className="text-sm text-secondary-500 mb-1">
                Mes anterior: {balanceNetoAnterior >= 0 ? '+' : ''}{formatNumber(balanceNetoAnterior)}
              </p>
              <VariacionBadge actual={balanceNeto} anterior={balanceNetoAnterior} />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Placeholder para gráficos */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Distribución de Movimientos</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-64 flex items-center justify-center text-secondary-500 border-2 border-dashed border-secondary-700 rounded-lg">
              📊 Gráfico de Barras (próximamente)
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Ausentismo por Motivo</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-64 flex items-center justify-center text-secondary-500 border-2 border-dashed border-secondary-700 rounded-lg">
              🍩 Gráfico Donut (próximamente)
            </div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Detalle de Movimientos</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-48 flex items-center justify-center text-secondary-500 border-2 border-dashed border-secondary-700 rounded-lg">
            📋 Tabla de movimientos con filtros por tipo (próximamente)
          </div>
        </CardContent>
      </Card>

      {/* Notice */}
      <div className="p-3 bg-amber-500/10 border border-amber-500/30 rounded-lg">
        <p className="text-xs text-amber-400">
          ⚠️ Dashboard en desarrollo. Los datos mostrados son de ejemplo.
        </p>
      </div>
    </div>
  )
}

export default MovimientosDashboardPage
