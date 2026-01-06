/**
 * Tabla de Mis Clientes (versión simplificada sin acciones de admin)
 * Issue #9: Formato tabla para página Mis Clientes
 */
import { Link } from 'react-router-dom'
import { Building2, Eye } from 'lucide-react'
import { Table, Badge, Button } from '../../../components/ui'

const MisClientesTable = ({ clientes = [] }) => {
  if (clientes.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-12 text-secondary-500">
        <Building2 className="h-12 w-12 mb-4 opacity-50" />
        <p className="text-lg font-medium">No hay clientes asignados</p>
        <p className="text-sm">Contacta a tu supervisor para que te asigne clientes</p>
      </div>
    )
  }

  return (
    <Table>
      <Table.Header>
        <Table.Row hoverable={false}>
          <Table.Head>Cliente</Table.Head>
          <Table.Head>RUT</Table.Head>
          <Table.Head>Industria</Table.Head>
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
                    {cliente.nombre_display || cliente.nombre || cliente.razon_social}
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
                {cliente.rut || 'Sin RUT'}
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
              <Link to={`/clientes/${cliente.id}`}>
                <Button
                  variant="ghost"
                  size="sm"
                  title="Ver detalles"
                >
                  <Eye className="h-4 w-4" />
                  <span className="ml-1 hidden sm:inline">Ver</span>
                </Button>
              </Link>
            </Table.Cell>
          </Table.Row>
        ))}
      </Table.Body>
    </Table>
  )
}

export default MisClientesTable
