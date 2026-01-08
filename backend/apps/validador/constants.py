"""
Constantes y configuraciones del Validador.

Incluye:
- Estados de cierre y sus transiciones
- Estados de incidencias
- Tipos de archivos
- Categorías de conceptos
"""


class EstadoCierre:
    """
    Estados del proceso de cierre de nómina.
    
    Flujo principal:
        CARGA_ARCHIVOS → CLASIFICACION → MAPEO → COMPARACION →
        CON_DISCREPANCIAS (loop) → CONSOLIDADO →
        DETECCION_INCIDENCIAS → REVISION_INCIDENCIAS → FINALIZADO
    
    Uso:
        from apps.validador.constants import EstadoCierre
        
        if cierre.estado == EstadoCierre.CONSOLIDADO:
            ...
        
        if cierre.estado in EstadoCierre.ESTADOS_ACTIVOS:
            ...
    """
    # Estados del flujo
    CARGA_ARCHIVOS = 'carga_archivos'
    CLASIFICACION_CONCEPTOS = 'clasificacion_conceptos'
    MAPEO_ITEMS = 'mapeo_items'
    COMPARACION = 'comparacion'
    CON_DISCREPANCIAS = 'con_discrepancias'
    CONSOLIDADO = 'consolidado'
    DETECCION_INCIDENCIAS = 'deteccion_incidencias'
    REVISION_INCIDENCIAS = 'revision_incidencias'
    FINALIZADO = 'finalizado'
    CANCELADO = 'cancelado'
    ERROR = 'error'
    
    # Choices para campos de modelo Django
    CHOICES = [
        (CARGA_ARCHIVOS, 'Carga de Archivos'),
        (CLASIFICACION_CONCEPTOS, 'Clasificación de Conceptos'),
        (MAPEO_ITEMS, 'Mapeo de Items'),
        (COMPARACION, 'Comparación en Proceso'),
        (CON_DISCREPANCIAS, 'Con Discrepancias'),
        (CONSOLIDADO, 'Consolidado'),
        (DETECCION_INCIDENCIAS, 'Detectando Incidencias'),
        (REVISION_INCIDENCIAS, 'Revisión de Incidencias'),
        (FINALIZADO, 'Finalizado'),
        (ERROR, 'Error en Proceso'),
    ]
    
    # Grupos de estados
    ESTADOS_ACTIVOS = [
        CARGA_ARCHIVOS,
        CLASIFICACION_CONCEPTOS,
        MAPEO_ITEMS,
        COMPARACION,
        CON_DISCREPANCIAS,
        CONSOLIDADO,
        DETECCION_INCIDENCIAS,
        REVISION_INCIDENCIAS,
    ]
    ESTADOS_FINALES = [FINALIZADO, CANCELADO]
    ESTADOS_CON_ERROR = [ERROR]
    
    # Estados que permiten edición de archivos
    ESTADOS_EDITABLES = [CARGA_ARCHIVOS, CON_DISCREPANCIAS]
    
    # Estados que requieren acción del supervisor
    ESTADOS_REQUIEREN_SUPERVISOR = [REVISION_INCIDENCIAS]
    
    # Estados donde se puede finalizar
    ESTADOS_PUEDEN_FINALIZAR = [CONSOLIDADO, REVISION_INCIDENCIAS, DETECCION_INCIDENCIAS]
    
    ALL = [
        CARGA_ARCHIVOS, CLASIFICACION_CONCEPTOS, MAPEO_ITEMS,
        COMPARACION, CON_DISCREPANCIAS, CONSOLIDADO,
        DETECCION_INCIDENCIAS, REVISION_INCIDENCIAS,
        FINALIZADO, CANCELADO, ERROR,
    ]
    
    @classmethod
    def es_valido(cls, valor):
        """Verifica si un valor es un estado válido."""
        return valor in cls.ALL
    
    @classmethod
    def es_activo(cls, estado):
        """Verifica si el estado está activo (no finalizado/cancelado)."""
        return estado in cls.ESTADOS_ACTIVOS
    
    @classmethod
    def es_final(cls, estado):
        """Verifica si el estado es final."""
        return estado in cls.ESTADOS_FINALES
    
    @classmethod
    def permite_edicion(cls, estado):
        """Verifica si el estado permite editar archivos."""
        return estado in cls.ESTADOS_EDITABLES


class EstadoIncidencia:
    """
    Estados de una incidencia detectada.
    
    Flujo:
        PENDIENTE → EN_REVISION → APROBADA/RECHAZADA
    
    Uso:
        from apps.validador.constants import EstadoIncidencia
        
        if incidencia.estado == EstadoIncidencia.PENDIENTE:
            incidencia.estado = EstadoIncidencia.EN_REVISION
    """
    PENDIENTE = 'pendiente'
    EN_REVISION = 'en_revision'
    APROBADA = 'aprobada'
    RECHAZADA = 'rechazada'
    
    # Choices para campos de modelo Django
    CHOICES = [
        (PENDIENTE, 'Pendiente de Revisión'),
        (EN_REVISION, 'En Revisión'),
        (APROBADA, 'Aprobada'),
        (RECHAZADA, 'Rechazada'),
    ]
    
    # Grupos de estados
    ESTADOS_ABIERTOS = [PENDIENTE, EN_REVISION]
    ESTADOS_RESUELTOS = [APROBADA, RECHAZADA]
    
    ALL = [PENDIENTE, EN_REVISION, APROBADA, RECHAZADA]
    
    @classmethod
    def es_valido(cls, valor):
        """Verifica si un valor es un estado válido."""
        return valor in cls.ALL
    
    @classmethod
    def es_abierto(cls, estado):
        """Verifica si la incidencia está abierta (sin resolver)."""
        return estado in cls.ESTADOS_ABIERTOS
    
    @classmethod
    def es_resuelto(cls, estado):
        """Verifica si la incidencia está resuelta."""
        return estado in cls.ESTADOS_RESUELTOS


