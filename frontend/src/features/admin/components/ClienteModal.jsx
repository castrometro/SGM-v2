/**
 * Modal para crear/editar Cliente
 */
import { Modal } from '../../../components/ui'
import ClienteForm from './ClienteForm'
import { useIndustrias, useCreateCliente, useUpdateCliente, useErpsActivos, useAsignarERP } from '../hooks/useClientes'
import { usePermissions } from '../../../hooks/usePermissions'
import { toast } from 'react-hot-toast'

const ClienteModal = ({ isOpen, onClose, cliente = null }) => {
  const isEditing = !!cliente
  const { isGerente } = usePermissions()
  
  const { data: industrias = [] } = useIndustrias()
  const { data: erps = [] } = useErpsActivos()
  const createMutation = useCreateCliente()
  const updateMutation = useUpdateCliente()
  const asignarERPMutation = useAsignarERP()

  const isLoading = createMutation.isPending || updateMutation.isPending || asignarERPMutation.isPending

  const handleSubmit = async (data) => {
    try {
      const { erp_id, ...clienteData } = data
      
      if (isEditing) {
        await updateMutation.mutateAsync({ id: cliente.id, ...clienteData })
        
        // Si es gerente y cambió el ERP, actualizar
        if (isGerente && erp_id !== undefined) {
          const currentErpId = cliente.erp_activo?.id || null
          const newErpId = erp_id || null
          
          if (currentErpId !== newErpId) {
            await asignarERPMutation.mutateAsync({ 
              clienteId: cliente.id, 
              erpId: newErpId 
            })
          }
        }
        
        toast.success('Cliente actualizado correctamente')
      } else {
        const newCliente = await createMutation.mutateAsync(clienteData)
        
        // Si es gerente y seleccionó un ERP, asignarlo
        if (isGerente && erp_id) {
          await asignarERPMutation.mutateAsync({ 
            clienteId: newCliente.id, 
            erpId: erp_id 
          })
        }
        
        toast.success('Cliente creado correctamente')
      }
      onClose()
    } catch (error) {
      const message = error.response?.data?.detail || 
                      error.response?.data?.error ||
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
        erps={isGerente ? erps : []}
        showErpField={isGerente}
        onSubmit={handleSubmit}
        onCancel={onClose}
        isLoading={isLoading}
      />
    </Modal>
  )
}

export default ClienteModal
