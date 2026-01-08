/**
 * Hook para verificar permisos basados en rol
 * 
 * IMPORTANTE: Los permisos se calculan en el backend y se envían en /api/v1/core/me/
 * Este hook consume esos permisos directamente, asegurando sincronización con el backend.
 * 
 * USO (Issue #16 - Consolidación Context vs Zustand):
 * - Este hook usa useAuthStore internamente para compatibilidad con cualquier contexto
 * - En componentes que ya usan useAuth(), pueden acceder a permisos básicos directamente
 * - Para permisos detallados, este hook es la fuente de verdad
 * 
 * @see apps/core/serializers/usuario.py - get_permisos()
 * @see apps/core/constants.py - Permisos
 */
import { useMemo } from 'react'
import { useAuthStore } from '../stores/authStore'
import { 
  TIPO_USUARIO, 
  PUEDEN_APROBAR, 
  PUEDEN_SUPERVISAR, 
  PUEDEN_ADMINISTRAR 
} from '../constants'

/**
 * Hook principal para permisos detallados
 * Usa useAuthStore para compatibilidad universal
 */
export const usePermissions = () => {
  // Nota: Usamos useAuthStore aquí porque este hook puede ser llamado
  // en contextos donde AuthProvider aún no está disponible (ej: guards de ruta)
  const user = useAuthStore((state) => state.user)
  const tipoUsuario = user?.tipo_usuario
  
  // Permisos del backend (fuente de verdad)
  const permisosBackend = user?.permisos || {}

  const permissions = useMemo(() => ({
    // Verificaciones de rol (locales para UI rápida)
    isAnalista: tipoUsuario === TIPO_USUARIO.ANALISTA,
    isSupervisor: tipoUsuario === TIPO_USUARIO.SUPERVISOR,
    isGerente: tipoUsuario === TIPO_USUARIO.GERENTE,
    isSupervisorOrHigher: PUEDEN_SUPERVISAR.includes(tipoUsuario),

    // Permisos de cierre
    canCreateCierre: permisosBackend.canCreateCierre ?? true,
    canViewAllCierres: permisosBackend.canViewAllCierres ?? PUEDEN_SUPERVISAR.includes(tipoUsuario),
    canApproveCierre: permisosBackend.canApproveCierre ?? PUEDEN_APROBAR.includes(tipoUsuario),
    
    // Permisos de archivos
    canUploadFiles: permisosBackend.canUploadFiles ?? true,
    canClassifyConcepts: permisosBackend.canClassifyConcepts ?? true,
    canMapNovedades: permisosBackend.canMapNovedades ?? true,
    
    // Permisos de incidencias
    canRespondIncidencia: permisosBackend.canRespondIncidencia ?? true,
    canApproveIncidencia: permisosBackend.canApproveIncidencia ?? PUEDEN_APROBAR.includes(tipoUsuario),
    canViewAllIncidencias: permisosBackend.canViewAllIncidencias ?? PUEDEN_SUPERVISAR.includes(tipoUsuario),
    
    // Permisos de equipo
    canViewTeam: permisosBackend.canViewTeam ?? PUEDEN_SUPERVISAR.includes(tipoUsuario),
    
    // Permisos de administración
    canManageUsers: permisosBackend.canManageUsers ?? PUEDEN_ADMINISTRAR.includes(tipoUsuario),
    canManageClients: permisosBackend.canManageClients ?? PUEDEN_ADMINISTRAR.includes(tipoUsuario),
    canManageServices: permisosBackend.canManageServices ?? PUEDEN_ADMINISTRAR.includes(tipoUsuario),
    
    // Permisos de reportes
    canViewExecutiveDashboard: permisosBackend.canViewExecutiveDashboard ?? PUEDEN_ADMINISTRAR.includes(tipoUsuario),
    canViewAllReports: permisosBackend.canViewAllReports ?? PUEDEN_ADMINISTRAR.includes(tipoUsuario),
    canViewGlobalReports: permisosBackend.canViewGlobalReports ?? PUEDEN_SUPERVISAR.includes(tipoUsuario),
  }), [tipoUsuario, permisosBackend])

  return permissions
}

export default usePermissions
