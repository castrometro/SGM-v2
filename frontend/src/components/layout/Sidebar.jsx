/**
 * Sidebar con navegación basada en rol
 * 
 * Jerarquía de permisos:
 * - Analista: Dashboard, Mis Cierres, Mis Clientes
 * - Supervisor: + Mi Equipo, Incidencias del equipo
 * - Gerente: + Administración, Dashboard Ejecutivo, Todos los reportes
 */
import { NavLink } from 'react-router-dom'
import { 
  LayoutDashboard, 
  Building2, 
  FileCheck2, 
  BarChart3,
  Users,
  AlertTriangle,
  FolderKanban,
  Settings,
  FileText,
  UserCog
} from 'lucide-react'
import { useAuthStore } from '../../stores/authStore'
import { usePermissions } from '../../hooks/usePermissions'
import { cn } from '../../utils/cn'

const Sidebar = () => {
  const user = useAuthStore((state) => state.user)
  const { isSupervisorOrHigher, isGerente } = usePermissions()
  
  // Navegación común para todos los roles (excepto Mis Clientes para gerentes)
  const mainNavigation = [
    { 
      name: 'Dashboard', 
      href: '/dashboard', 
      icon: LayoutDashboard,
      description: 'Panel principal'
    },
    { 
      name: 'Mis Cierres', 
      href: '/validador', 
      icon: FileCheck2,
      description: 'Procesos de validación'
    },
    // "Mis Clientes" solo para analistas y supervisores (gerentes usan Admin > Clientes)
    ...(!isGerente ? [{ 
      name: 'Mis Clientes', 
      href: '/clientes', 
      icon: Building2,
      description: 'Clientes asignados'
    }] : []),
  ]
  
  // Navegación para supervisores
  const supervisorNavigation = [
    { 
      name: 'Mi Equipo', 
      href: '/equipo', 
      icon: Users,
      children: [
        { name: 'Cierres del Equipo', href: '/equipo/cierres' },
        { name: 'Incidencias', href: '/equipo/incidencias' },
      ]
    },
    {
      name: 'Incidencias',
      href: '/incidencias',
      icon: AlertTriangle,
      description: 'Incidencias pendientes'
    },
  ]
  
  // Navegación para gerentes
  const gerenteNavigation = [
    { 
      name: 'Dashboard Ejecutivo', 
      href: '/ejecutivo', 
      icon: BarChart3,
      description: 'Métricas generales'
    },
    { 
      name: 'Reportes', 
      href: '/reportes', 
      icon: FolderKanban,
      description: 'Reportería avanzada'
    },
    { 
      name: 'Todos los Cierres', 
      href: '/cierres', 
      icon: FileCheck2,
      description: 'Vista global'
    },
  ]
  
  // Administración (solo gerentes)
  const adminNavigation = [
    { name: 'Usuarios', href: '/admin/usuarios', icon: UserCog },
    { name: 'Clientes', href: '/admin/clientes', icon: Building2 },
    { name: 'Servicios', href: '/admin/servicios', icon: Settings },
  ]

  const NavItem = ({ item }) => (
    <NavLink
      to={item.href}
      className={({ isActive }) =>
        cn(
          'group flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-all duration-200',
          isActive
            ? 'bg-primary-600/15 text-primary-400 shadow-sm'
            : 'text-secondary-400 hover:bg-secondary-800/50 hover:text-secondary-200'
        )
      }
    >
      <item.icon className="h-5 w-5 flex-shrink-0" />
      <span>{item.name}</span>
    </NavLink>
  )

  const SectionTitle = ({ children }) => (
    <p className="mb-2 mt-6 px-3 text-xs font-semibold uppercase tracking-wider text-secondary-600">
      {children}
    </p>
  )

  const getRoleBadgeColor = (tipo) => {
    switch (tipo) {
      case 'gerente': return 'bg-amber-500/20 text-amber-400 border-amber-500/30'
      case 'supervisor': return 'bg-blue-500/20 text-blue-400 border-blue-500/30'
      default: return 'bg-secondary-500/20 text-secondary-400 border-secondary-500/30'
    }
  }

  return (
    <aside className="flex w-64 flex-col border-r border-secondary-800/50 bg-secondary-900">
      {/* Logo */}
      <div className="flex h-16 items-center gap-3 border-b border-secondary-800/50 px-6">
        <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-primary-500 to-primary-700 shadow-lg shadow-primary-500/20">
          <FileText className="h-5 w-5 text-white" />
        </div>
        <div>
          <h1 className="text-lg font-bold text-white">SGM</h1>
          <p className="text-xs text-secondary-500">Nómina v2.0</p>
        </div>
      </div>
      
      {/* Navigation */}
      <nav className="flex-1 space-y-1 overflow-y-auto px-3 py-4">
        <SectionTitle>Principal</SectionTitle>
        {mainNavigation.map((item) => (
          <NavItem key={item.name} item={item} />
        ))}
        
        {/* Sección Supervisor */}
        {isSupervisorOrHigher && (
          <>
            <SectionTitle>Supervisión</SectionTitle>
            {supervisorNavigation.map((item) => (
              <NavItem key={item.name} item={item} />
            ))}
          </>
        )}
        
        {/* Sección Gerente */}
        {isGerente && (
          <>
            <SectionTitle>Gerencia</SectionTitle>
            {gerenteNavigation.map((item) => (
              <NavItem key={item.name} item={item} />
            ))}
            
            <SectionTitle>Administración</SectionTitle>
            {adminNavigation.map((item) => (
              <NavItem key={item.name} item={item} />
            ))}
          </>
        )}
      </nav>
      
      {/* User info */}
      <div className="border-t border-secondary-800/50 p-4">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-full bg-gradient-to-br from-primary-500 to-primary-700 text-sm font-semibold text-white shadow-md">
            {user?.nombre?.[0]}{user?.apellido?.[0]}
          </div>
          <div className="flex-1 min-w-0">
            <p className="truncate text-sm font-medium text-secondary-100">
              {user?.nombre} {user?.apellido}
            </p>
            <span className={cn(
              "inline-flex items-center rounded-md border px-1.5 py-0.5 text-xs font-medium capitalize",
              getRoleBadgeColor(user?.tipo_usuario)
            )}>
              {user?.tipo_usuario}
            </span>
          </div>
        </div>
      </div>
    </aside>
  )
}

export default Sidebar
