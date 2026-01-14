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


class TipoERP:
    """
    Slugs de sistemas ERP soportados por SGM.
    
    Estos slugs se usan como identificadores para:
    - El patrón Factory (instanciar estrategias de parseo)
    - Validar configuraciones de clientes
    - Consistencia frontend/backend
    
    Uso:
        from apps.core.constants import TipoERP
        
        if config.erp.slug == TipoERP.TALANA:
            ...
        
        if TipoERP.tiene_api(erp_slug):
            ...
    """
    TALANA = 'talana'
    BUK = 'buk'
    SAP = 'sap'
    NUBOX = 'nubox'
    SOFTLAND = 'softland'
    GENERIC = 'generic'  # Fallback para ERPs sin implementación específica
    
    # Choices para campos de modelo Django
    CHOICES = [
        (TALANA, 'Talana'),
        (BUK, 'BUK'),
        (SAP, 'SAP'),
        (NUBOX, 'Nubox'),
        (SOFTLAND, 'Softland'),
        (GENERIC, 'Genérico'),
    ]
    
    # ERPs con API disponible para integración directa
    CON_API = [TALANA, BUK]
    
    # ERPs que solo soportan carga de archivos
    SOLO_ARCHIVOS = [SAP, NUBOX, SOFTLAND, GENERIC]
    
    # Todos los slugs válidos
    ALL = [TALANA, BUK, SAP, NUBOX, SOFTLAND, GENERIC]
    
    @classmethod
    def es_valido(cls, slug: str) -> bool:
        """Verifica si un slug es válido."""
        return slug in cls.ALL
    
    @classmethod
    def tiene_api(cls, slug: str) -> bool:
        """Verifica si el ERP tiene API para integración directa."""
        return slug in cls.CON_API
    
    @classmethod
    def get_nombre_display(cls, slug: str) -> str:
        """Obtiene el nombre de display para un slug."""
        for s, nombre in cls.CHOICES:
            if s == slug:
                return nombre
        return slug.upper()


class AccionAudit:
    """
    Tipos de acciones para auditoría.
    
    Uso:
        from apps.core.constants import AccionAudit
        
        AuditLog.registrar(request, AccionAudit.CREATE, instancia)
    
    Compliance:
        - ISO 27001:2022 (A.8.15) - Logging
        - Ley 21.719 Chile - Trazabilidad de acceso a datos personales
    """
    CREATE = 'create'
    UPDATE = 'update'
    DELETE = 'delete'
    LOGIN = 'login'
    LOGOUT = 'logout'
    EXPORT = 'export'
    PROCESAR = 'procesar'  # Procesamiento de archivos (ej: libro de remuneraciones)
    
    CHOICES = [
        (CREATE, 'Crear'),
        (UPDATE, 'Actualizar'),
        (DELETE, 'Eliminar'),
        (LOGIN, 'Inicio de sesión'),
        (LOGOUT, 'Cierre de sesión'),
        (EXPORT, 'Exportación'),
        (PROCESAR, 'Procesar'),
    ]
    
    ALL = [CREATE, UPDATE, DELETE, LOGIN, LOGOUT, EXPORT, PROCESAR]
    
    @classmethod
    def es_valido(cls, valor):
        """Verifica si un valor es una acción válida."""
        return valor in cls.ALL