class TipoArchivoERP:
    """Tipos de archivos provenientes del ERP."""
    LIBRO_REMUNERACIONES = 'libro_remuneraciones'
    MOVIMIENTOS_MES = 'movimientos_mes'
    
    ALL = [LIBRO_REMUNERACIONES, MOVIMIENTOS_MES]
    
    @classmethod
    def es_valido(cls, valor):
        return valor in cls.ALL


class TipoArchivoAnalista:
    """Tipos de archivos cargados por el analista."""
    NOVEDADES = 'novedades'
    ASISTENCIAS = 'asistencias'
    FINIQUITOS = 'finiquitos'
    INGRESOS = 'ingresos'
    
    ALL = [NOVEDADES, ASISTENCIAS, FINIQUITOS, INGRESOS]
    REQUERIDOS = [NOVEDADES]
    OPCIONALES = [ASISTENCIAS, FINIQUITOS, INGRESOS]
    
    @classmethod
    def es_valido(cls, valor):
        return valor in cls.ALL
    
    @classmethod
    def es_requerido(cls, valor):
        return valor in cls.REQUERIDOS


# Umbral de variación para detectar incidencias (30%)
UMBRAL_VARIACION_INCIDENCIA = 30.0

# Categorías que SE EXCLUYEN de la detección de incidencias
CATEGORIAS_EXCLUIDAS_INCIDENCIAS = [
    'informativos',
    'descuentos_legales',
]

# Configuración de categorías inicial
CATEGORIAS_INICIALES = [
    {
        'codigo': 'haberes_imponibles',
        'nombre': 'Haberes Imponibles',
        'descripcion': 'Ingresos que están afectos a cotizaciones previsionales',
        'se_compara': True,
        'se_incluye_en_incidencias': True,
        'orden': 1,
    },
    {
        'codigo': 'haberes_no_imponibles',
        'nombre': 'Haberes No Imponibles',
        'descripcion': 'Ingresos que no están afectos a cotizaciones previsionales',
        'se_compara': True,
        'se_incluye_en_incidencias': True,
        'orden': 2,
    },
    {
        'codigo': 'descuentos_legales',
        'nombre': 'Descuentos Legales',
        'descripcion': 'AFP, Salud, Impuesto Único, etc.',
        'se_compara': True,
        'se_incluye_en_incidencias': False,  # EXCLUIDO
        'orden': 3,
    },
    {
        'codigo': 'otros_descuentos',
        'nombre': 'Otros Descuentos',
        'descripcion': 'Anticipos, préstamos, cuotas sindicales, etc.',
        'se_compara': True,
        'se_incluye_en_incidencias': True,
        'orden': 4,
    },
    {
        'codigo': 'aportes_patronales',
        'nombre': 'Aportes Patronales',
        'descripcion': 'Aportes del empleador (Seguro Cesantía, Mutual, etc.)',
        'se_compara': True,
        'se_incluye_en_incidencias': True,
        'orden': 5,
    },
    {
        'codigo': 'informativos',
        'nombre': 'Informativos',
        'descripcion': 'Información adicional (días trabajados, horas extra, etc.)',
        'se_compara': False,  # NO SE COMPARA
        'se_incluye_en_incidencias': False,  # EXCLUIDO
        'orden': 6,
    },
]

# Tipos de archivos ERP esperados
TIPOS_ARCHIVO_ERP = {
    'libro_remuneraciones': {
        'nombre': 'Libro de Remuneraciones',
        'extensiones_validas': ['.xlsx', '.xls', '.csv'],
        'requerido': True,
    },
    'movimientos_mes': {
        'nombre': 'Movimientos del Mes',
        'extensiones_validas': ['.xlsx', '.xls'],
        'requerido': True,
    },
}

# Tipos de archivos Analista esperados
TIPOS_ARCHIVO_ANALISTA = {
    'novedades': {
        'nombre': 'Novedades',
        'extensiones_validas': ['.xlsx', '.xls', '.csv'],
        'requerido': True,
    },
    'asistencias': {
        'nombre': 'Asistencias',
        'extensiones_validas': ['.xlsx', '.xls', '.csv'],
        'requerido': False,
    },
    'finiquitos': {
        'nombre': 'Finiquitos',
        'extensiones_validas': ['.xlsx', '.xls', '.csv'],
        'requerido': False,
    },
    'ingresos': {
        'nombre': 'Ingresos',
        'extensiones_validas': ['.xlsx', '.xls', '.csv'],
        'requerido': False,
    },
}

# Hojas esperadas en Movimientos del Mes (nombres comunes)
HOJAS_MOVIMIENTOS = [
    'Ingresos',
    'Finiquitos',
    'Licencias',
    'Vacaciones',
    'Permisos',
    'Ausencias',
]
