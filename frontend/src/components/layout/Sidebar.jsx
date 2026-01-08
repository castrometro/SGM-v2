/**
 * Sidebar colapsable con navegación basada en rol
 * 
 * Jerarquía de permisos:
 * - Analista: Dashboard, Mis Cierres, Mis Clientes
 * - Supervisor: + Mi Equipo, Incidencias del equipo
 * - Gerente: + Administración, Dashboard Ejecutivo, Todos los reportes
 */
import { useState, useEffect } from 'react'
import { NavLink, useLocation } from 'react-router-dom'
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
  UserCog,
  ChevronDown,
  ChevronRight,
  PanelLeftClose,
  PanelLeft
} from 'lucide-react'
import { useAuthStore } from '../../stores/authStore'
import { usePermissions } from '../../hooks/usePermissions'
import { cn } from '../../utils/cn'

const Sidebar = () => {
  const user = useAuthStore((state) => state.user)
  const { isSupervisorOrHigher, isGerente } = usePermissions()
  const location = useLocation()
  const [expandedMenus, setExpandedMenus] = useState({})
  const [isCollapsed, setIsCollapsed] = useState(() => {
    const saved = localStorage.getItem('sidebar-collapsed')
    return saved ? JSON.parse(saved) : false
  })
  
  useEffect(() => {
    localStorage.setItem('sidebar-collapsed', JSON.stringify(isCollapsed))
  }, [isCollapsed])
  
  const toggleSidebar = () => {
    setIsCollapsed(prev => !prev)
    if (!isCollapsed) {
      setExpandedMenus({})
    }
  }
  
  const toggleMenu = (menuName) => {
    if (isCollapsed) return
    setExpandedMenus(prev => ({
      ...prev,
      [menuName]: !prev[menuName]
    }))
  }
  
  const mainNavigation = [
    { name: 'Dashboard', href: '/dashboard', icon: LayoutDashboard },
    { name: 'Mis Cierres', href: '/validador', icon: FileCheck2 },
    ...(!isGerente ? [{ name: 'Mis Clientes', href: '/clientes', icon: Building2 }] : []),
  ]
  
  const supervisorNavigation = [
    { 
      name: 'Mi Equipo', 
      href: '/equipo', 
      icon: Users,
      children: [
        { name: 'Clientes del Equipo', href: '/equipo' },
        { name: 'Cierres del Equipo', href: '/equipo/cierres' },
        { name: 'Incidencias del Equipo', href: '/equipo/incidencias' },
      ]
    },
    { name: 'Incidencias', href: '/incidencias', icon: AlertTriangle },
  ]
  
  const gerenteNavigation = [
    { name: 'Dashboard Ejecutivo', href: '/ejecutivo', icon: BarChart3 },
    { name: 'Reportes', href: '/reportes', icon: FolderKanban },
    { name: 'Todos los Cierres', href: '/cierres', icon: FileCheck2 },
  ]
  
  const adminNavigation = [
    { name: 'Usuarios', href: '/admin/usuarios', icon: UserCog },
    { name: 'Clientes', href: '/admin/clientes', icon: Building2 },
    { name: 'Servicios', href: '/admin/servicios', icon: Settings },
  ]

  const NavItem = ({ item }) => {
    const hasChildren = item.children && item.children.length > 0
    const isExpanded = expandedMenus[item.name]
    const isChildActive = hasChildren && item.children.some(child => location.pathname === child.href)
    
    if (hasChildren) {
      return (
        <div className="relative group">
          <button
            onClick={() => toggleMenu(item.name)}
            className={cn(
              'flex w-full items-center rounded-lg px-3 py-2.5 text-sm font-medium transition-all duration-200',
              isCollapsed ? 'justify-center' : 'justify-between gap-3',
              isChildActive
                ? 'bg-primary-600/15 text-primary-400'
                : 'text-secondary-400 hover:bg-secondary-800/50 hover:text-secondary-200'
            )}
            title={isCollapsed ? item.name : undefined}
          >
            <div className={cn('flex items-center', isCollapsed ? '' : 'gap-3')}>
              <item.icon className="h-5 w-5 flex-shrink-0" />
              {!isCollapsed && <span>{item.name}</span>}
            </div>
            {!isCollapsed && (isExpanded ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />)}
          </button>
          
          {isCollapsed && (
            <div className="absolute left-full top-0 ml-2 hidden group-hover:block z-50">
              <div className="bg-secondary-800 border border-secondary-700 rounded-lg shadow-xl py-2 min-w-[180px]">
                <p className="px-3 py-1 text-sm font-medium text-secondary-200 border-b border-secondary-700 mb-1">{item.name}</p>
                {item.children.map((child) => (
                  <NavLink
                    key={child.href}
                    to={child.href}
                    className={cn(
                      'block px-3 py-2 text-sm transition-colors',
                      location.pathname === child.href
                        ? 'bg-primary-600/15 text-primary-400'
                        : 'text-secondary-400 hover:bg-secondary-700 hover:text-secondary-200'
                    )}
                  >
                    {child.name}
                  </NavLink>
                ))}
              </div>
            </div>
          )}
          
          {!isCollapsed && isExpanded && (
            <div className="ml-4 mt-1 space-y-1 border-l border-secondary-700 pl-4">
              {item.children.map((child) => (
                <NavLink
                  key={child.href}
                  to={child.href}
                  end
                  className={cn(
                    'block rounded-lg px-3 py-2 text-sm transition-all duration-200',
                    location.pathname === child.href
                      ? 'bg-primary-600/15 text-primary-400'
                      : 'text-secondary-400 hover:bg-secondary-800/50 hover:text-secondary-200'
                  )}
                >
                  {child.name}
                </NavLink>
              ))}
            </div>
          )}
        </div>
      )
    }
    
    return (
      <div className="relative group">
        <NavLink
          to={item.href}
          className={({ isActive }) =>
            cn(
              'flex items-center rounded-lg px-3 py-2.5 text-sm font-medium transition-all duration-200',
              isCollapsed ? 'justify-center' : 'gap-3',
              isActive
                ? 'bg-primary-600/15 text-primary-400 shadow-sm'
                : 'text-secondary-400 hover:bg-secondary-800/50 hover:text-secondary-200'
            )
          }
          title={isCollapsed ? item.name : undefined}
        >
          <item.icon className="h-5 w-5 flex-shrink-0" />
          {!isCollapsed && <span>{item.name}</span>}
        </NavLink>
        
        {isCollapsed && (
          <div className="absolute left-full top-1/2 -translate-y-1/2 ml-2 hidden group-hover:block z-50">
            <div className="bg-secondary-800 border border-secondary-700 rounded-lg shadow-xl px-3 py-2 whitespace-nowrap">
              <span className="text-sm text-secondary-200">{item.name}</span>
            </div>
          </div>
        )}
      </div>
    )
  }

  const SectionTitle = ({ children }) => (
    <p className={cn(
      "mb-2 mt-6 text-xs font-semibold uppercase tracking-wider text-secondary-600 transition-all duration-200",
      isCollapsed ? "px-0 text-center" : "px-3"
    )}>
      {isCollapsed ? '•••' : children}
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
    <aside className={cn(
      "flex flex-col border-r border-secondary-800/50 bg-secondary-900 transition-all duration-300",
      isCollapsed ? "w-[72px]" : "w-64"
    )}>
      {/* Logo */}
      <div className={cn(
        "flex h-16 items-center border-b border-secondary-800/50 transition-all duration-300",
        isCollapsed ? "justify-center px-2" : "gap-3 px-6"
      )}>
        <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-primary-500 to-primary-700 shadow-lg shadow-primary-500/20 flex-shrink-0">
          <FileText className="h-5 w-5 text-white" />
        </div>
        {!isCollapsed && (
          <div className="overflow-hidden">
            <h1 className="text-lg font-bold text-white">SGM</h1>
            <p className="text-xs text-secondary-500">Nómina v2.0</p>
          </div>
        )}
      </div>
      
      {/* Toggle button */}
      <div className={cn(
        "flex border-b border-secondary-800/50 p-2",
        isCollapsed ? "justify-center" : "justify-end"
      )}>
        <button
          onClick={toggleSidebar}
          className="p-2 rounded-lg text-secondary-400 hover:bg-secondary-800 hover:text-secondary-200 transition-colors"
          title={isCollapsed ? "Expandir menú" : "Colapsar menú"}
        >
          {isCollapsed ? <PanelLeft className="h-5 w-5" /> : <PanelLeftClose className="h-5 w-5" />}
        </button>
      </div>
      
      {/* Navigation */}
      <nav className={cn(
        "flex-1 space-y-1 overflow-y-auto py-4 transition-all duration-300",
        isCollapsed ? "px-2" : "px-3"
      )}>
        <SectionTitle>Principal</SectionTitle>
        {mainNavigation.map((item) => (
          <NavItem key={item.name} item={item} />
        ))}
        
        {isSupervisorOrHigher && (
          <>
            <SectionTitle>Supervisión</SectionTitle>
            {supervisorNavigation.map((item) => (
              <NavItem key={item.name} item={item} />
            ))}
          </>
        )}
        
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
      <div className={cn(
        "border-t border-secondary-800/50 transition-all duration-300",
        isCollapsed ? "p-2" : "p-4"
      )}>
        <div className={cn(
          "flex items-center",
          isCollapsed ? "justify-center" : "gap-3"
        )}>
          <div className="flex h-10 w-10 items-center justify-center rounded-full bg-gradient-to-br from-primary-500 to-primary-700 text-sm font-semibold text-white shadow-md flex-shrink-0">
            {user?.nombre?.[0]}{user?.apellido?.[0]}
          </div>
          {!isCollapsed && (
            <div className="flex-1 min-w-0 overflow-hidden">
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
          )}
        </div>
      </div>
    </aside>
  )
}

export default Sidebar
