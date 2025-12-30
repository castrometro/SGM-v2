/**
 * Página de administración de usuarios (solo gerente)
 */
import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { UserCog, Plus, Search } from 'lucide-react'
import api from '../../../api/axios'
import { Card, CardContent, CardHeader, CardTitle } from '../../../components/ui'
import Button from '../../../components/ui/Button'
import Badge from '../../../components/ui/Badge'

const ROLES = {
  analista: { label: 'Analista', color: 'default' },
  supervisor: { label: 'Supervisor', color: 'info' },
  gerente: { label: 'Gerente', color: 'warning' },
}

const UsuariosPage = () => {
  const [search, setSearch] = useState('')

  const { data: usuarios = [], isLoading } = useQuery({
    queryKey: ['admin-usuarios', search],
    queryFn: async () => {
      const params = search ? { search } : {}
      const { data } = await api.get('/v1/core/usuarios/', { params })
      return data.results || data
    },
  })

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-500"></div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-secondary-100">Usuarios</h1>
          <p className="text-secondary-400 mt-1">Administra los usuarios del sistema</p>
        </div>
        <Button>
          <Plus className="h-4 w-4" />
          Nuevo Usuario
        </Button>
      </div>

      {/* Search */}
      <div className="relative max-w-md">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-secondary-500" />
        <input
          type="text"
          placeholder="Buscar usuarios..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="w-full pl-10 pr-4 py-2.5 bg-secondary-800 border border-secondary-700 rounded-lg text-secondary-100 placeholder-secondary-500 focus:ring-2 focus:ring-primary-500 focus:border-transparent"
        />
      </div>

      {/* Lista */}
      <Card>
        <CardHeader>
          <CardTitle>Usuarios del Sistema</CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          <div className="divide-y divide-secondary-800">
            {usuarios.map((usuario) => {
              const rolInfo = ROLES[usuario.tipo_usuario] || { label: usuario.tipo_usuario, color: 'default' }
              
              return (
                <div
                  key={usuario.id}
                  className="flex items-center gap-4 p-4 hover:bg-secondary-800/50 transition-colors"
                >
                  <div className="flex h-10 w-10 items-center justify-center rounded-full bg-primary-600 text-sm font-semibold text-white">
                    {usuario.nombre?.[0]}{usuario.apellido?.[0]}
                  </div>
                  
                  <div className="flex-1 min-w-0">
                    <p className="font-medium text-secondary-100">
                      {usuario.nombre} {usuario.apellido}
                    </p>
                    <p className="text-sm text-secondary-500">
                      {usuario.email}
                    </p>
                  </div>
                  
                  <Badge variant={rolInfo.color}>
                    {rolInfo.label}
                  </Badge>
                  
                  <div className="text-sm text-secondary-500">
                    {usuario.is_active ? (
                      <span className="text-green-400">Activo</span>
                    ) : (
                      <span className="text-red-400">Inactivo</span>
                    )}
                  </div>
                </div>
              )
            })}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

export default UsuariosPage
