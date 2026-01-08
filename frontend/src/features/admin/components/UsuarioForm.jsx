/**
 * Formulario de Usuario (crear/editar)
 */
import { useForm } from 'react-hook-form'
import { Input, Select, Button } from '../../../components/ui'
import { TIPO_USUARIO, TIPO_USUARIO_BADGE } from '../../../constants'

const UsuarioForm = ({ 
  usuario = null, 
  supervisores = [], 
  onSubmit, 
  onCancel,
  isLoading = false 
}) => {
  const isEditing = !!usuario

  const {
    register,
    handleSubmit,
    watch,
    formState: { errors },
  } = useForm({
    defaultValues: usuario ? {
      email: usuario.email,
      nombre: usuario.nombre,
      apellido: usuario.apellido,
      tipo_usuario: usuario.tipo_usuario,
      cargo: usuario.cargo || '',
      supervisor: usuario.supervisor || '',
      is_active: usuario.is_active,
    } : {
      email: '',
      nombre: '',
      apellido: '',
      tipo_usuario: TIPO_USUARIO.ANALISTA,
      cargo: '',
      supervisor: '',
      password: '',
      password_confirm: '',
    },
  })

  const tipoUsuario = watch('tipo_usuario')

  const tipoUsuarioOptions = [
    { value: TIPO_USUARIO.ANALISTA, label: TIPO_USUARIO_BADGE[TIPO_USUARIO.ANALISTA].label },
    { value: TIPO_USUARIO.SUPERVISOR, label: TIPO_USUARIO_BADGE[TIPO_USUARIO.SUPERVISOR].label },
    { value: TIPO_USUARIO.GERENTE, label: TIPO_USUARIO_BADGE[TIPO_USUARIO.GERENTE].label },
  ]

  const supervisorOptions = supervisores
    .filter(s => s.id !== usuario?.id) // No puede ser su propio supervisor
    .map((sup) => ({
      value: sup.id,
      label: `${sup.nombre} ${sup.apellido}`,
    }))

  const handleFormSubmit = (data) => {
    // Convertir string vacío a null para supervisor
    const submitData = {
      ...data,
      supervisor: data.supervisor || null,
    }
    onSubmit(submitData)
  }

  return (
    <form onSubmit={handleSubmit(handleFormSubmit)} className="space-y-6">
      {/* Sección: Datos Personales */}
      <div className="space-y-4">
        <h3 className="text-sm font-semibold text-secondary-400 uppercase tracking-wider">
          Datos Personales
        </h3>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Input
            label="Nombre"
            placeholder="Nombre del usuario"
            error={errors.nombre?.message}
            {...register('nombre', {
              required: 'El nombre es requerido',
              minLength: {
                value: 2,
                message: 'Mínimo 2 caracteres',
              },
            })}
          />
          
          <Input
            label="Apellido"
            placeholder="Apellido del usuario"
            error={errors.apellido?.message}
            {...register('apellido', {
              required: 'El apellido es requerido',
              minLength: {
                value: 2,
                message: 'Mínimo 2 caracteres',
              },
            })}
          />
        </div>

        <Input
          type="email"
          label="Email"
          placeholder="usuario@empresa.cl"
          error={errors.email?.message}
          {...register('email', {
            required: 'El email es requerido',
            pattern: {
              value: /^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$/i,
              message: 'Email inválido',
            },
          })}
        />
      </div>

      {/* Sección: Rol y Organización */}
      <div className="space-y-4">
        <h3 className="text-sm font-semibold text-secondary-400 uppercase tracking-wider">
          Rol y Organización
        </h3>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Select
            label="Tipo de Usuario"
            options={tipoUsuarioOptions}
            error={errors.tipo_usuario?.message}
            {...register('tipo_usuario', {
              required: 'El tipo de usuario es requerido',
            })}
          />
          
          <Input
            label="Cargo"
            placeholder="Ej: Analista Senior, Jefe de Nómina"
            helperText="Opcional"
            {...register('cargo')}
          />
        </div>

        {/* Solo mostrar selector de supervisor para analistas */}
        {tipoUsuario === TIPO_USUARIO.ANALISTA && (
          <Select
            label="Supervisor Asignado"
            options={supervisorOptions}
            placeholder="Seleccione un supervisor"
            helperText="Opcional - puede asignarse después"
            {...register('supervisor')}
          />
        )}
      </div>

      {/* Sección: Contraseña (solo para nuevo usuario) */}
      {!isEditing && (
        <div className="space-y-4">
          <h3 className="text-sm font-semibold text-secondary-400 uppercase tracking-wider">
            Contraseña
          </h3>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Input
              type="password"
              label="Contraseña"
              placeholder="Mínimo 8 caracteres"
              error={errors.password?.message}
              {...register('password', {
                required: 'La contraseña es requerida',
                minLength: {
                  value: 8,
                  message: 'Mínimo 8 caracteres',
                },
              })}
            />
            
            <Input
              type="password"
              label="Confirmar Contraseña"
              placeholder="Repita la contraseña"
              error={errors.password_confirm?.message}
              {...register('password_confirm', {
                required: 'Confirme la contraseña',
                validate: (value) => {
                  const password = watch('password')
                  return value === password || 'Las contraseñas no coinciden'
                },
              })}
            />
          </div>
        </div>
      )}

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
          {isEditing ? 'Guardar Cambios' : 'Crear Usuario'}
        </Button>
      </div>
    </form>
  )
}

export default UsuarioForm
