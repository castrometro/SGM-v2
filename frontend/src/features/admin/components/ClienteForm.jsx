/**
 * Formulario de Cliente (crear/editar)
 */
import { useForm } from 'react-hook-form'
import { Input, Select, Textarea, Checkbox, Button } from '../../../components/ui'

const ClienteForm = ({ 
  cliente = null, 
  industrias = [], 
  erps = [],
  showErpField = false,
  onSubmit, 
  onCancel,
  isLoading = false 
}) => {
  const isEditing = !!cliente

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm({
    defaultValues: cliente ? {
      ...cliente,
      industria: cliente.industria?.id || cliente.industria || '',
      erp_id: cliente.erp_activo?.id || '',
    } : {
      rut: '',
      razon_social: '',
      nombre_comercial: '',
      industria: '',
      erp_id: '',
      bilingue: false,
      contacto_nombre: '',
      contacto_email: '',
      contacto_telefono: '',
      notas: '',
      activo: true,
    },
  })

  const industriaOptions = industrias.map((ind) => ({
    value: ind.id,
    label: ind.nombre,
  }))

  const erpOptions = erps.map((erp) => ({
    value: erp.id,
    label: erp.nombre,
  }))

  const handleFormSubmit = (data) => {
    // Convertir string vacío a null para industria y erp_id
    const submitData = {
      ...data,
      industria: data.industria || null,
      erp_id: data.erp_id || null,
    }
    onSubmit(submitData)
  }

  return (
    <form onSubmit={handleSubmit(handleFormSubmit)} className="space-y-6">
      {/* Sección: Identificación */}
      <div className="space-y-4">
        <h3 className="text-sm font-semibold text-secondary-400 uppercase tracking-wider">
          Identificación
        </h3>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Input
            label="RUT"
            placeholder="12345678-9"
            error={errors.rut?.message}
            {...register('rut', {
              required: 'El RUT es requerido',
              pattern: {
                value: /^\d{7,8}-[\dkK]$/,
                message: 'Formato inválido. Use: 12345678-9',
              },
            })}
          />
          
          <Input
            label="Razón Social"
            placeholder="Nombre legal de la empresa"
            error={errors.razon_social?.message}
            {...register('razon_social', {
              required: 'La razón social es requerida',
              minLength: {
                value: 3,
                message: 'Mínimo 3 caracteres',
              },
            })}
          />
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Input
            label="Nombre Comercial"
            placeholder="Nombre con el que se conoce"
            helperText="Opcional - si es diferente a la razón social"
            {...register('nombre_comercial')}
          />
          
          <Select
            label="Industria"
            options={industriaOptions}
            placeholder="Seleccione una industria"
            {...register('industria')}
          />
        </div>
      </div>

      {/* Sección: Contacto */}
      <div className="space-y-4">
        <h3 className="text-sm font-semibold text-secondary-400 uppercase tracking-wider">
          Contacto Principal
        </h3>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Input
            label="Nombre"
            placeholder="Nombre del contacto"
            {...register('contacto_nombre')}
          />
          
          <Input
            type="email"
            label="Email"
            placeholder="email@empresa.cl"
            error={errors.contacto_email?.message}
            {...register('contacto_email', {
              pattern: {
                value: /^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$/i,
                message: 'Email inválido',
              },
            })}
          />
          
          <Input
            type="tel"
            label="Teléfono"
            placeholder="+56 9 1234 5678"
            {...register('contacto_telefono')}
          />
        </div>
      </div>

      {/* Sección: Configuración */}
      <div className="space-y-4">
        <h3 className="text-sm font-semibold text-secondary-400 uppercase tracking-wider">
          Configuración
        </h3>
        
        {showErpField && (
          <Select
            label="Sistema ERP"
            options={erpOptions}
            placeholder="Seleccione un ERP"
            helperText="Sistema ERP asignado al cliente para validaciones"
            {...register('erp_id')}
          />
        )}
        
        <div className="flex flex-wrap gap-6">
          <Checkbox
            label="Cliente bilingüe (requiere informes en español e inglés)"
            {...register('bilingue')}
          />
          
          <Checkbox
            label="Cliente activo"
            {...register('activo')}
          />
        </div>
      </div>

      {/* Sección: Notas */}
      <div className="space-y-4">
        <h3 className="text-sm font-semibold text-secondary-400 uppercase tracking-wider">
          Notas Internas
        </h3>
        
        <Textarea
          placeholder="Notas internas sobre el cliente..."
          rows={3}
          {...register('notas')}
        />
      </div>

      {/* Acciones */}
      <div className="flex items-center justify-end gap-3 pt-4 border-t border-secondary-800">
        <Button 
          type="button" 
          variant="outline" 
          onClick={onCancel}
          disabled={isLoading}
        >
          Cancelar
        </Button>
        <Button 
          type="submit" 
          loading={isLoading}
        >
          {isEditing ? 'Guardar Cambios' : 'Crear Cliente'}
        </Button>
      </div>
    </form>
  )
}

export default ClienteForm
