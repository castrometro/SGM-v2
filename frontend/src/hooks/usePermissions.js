/**
 * Hook para verificar permisos basados en rol
 */
import { useMemo } from 'react'
import { useAuthStore } from '../stores/authStore'

export const usePermissions = () => {
  const user = useAuthStore((state) => state.user)
  const tipoUsuario = user?.tipo_usuario

  const permissions = useMemo(() => ({
    // Verificaciones de rol
    isAnalista: tipoUsuario === 'analista',
    isSupervisor: tipoUsuario === 'supervisor',
    isGerente: tipoUsuario === 'gerente',
    isSupervisorOrHigher: ['supervisor', 'gerente'].includes(tipoUsuario),

    // Permisos específicos
    canCreateCierre: true, // Todos los autenticados
    canUploadFiles: true, // Todos
    canClassifyConcepts: true, // Todos
    canMapNovedades: true, // Todos
    canRespondIncidencia: true, // Todos pueden responder
    
    // Solo supervisor o gerente
    canApproveIncidencia: ['supervisor', 'gerente'].includes(tipoUsuario),
    canViewTeam: ['supervisor', 'gerente'].includes(tipoUsuario),
    canViewAllCierres: ['supervisor', 'gerente'].includes(tipoUsuario),
    canViewAllIncidencias: ['supervisor', 'gerente'].includes(tipoUsuario),
    
    // Solo gerente
    canManageUsers: tipoUsuario === 'gerente',
    canManageClients: tipoUsuario === 'gerente',
    canManageServices: tipoUsuario === 'gerente',
    canViewExecutiveDashboard: tipoUsuario === 'gerente',
    canViewAllReports: tipoUsuario === 'gerente',
  }), [tipoUsuario])

  return permissions
}

export default usePermissions
