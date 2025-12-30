import { NavLink } from 'react-router-dom'
import { 
  LayoutDashboard, 
  Building2, 
  FileCheck2, 
  BarChart3,
  Users,
  Settings,
  FileText
} from 'lucide-react'
import { useAuth } from '../../contexts/AuthContext'
import { cn } from '../../utils/cn'

const Sidebar = () => {
  const { user } = useAuth()
  
  const navigation = [
    { name: 'Dashboard', href: '/dashboard', icon: LayoutDashboard },
    { name: 'Clientes', href: '/clientes', icon: Building2 },
    { name: 'Validador', href: '/validador', icon: FileCheck2 },
    { name: 'Reportes', href: '/reportes', icon: BarChart3 },
  ]
  
  const adminNavigation = [
    { name: 'Usuarios', href: '/admin/usuarios', icon: Users },
  ]

  return (
    <aside className="flex w-64 flex-col border-r border-secondary-800 bg-secondary-900">
      {/* Logo */}
      <div className="flex h-16 items-center gap-3 border-b border-secondary-800 px-6">
        <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary-600">
          <FileText className="h-6 w-6 text-white" />
        </div>
        <div>
          <h1 className="text-lg font-bold text-white">SGM</h1>
          <p className="text-xs text-secondary-400">v2.0</p>
        </div>
      </div>
      
      {/* Navigation */}
      <nav className="flex-1 space-y-1 px-3 py-4">
        <p className="mb-2 px-3 text-xs font-semibold uppercase tracking-wider text-secondary-500">
          Principal
        </p>
        
        {navigation.map((item) => (
          <NavLink
            key={item.name}
            to={item.href}
            className={({ isActive }) =>
              cn(
                'flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors',
                isActive
                  ? 'bg-primary-600/10 text-primary-400'
                  : 'text-secondary-400 hover:bg-secondary-800 hover:text-secondary-100'
              )
            }
          >
            <item.icon className="h-5 w-5" />
            {item.name}
          </NavLink>
        ))}
        
        {/* Admin section - solo para gerentes */}
        {user?.tipo_usuario === 'gerente' && (
          <>
            <p className="mb-2 mt-6 px-3 text-xs font-semibold uppercase tracking-wider text-secondary-500">
              Administración
            </p>
            
            {adminNavigation.map((item) => (
              <NavLink
                key={item.name}
                to={item.href}
                className={({ isActive }) =>
                  cn(
                    'flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors',
                    isActive
                      ? 'bg-primary-600/10 text-primary-400'
                      : 'text-secondary-400 hover:bg-secondary-800 hover:text-secondary-100'
                  )
                }
              >
                <item.icon className="h-5 w-5" />
                {item.name}
              </NavLink>
            ))}
          </>
        )}
      </nav>
      
      {/* User info */}
      <div className="border-t border-secondary-800 p-4">
        <div className="flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-full bg-primary-600 text-sm font-medium text-white">
            {user?.nombre?.[0]}{user?.apellido?.[0]}
          </div>
          <div className="flex-1 truncate">
            <p className="truncate text-sm font-medium text-secondary-100">
              {user?.nombre} {user?.apellido}
            </p>
            <p className="truncate text-xs text-secondary-500">
              {user?.tipo_usuario}
            </p>
          </div>
        </div>
      </div>
    </aside>
  )
}

export default Sidebar
