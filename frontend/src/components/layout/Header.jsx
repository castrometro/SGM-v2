import { Bell, LogOut, User } from 'lucide-react'
import { useAuth } from '../../contexts/AuthContext'

const Header = () => {
  const { user, logout } = useAuth()

  return (
    <header className="flex h-16 items-center justify-between border-b border-secondary-800 bg-secondary-900 px-6">
      {/* Page title - could be dynamic */}
      <div>
        <h2 className="text-lg font-semibold text-secondary-100">
          Sistema de Gestión de Nómina
        </h2>
      </div>
      
      {/* Actions */}
      <div className="flex items-center gap-2">
        {/* Notifications */}
        <button className="btn-ghost btn-sm relative">
          <Bell className="h-5 w-5" />
          <span className="absolute -right-1 -top-1 flex h-4 w-4 items-center justify-center rounded-full bg-red-500 text-xs text-white">
            3
          </span>
        </button>
        
        {/* User dropdown */}
        <div className="relative ml-2">
          <button 
            onClick={logout}
            className="btn-ghost btn-sm flex items-center gap-2 text-secondary-400 hover:text-secondary-100"
          >
            <LogOut className="h-4 w-4" />
            <span>Salir</span>
          </button>
        </div>
      </div>
    </header>
  )
}

export default Header
