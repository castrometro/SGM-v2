/**
 * Dashboard de Libro de Remuneraciones
 * Análisis de haberes, descuentos y aportes patronales
 * 
 * TODO: Implementar con datos reales del backend
 * - Selector de período
 * - Comparación con mes anterior
 * - Tarjetas comparativas por categoría
 * - Gráficos de barras y donut
 * - Tabla de conceptos con búsqueda y paginación
 */
import { useParams, useNavigate, useSearchParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { 
  ArrowLeft, 
  BookOpen,
  TrendingUp,
  TrendingDown,
  DollarSign,
  Building2,
  Users,
} from 'lucide-react'
import api from '@/api/axios'
import { Card, CardContent, CardHeader, CardTitle, Badge } from '@/components/ui'
import { VariacionBadge } from '../components'
import { formatCurrency, formatNumber, formatPeriodo } from '../utils'

// Mock data (TODO: obtener del backend)
const MOCK_LIBRO = {
  periodo: '2025-12',
  periodoAnterior: '2025-11',
  totales: {
    empleados: { actual: 1247, anterior: 1215 },
    haberImponible: { actual: 892450000, anterior: 865230000 },
    haberNoImponible: { actual: 156780000, anterior: 148920000 },
    descuentoLegal: { actual: 223112500, anterior: 216307500 },
    otroDescuento: { actual: 45670000, anterior: 42890000 },
    aportePatronal: { actual: 178490000, anterior: 173046000 },
    liquidoAPagar: { actual: 780447500, anterior: 754952500 },
  }
}

const LibroDashboardPage = () => {
  const { clienteId } = useParams()
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const periodo = searchParams.get('periodo') || MOCK_LIBRO.periodo

  // Obtener info del cliente
  const { data: cliente } = useQuery({
    queryKey: ['cliente', clienteId],
    queryFn: async () => {
      const { data } = await api.get(`/v1/core/clientes/${clienteId}/`)
      return data
    },
  })

  const { totales } = MOCK_LIBRO

  // Tarjetas de categorías
  const categorias = [
    {
      key: 'empleados',
      title: 'Empleados',
      icon: Users,
      color: 'text-blue-400',
      bgColor: 'bg-blue-500/20',
      actual: totales.empleados.actual,
      anterior: totales.empleados.anterior,
      format: formatNumber,
    },
    {
      key: 'haberImponible',
      title: 'Haberes Imponibles',
      icon: TrendingUp,
      color: 'text-green-400',
      bgColor: 'bg-green-500/20',
      actual: totales.haberImponible.actual,
      anterior: totales.haberImponible.anterior,
      format: formatCurrency,
    },
    {
      key: 'haberNoImponible',
      title: 'Haberes No Imponibles',
      icon: DollarSign,
      color: 'text-emerald-400',
      bgColor: 'bg-emerald-500/20',
      actual: totales.haberNoImponible.actual,
      anterior: totales.haberNoImponible.anterior,
      format: formatCurrency,
    },
    {
      key: 'descuentoLegal',
      title: 'Descuentos Legales',
      icon: TrendingDown,
      color: 'text-orange-400',
      bgColor: 'bg-orange-500/20',
      actual: totales.descuentoLegal.actual,
      anterior: totales.descuentoLegal.anterior,
      format: formatCurrency,
      invertColor: true,
    },
    {
      key: 'otroDescuento',
      title: 'Otros Descuentos',
      icon: TrendingDown,
      color: 'text-red-400',
      bgColor: 'bg-red-500/20',
      actual: totales.otroDescuento.actual,
      anterior: totales.otroDescuento.anterior,
      format: formatCurrency,
      invertColor: true,
    },
    {
      key: 'aportePatronal',
      title: 'Aportes Patronales',
      icon: Building2,
      color: 'text-purple-400',
      bgColor: 'bg-purple-500/20',
      actual: totales.aportePatronal.actual,
      anterior: totales.aportePatronal.anterior,
      format: formatCurrency,
    },
  ]

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
            <div className="p-2 rounded-lg bg-green-500/20">
              <BookOpen className="h-6 w-6 text-green-400" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-secondary-100">Libro de Remuneraciones</h1>
              <p className="text-secondary-400">
                {cliente?.nombre_display || cliente?.razon_social || 'Cliente'}
              </p>
            </div>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant="secondary">{formatPeriodo(MOCK_LIBRO.periodoAnterior)}</Badge>
          <span className="text-secondary-500">→</span>
          <Badge variant="primary">{formatPeriodo(periodo)}</Badge>
        </div>
      </div>

      {/* Tarjetas Comparativas */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
        {categorias.map((cat) => (
          <Card key={cat.key} className="hover:border-secondary-600 transition-colors cursor-pointer">
            <CardContent className="p-4">
              <div className="flex items-center gap-2 mb-3">
                <div className={`p-1.5 rounded ${cat.bgColor}`}>
                  <cat.icon className={`h-4 w-4 ${cat.color}`} />
                </div>
              </div>
              <p className="text-xs text-secondary-500 uppercase tracking-wide mb-1">{cat.title}</p>
              <p className={`text-lg font-bold ${cat.color} mb-1`}>{cat.format(cat.actual)}</p>
              <div className="flex items-center justify-between">
                <span className="text-xs text-secondary-500">Prev: {cat.format(cat.anterior)}</span>
                <VariacionBadge actual={cat.actual} anterior={cat.anterior} invertColor={cat.invertColor} />
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Líquido a Pagar destacado */}
      <Card className="border-primary-500/30 bg-primary-500/5">
        <CardContent className="p-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="p-3 rounded-lg bg-primary-500/20">
                <DollarSign className="h-8 w-8 text-primary-400" />
              </div>
              <div>
                <p className="text-sm text-secondary-400 uppercase tracking-wide">Líquido a Pagar</p>
                <p className="text-3xl font-bold text-primary-400">{formatCurrency(totales.liquidoAPagar.actual)}</p>
              </div>
            </div>
            <div className="text-right">
              <p className="text-sm text-secondary-500 mb-1">Mes anterior: {formatCurrency(totales.liquidoAPagar.anterior)}</p>
              <VariacionBadge actual={totales.liquidoAPagar.actual} anterior={totales.liquidoAPagar.anterior} />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Placeholder para gráficos y tabla */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Distribución por Categoría</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-64 flex items-center justify-center text-secondary-500 border-2 border-dashed border-secondary-700 rounded-lg">
              📊 Gráfico de Barras (próximamente)
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Composición Porcentual</CardTitle>
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
          <CardTitle>Detalle de Conceptos</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-48 flex items-center justify-center text-secondary-500 border-2 border-dashed border-secondary-700 rounded-lg">
            📋 Tabla de conceptos con búsqueda, ordenamiento y paginación (próximamente)
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

export default LibroDashboardPage
