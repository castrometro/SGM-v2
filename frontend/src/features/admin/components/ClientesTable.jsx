/**
 * Tabla de Clientes con acciones
 */
import { useState } from 'react'
import { Building2, Edit2, Trash2, ToggleLeft, ToggleRight, Eye, Users } from 'lucide-react'
import { Table, Badge, Button, ConfirmDialog } from '../../../components/ui'
import { useToggleClienteActivo, useDeleteCliente } from '../hooks/useClientes'
import { toast } from 'react-hot-toast'

const ClientesTable = ({ clientes = [], onEdit, onView, onManageAsignaciones }) => {
  const [deleteModal, setDeleteModal] = useState({ open: false, cliente: null })
  
  const toggleMutation = useToggleClienteActivo()
  const deleteMutation = useDeleteCliente()

  const handleToggleActivo = async (cliente) => {
    try {
      await toggleMutation.mutateAsync({ 
        id: cliente.id, 
        activo: !cliente.activo 
      })
      toast.success(
        cliente.activo 
          ? 'Cliente desactivado' 
          : 'Cliente activado'
      )
    } catch (error) {
      toast.error('Error al cambiar estado del cliente')
    }
  }

  const handleDelete = async () => {
    try {
      await deleteMutation.mutateAsync(deleteModal.cliente.id)
      toast.success('Cliente eliminado correctamente')
      setDeleteModal({ open: false, cliente: null })
    } catch (error) {
      toast.error('Error al eliminar el cliente')
    }
  }

  if (clientes.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-12 text-secondary-500">
        <Building2 className="h-12 w-12 mb-4 opacity-50" />
        <p className="text-lg font-medium">No hay clientes</p>
        <p className="text-sm">Crea un nuevo cliente para comenzar</p>
      </div>
    )
  }

  return (
    <>
      <Table>
        <Table.Header>
          <Table.Row hoverable={false}>
            <Table.Head>Cliente</Table.Head>
            <Table.Head>RUT</Table.Head>
            <Table.Head>Industria</Table.Head>
            <Table.Head>Asignaciones</Table.Head>
            <Table.Head>Contacto</Table.Head>
            <Table.Head align="center">Estado</Table.Head>
            <Table.Head align="right">Acciones</Table.Head>
          </Table.Row>
        </Table.Header>
        <Table.Body>
          {clientes.map((cliente) => (
            <Table.Row key={cliente.id}>
              <Table.Cell>
                <div className="flex items-center gap-3">
                  <div className="p-2 rounded-lg bg-primary-600/20">
                    <Building2 className="h-4 w-4 text-primary-400" />
                  </div>
                  <div>
                    <p className="font-medium text-secondary-100">
                      {cliente.nombre_display || cliente.razon_social}
                    </p>
                    {cliente.nombre_comercial && cliente.nombre_comercial !== cliente.razon_social && (
                      <p className="text-xs text-secondary-500">
                        {cliente.razon_social}
                      </p>
                    )}
                  </div>
                </div>
              </Table.Cell>
              <Table.Cell>
                <code className="text-sm bg-secondary-800 px-2 py-0.5 rounded">
                  {cliente.rut}
                </code>
              </Table.Cell>
              <Table.Cell>
                {cliente.industria_nombre ? (
                  <Badge variant="secondary">
                    {cliente.industria_nombre}
                  </Badge>
                ) : (
                  <span className="text-secondary-500 text-sm">Sin industria</span>
                )}
              </Table.Cell>
              <Table.Cell>
                <button
                  onClick={() => onManageAsignaciones && onManageAsignaciones(cliente)}
                  className="flex flex-col gap-1 text-left hover:bg-secondary-800 rounded-lg p-1.5 -m-1.5 transition-colors"
                  title="Gestionar asignaciones"
                >
                  {cliente.supervisor_nombre ? (
                    <span className="text-xs text-secondary-300">
                      <span className="text-secondary-500">Sup:</span> {cliente.supervisor_nombre}
                    </span>
                  ) : (
                    <span className="text-xs text-warning-400">Sin supervisor</span>
                  )}
                  <span className="text-xs text-secondary-500">
                    {cliente.total_analistas || 0} analista(s)
                  </span>
                </button>
              </Table.Cell>
              <Table.Cell>
                {cliente.contacto_nombre ? (
                  <div>
                    <p className="text-sm">{cliente.contacto_nombre}</p>
                    {cliente.contacto_email && (
                      <p className="text-xs text-secondary-500">{cliente.contacto_email}</p>
                    )}
                  </div>
                ) : (
                  <span className="text-secondary-500 text-sm">Sin contacto</span>
                )}
              </Table.Cell>
              <Table.Cell align="center">
                <Badge variant={cliente.activo ? 'success' : 'secondary'}>
                  {cliente.activo ? 'Activo' : 'Inactivo'}
                </Badge>
              </Table.Cell>
              <Table.Cell align="right">
                <div className="flex items-center justify-end gap-1">
                  {onView && (
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => onView(cliente)}
                      title="Ver detalles"
                    >
                      <Eye className="h-4 w-4" />
                    </Button>
                  )}
                  {onManageAsignaciones && (
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => onManageAsignaciones(cliente)}
                      title="Gestionar asignaciones"
                    >
                      <Users className="h-4 w-4 text-primary-400" />
                    </Button>
                  )}
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => onEdit(cliente)}
                    title="Editar"
                  >
                    <Edit2 className="h-4 w-4" />
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => handleToggleActivo(cliente)}
                    title={cliente.activo ? 'Desactivar' : 'Activar'}
                    disabled={toggleMutation.isPending}
                  >
                    {cliente.activo ? (
                      <ToggleRight className="h-4 w-4 text-green-400" />
                    ) : (
                      <ToggleLeft className="h-4 w-4 text-secondary-500" />
                    )}
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setDeleteModal({ open: true, cliente })}
                    title="Eliminar"
                    className="text-red-400 hover:text-red-300"
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              </Table.Cell>
            </Table.Row>
          ))}
        </Table.Body>
      </Table>

      <ConfirmDialog
        isOpen={deleteModal.open}
        onClose={() => setDeleteModal({ open: false, cliente: null })}
        onConfirm={handleDelete}
        title="Eliminar Cliente"
        description={`¿Estás seguro de que deseas eliminar a "${deleteModal.cliente?.razon_social}"? Esta acción no se puede deshacer.`}
        confirmText="Eliminar"
        variant="danger"
        loading={deleteMutation.isPending}
      />
    </>
  )
}

export default ClientesTable
