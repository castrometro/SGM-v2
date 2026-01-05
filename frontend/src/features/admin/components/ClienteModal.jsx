/**
 * Modal para crear/editar Cliente
 */
import { Modal } from '../../../components/ui'
import ClienteForm from './ClienteForm'
import { useIndustrias, useCreateCliente, useUpdateCliente } from '../hooks/useClientes'
import { toast } from 'react-hot-toast'

const ClienteModal = ({ isOpen, onClose, cliente = null }) => {
  const isEditing = !!cliente
  
  const { data: industrias = [] } = useIndustrias()
  const createMutation = useCreateCliente()
  const updateMutation = useUpdateCliente()

  const isLoading = createMutation.isPending || updateMutation.isPending

  const handleSubmit = async (data) => {
    try {
      if (isEditing) {
        await updateMutation.mutateAsync({ id: cliente.id, ...data })
        toast.success('Cliente actualizado correctamente')
      } else {
        await createMutation.mutateAsync(data)
        toast.success('Cliente creado correctamente')
      }
      onClose()
    } catch (error) {
      const message = error.response?.data?.detail || 
                      error.response?.data?.rut?.[0] ||
                      'Error al guardar el cliente'
      toast.error(message)
    }
  }

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={isEditing ? 'Editar Cliente' : 'Nuevo Cliente'}
      description={isEditing 
        ? `Editando: ${cliente.razon_social}` 
        : 'Complete los datos del nuevo cliente'
      }
      size="lg"
    >
      <ClienteForm
        cliente={cliente}
        industrias={industrias}
        onSubmit={handleSubmit}
        onCancel={onClose}
        isLoading={isLoading}
      />
    </Modal>
  )
}

export default ClienteModal
