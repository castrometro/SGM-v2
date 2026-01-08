"""
Constantes centralizadas para el módulo Core.
Tipos de usuario y permisos del sistema.
"""


class TipoUsuario:
    """
    Tipos de usuario del sistema SGM.
    
    Jerarquía de permisos (heredados):
        GERENTE > SUPERVISOR > ANALISTA
    
    Uso:
        from apps.core.constants import TipoUsuario
        
        if user.tipo_usuario == TipoUsuario.GERENTE:
            ...
        
        if user.tipo_usuario in TipoUsuario.PUEDEN_APROBAR:
            ...
    """
    ANALISTA = 'analista'
    SUPERVISOR = 'supervisor'
    GERENTE = 'gerente'
    
    # Choices para campos de modelo Django
    CHOICES = [
        (ANALISTA, 'Analista'),
        (SUPERVISOR, 'Supervisor'),
        (GERENTE, 'Gerente'),
    ]
    
    # Grupos de permisos
    PUEDEN_APROBAR = [SUPERVISOR, GERENTE]
    PUEDEN_SUPERVISAR = [SUPERVISOR, GERENTE]
    PUEDEN_ADMINISTRAR = [GERENTE]
    PUEDEN_GESTIONAR_USUARIOS = [GERENTE]
    PUEDEN_SER_SUPERVISORES = [SUPERVISOR, GERENTE]
    PUEDEN_SER_ASIGNADOS_CLIENTE = [ANALISTA, SUPERVISOR]
    
    # Para validaciones
    ALL = [ANALISTA, SUPERVISOR, GERENTE]
    
    @classmethod
    def es_valido(cls, valor):
        """Verifica si un valor es un tipo de usuario válido."""
        return valor in cls.ALL
    
    @classmethod
    def puede_aprobar(cls, tipo):
        """Verifica si el tipo puede aprobar incidencias/cierres."""
        return tipo in cls.PUEDEN_APROBAR
    
    @classmethod
    def puede_supervisar(cls, tipo):
        """Verifica si el tipo puede supervisar equipos."""
        return tipo in cls.PUEDEN_SUPERVISAR
    
    @classmethod
    def puede_administrar(cls, tipo):
        """Verifica si el tipo puede administrar el sistema."""
        return tipo in cls.PUEDEN_ADMINISTRAR


class Permisos:
    """
    Nombres de permisos calculados.
    Usados en la respuesta del endpoint /me/ y en el frontend.
    """
    # Permisos de cierre
    CAN_CREATE_CIERRE = 'canCreateCierre'
    CAN_VIEW_ALL_CIERRES = 'canViewAllCierres'
    CAN_APPROVE_CIERRE = 'canApproveCierre'
    
    # Permisos de archivos
    CAN_UPLOAD_FILES = 'canUploadFiles'
    CAN_CLASSIFY_CONCEPTS = 'canClassifyConcepts'
    CAN_MAP_NOVEDADES = 'canMapNovedades'
    
    # Permisos de incidencias
    CAN_RESPOND_INCIDENCIA = 'canRespondIncidencia'
    CAN_APPROVE_INCIDENCIA = 'canApproveIncidencia'
    CAN_VIEW_ALL_INCIDENCIAS = 'canViewAllIncidencias'
    
    # Permisos de equipo
    CAN_VIEW_TEAM = 'canViewTeam'
    
    # Permisos de administración
    CAN_MANAGE_USERS = 'canManageUsers'
    CAN_MANAGE_CLIENTS = 'canManageClients'
    CAN_MANAGE_SERVICES = 'canManageServices'
    
    # Permisos de reportes
    CAN_VIEW_EXECUTIVE_DASHBOARD = 'canViewExecutiveDashboard'
    CAN_VIEW_ALL_REPORTS = 'canViewAllReports'
    CAN_VIEW_GLOBAL_REPORTS = 'canViewGlobalReports'
