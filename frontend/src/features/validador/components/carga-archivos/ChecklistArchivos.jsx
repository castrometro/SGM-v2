/**
 * Checklist de archivos con estado y botón de continuar
 * Muestra los 8 items requeridos y permite avanzar cuando todo está listo
 */
import { FileCheck, CheckCircle, Circle, ArrowRight, Loader2 } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '../../../../components/ui'
import Badge from '../../../../components/ui/Badge'
import Button from '../../../../components/ui/Button'
import { cn } from '../../../../utils/cn'

/**
 * @param {Object} props
 * @param {Object} props.cierre - Datos del cierre con archivos_listos_status
 * @param {Function} props.onContinuar - Callback cuando se hace click en continuar
 * @param {boolean} props.isPending - Si está procesando la acción de continuar
 */
const ChecklistArchivos = ({ cierre, onContinuar, isPending }) => {
  // Calcular estado del checklist usando datos del cierre
  const archivosListosStatus = cierre?.archivos_listos_status || {}
  
  const checklistItems = [
    {
      key: 'libro',
      label: 'Libro de Remuneraciones',
      done: archivosListosStatus.detalle?.erp?.libro_remuneraciones?.listo || false,
    },
    {
      key: 'movimientos',
      label: 'Movimientos del Mes',
      done: archivosListosStatus.detalle?.erp?.movimientos_mes?.listo || false,
    },
    {
      key: 'novedades',
      label: 'Novedades',
      done: archivosListosStatus.detalle?.analista?.novedades?.listo || false,
    },
    {
      key: 'asistencias',
      label: 'Asistencias',
      done: archivosListosStatus.detalle?.analista?.asistencias?.listo || false,
    },
    {
      key: 'finiquitos',
      label: 'Finiquitos',
      done: archivosListosStatus.detalle?.analista?.finiquitos?.listo || false,
    },
    {
      key: 'ingresos',
      label: 'Ingresos',
      done: archivosListosStatus.detalle?.analista?.ingresos?.listo || false,
    },
    {
      key: 'clasificacion',
      label: 'Clasificación de Conceptos',
      done: archivosListosStatus.detalle?.clasificacion_completa || false,
    },
    {
      key: 'mapeo',
      label: 'Mapeo de Headers',
      done: archivosListosStatus.detalle?.mapeo_completo || false,
    },
  ]
  
  const todoListo = archivosListosStatus.listos || false

  return (
    <Card className={cn(
      "border-2 transition-colors",
      todoListo ? "border-green-500/50 bg-green-500/5" : "border-secondary-700"
    )}>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <FileCheck className="h-5 w-5 text-primary-400" />
            <CardTitle className="text-base">Estado de Archivos</CardTitle>
          </div>
          <Badge variant={todoListo ? "success" : "warning"}>
            {checklistItems.filter(i => i.done).length} / {checklistItems.length} completados
          </Badge>
        </div>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
          {checklistItems.map((item) => (
            <div
              key={item.key}
              className={cn(
                "flex items-center gap-2 p-2 rounded-lg text-sm",
                item.done 
                  ? "bg-green-500/10 text-green-400" 
                  : "bg-secondary-800 text-secondary-400"
              )}
            >
              {item.done ? (
                <CheckCircle className="h-4 w-4 flex-shrink-0" />
              ) : (
                <Circle className="h-4 w-4 flex-shrink-0" />
              )}
              <span className="truncate">{item.label}</span>
            </div>
          ))}
        </div>
        
        {todoListo ? (
          <div className="flex items-center justify-between pt-3 border-t border-secondary-700">
            <p className="text-sm text-green-400">
              ✓ Todos los archivos están listos para continuar
            </p>
            <Button
              onClick={onContinuar}
              disabled={isPending}
              className="bg-green-600 hover:bg-green-700"
            >
              {isPending ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Procesando...
                </>
              ) : (
                <>
                  Continuar
                  <ArrowRight className="h-4 w-4 ml-2" />
                </>
              )}
            </Button>
          </div>
        ) : (
          <div className="pt-3 border-t border-secondary-700">
            <p className="text-sm text-secondary-400">
              Completa los elementos pendientes para continuar al siguiente paso
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  )
}

export default ChecklistArchivos
