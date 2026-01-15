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
    Estados del proceso de cierre de nómina (7 estados principales).
    
    Flujo principal:
        CARGA_ARCHIVOS (hub único: ERP + clasificación + novedades + mapeo)
        → [Generar Comparación]
        → CON_DISCREPANCIAS / SIN_DISCREPANCIAS
        → [Click manual] → CONSOLIDADO
        → [Detectar Incidencias manual]
        → CON_INCIDENCIAS / SIN_INCIDENCIAS
        → FINALIZADO
    
    IMPORTANTE:
    - CARGA_ARCHIVOS es el hub donde se hace todo el trabajo de preparación
    - SIN_DISCREPANCIAS requiere click manual para pasar a CONSOLIDADO
    - Se puede volver a CARGA_ARCHIVOS desde CON/SIN_DISCREPANCIAS
    - Detección de incidencias es manual
    
    Uso:
        from apps.validador.constants import EstadoCierre
        
        if cierre.estado == EstadoCierre.CONSOLIDADO:
            ...
        
        if cierre.estado in EstadoCierre.ESTADOS_ACTIVOS:
            ...
    """
    # Estados del flujo (7 principales)
    CARGA_ARCHIVOS = 'carga_archivos'       # Hub único: ERP + clasificación + novedades + mapeo
    CON_DISCREPANCIAS = 'con_discrepancias' # Hay diferencias por resolver
    SIN_DISCREPANCIAS = 'sin_discrepancias' # 0 discrepancias, requiere click manual
    CONSOLIDADO = 'consolidado'             # Datos validados y confirmados
    CON_INCIDENCIAS = 'con_incidencias'     # Hay incidencias por resolver
    SIN_INCIDENCIAS = 'sin_incidencias'     # No hay incidencias
    FINALIZADO = 'finalizado'               # Proceso completo
    
    # Estados especiales
    CANCELADO = 'cancelado'
    ERROR = 'error'
    
    # Choices para campos de modelo Django
    CHOICES = [
        (CARGA_ARCHIVOS, 'Carga de Archivos'),
        (CON_DISCREPANCIAS, 'Con Discrepancias'),
        (SIN_DISCREPANCIAS, 'Sin Discrepancias'),
        (CONSOLIDADO, 'Consolidado'),
        (CON_INCIDENCIAS, 'Con Incidencias'),
        (SIN_INCIDENCIAS, 'Sin Incidencias'),
        (FINALIZADO, 'Finalizado'),
        (CANCELADO, 'Cancelado'),
        (ERROR, 'Error'),
    ]
    
    # Grupos de estados
    ESTADOS_ACTIVOS = [
        CARGA_ARCHIVOS,
        CON_DISCREPANCIAS,
        SIN_DISCREPANCIAS,
        CONSOLIDADO,
        CON_INCIDENCIAS,
        SIN_INCIDENCIAS,
    ]
    ESTADOS_FINALES = [FINALIZADO, CANCELADO]
    ESTADOS_CON_ERROR = [ERROR]
    
    # Estados que permiten edición de archivos (solo en hub)
    ESTADOS_EDITABLES = [CARGA_ARCHIVOS]
    
    # Estados que permiten volver a CARGA_ARCHIVOS
    ESTADOS_PUEDEN_RETROCEDER = [CON_DISCREPANCIAS, SIN_DISCREPANCIAS]
    
    # Estados que requieren acción manual del usuario
    ESTADOS_REQUIEREN_ACCION_MANUAL = [SIN_DISCREPANCIAS, SIN_INCIDENCIAS]
    
    # Estados que requieren atención/revisión (para dashboard)
    ESTADOS_REQUIEREN_ATENCION = [CON_DISCREPANCIAS, CON_INCIDENCIAS]
    
    # Estados donde se puede finalizar
    ESTADOS_PUEDEN_FINALIZAR = [SIN_INCIDENCIAS]
    
    # Estados donde se puede consolidar
    ESTADOS_PUEDEN_CONSOLIDAR = [SIN_DISCREPANCIAS]
    
    # Estados donde se puede detectar incidencias
    ESTADOS_PUEDEN_DETECTAR_INCIDENCIAS = [CONSOLIDADO]
    
    ALL = [
        CARGA_ARCHIVOS, CON_DISCREPANCIAS, SIN_DISCREPANCIAS,
        CONSOLIDADO, CON_INCIDENCIAS, SIN_INCIDENCIAS,
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
    
    @classmethod
    def puede_retroceder(cls, estado):
        """Verifica si puede volver a CARGA_ARCHIVOS."""
        return estado in cls.ESTADOS_PUEDEN_RETROCEDER
    
    @classmethod
    def puede_consolidar(cls, estado):
        """Verifica si puede pasar a CONSOLIDADO."""
        return estado in cls.ESTADOS_PUEDEN_CONSOLIDAR
    
    @classmethod
    def puede_detectar_incidencias(cls, estado):
        """Verifica si puede ejecutar detección de incidencias."""
        return estado in cls.ESTADOS_PUEDEN_DETECTAR_INCIDENCIAS


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


class EstadoArchivoLibro:
    """
    Estados específicos para el procesamiento del Libro de Remuneraciones.
    
    Flujo:
        SUBIDO → EXTRAYENDO_HEADERS → PENDIENTE_CLASIFICACION → 
        LISTO → PROCESANDO → PROCESADO
                                                      ↓
                                                    ERROR
    """
    SUBIDO = 'subido'
    EXTRAYENDO_HEADERS = 'extrayendo_headers'
    PENDIENTE_CLASIFICACION = 'pendiente_clasificacion'
    LISTO = 'listo'
    PROCESANDO = 'procesando'
    PROCESADO = 'procesado'
    ERROR = 'error'
    
    CHOICES = [
        (SUBIDO, 'Subido'),
        (EXTRAYENDO_HEADERS, 'Extrayendo Headers'),
        (PENDIENTE_CLASIFICACION, 'Pendiente Clasificación'),
        (LISTO, 'Listo para Procesar'),
        (PROCESANDO, 'Procesando'),
        (PROCESADO, 'Procesado'),
        (ERROR, 'Error'),
    ]
    
    # Estados que permiten extracción de headers
    ESTADOS_PUEDE_EXTRAER_HEADERS = [SUBIDO]
    
    # Estados que permiten clasificación
    ESTADOS_PUEDE_CLASIFICAR = [PENDIENTE_CLASIFICACION, LISTO]
    
    # Estados que permiten procesamiento
    ESTADOS_PUEDE_PROCESAR = [LISTO]
    
    # Estados en proceso (no terminados)
    ESTADOS_EN_PROCESO = [EXTRAYENDO_HEADERS, PROCESANDO]
    
    ALL = [
        SUBIDO, EXTRAYENDO_HEADERS, PENDIENTE_CLASIFICACION,
        LISTO, PROCESANDO, PROCESADO, ERROR
    ]
    
    @classmethod
    def es_valido(cls, valor):
        return valor in cls.ALL
    
    @classmethod
    def puede_extraer_headers(cls, estado):
        return estado in cls.ESTADOS_PUEDE_EXTRAER_HEADERS
    
    @classmethod
    def puede_clasificar(cls, estado):
        return estado in cls.ESTADOS_PUEDE_CLASIFICAR
    
    @classmethod
    def puede_procesar(cls, estado):
        return estado in cls.ESTADOS_PUEDE_PROCESAR


class EstadoArchivoNovedades:
    """
    Estados específicos para el procesamiento del archivo de Novedades.
    
    Flujo (similar al libro):
        SUBIDO → EXTRAYENDO_HEADERS → PENDIENTE_MAPEO → 
        LISTO → PROCESANDO → PROCESADO
                                              ↓
                                            ERROR
    
    La diferencia con el libro es que en vez de "clasificar" conceptos,
    se "mapean" items del cliente a conceptos ya clasificados del libro.
    """
    SUBIDO = 'subido'
    EXTRAYENDO_HEADERS = 'extrayendo_headers'
    PENDIENTE_MAPEO = 'pendiente_mapeo'
    LISTO = 'listo'
    PROCESANDO = 'procesando'
    PROCESADO = 'procesado'
    ERROR = 'error'
    
    CHOICES = [
        (SUBIDO, 'Subido'),
        (EXTRAYENDO_HEADERS, 'Extrayendo Headers'),
        (PENDIENTE_MAPEO, 'Pendiente Mapeo'),
        (LISTO, 'Listo para Procesar'),
        (PROCESANDO, 'Procesando'),
        (PROCESADO, 'Procesado'),
        (ERROR, 'Error'),
    ]
    
    # Estados que permiten extracción de headers
    ESTADOS_PUEDE_EXTRAER_HEADERS = [SUBIDO]
    
    # Estados que permiten mapeo
    ESTADOS_PUEDE_MAPEAR = [PENDIENTE_MAPEO, LISTO]
    
    # Estados que permiten procesamiento
    ESTADOS_PUEDE_PROCESAR = [LISTO]
    
    # Estados en proceso (no terminados)
    ESTADOS_EN_PROCESO = [EXTRAYENDO_HEADERS, PROCESANDO]
    
    ALL = [
        SUBIDO, EXTRAYENDO_HEADERS, PENDIENTE_MAPEO,
        LISTO, PROCESANDO, PROCESADO, ERROR
    ]
    
    @classmethod
    def es_valido(cls, valor):
        return valor in cls.ALL
    
    @classmethod
    def puede_extraer_headers(cls, estado):
        return estado in cls.ESTADOS_PUEDE_EXTRAER_HEADERS
    
    @classmethod
    def puede_mapear(cls, estado):
        return estado in cls.ESTADOS_PUEDE_MAPEAR
    
    @classmethod
    def puede_procesar(cls, estado):
        return estado in cls.ESTADOS_PUEDE_PROCESAR


class CategoriaConceptoLibro:
    """
    Categorías para clasificar conceptos del Libro de Remuneraciones.
    """
    HABERES_IMPONIBLES = 'haberes_imponibles'
    HABERES_NO_IMPONIBLES = 'haberes_no_imponibles'
    DESCUENTOS_LEGALES = 'descuentos_legales'
    OTROS_DESCUENTOS = 'otros_descuentos'
    APORTES_PATRONALES = 'aportes_patronales'
    INFO_ADICIONAL = 'info_adicional'
    IGNORAR = 'ignorar'
    
    CHOICES = [
        (HABERES_IMPONIBLES, 'Haberes Imponibles'),
        (HABERES_NO_IMPONIBLES, 'Haberes No Imponibles'),
        (DESCUENTOS_LEGALES, 'Descuentos Legales'),
        (OTROS_DESCUENTOS, 'Otros Descuentos'),
        (APORTES_PATRONALES, 'Aportes Patronales'),
        (INFO_ADICIONAL, 'Información Adicional'),
        (IGNORAR, 'Ignorar'),
    ]
    
    # Categorías que se suman para calcular totales
    CATEGORIAS_MONETARIAS = [
        HABERES_IMPONIBLES,
        HABERES_NO_IMPONIBLES,
        DESCUENTOS_LEGALES,
        OTROS_DESCUENTOS,
        APORTES_PATRONALES,
    ]
    
    # Categorías que no se procesan
    CATEGORIAS_NO_MONETARIAS = [
        INFO_ADICIONAL,
        IGNORAR,
    ]
    
    ALL = [
        HABERES_IMPONIBLES, HABERES_NO_IMPONIBLES,
        DESCUENTOS_LEGALES, OTROS_DESCUENTOS,
        APORTES_PATRONALES, INFO_ADICIONAL,
        IGNORAR
    ]
    
    @classmethod
    def es_valido(cls, valor):
        return valor in cls.ALL
    
    @classmethod
    def es_monetaria(cls, categoria):
        return categoria in cls.CATEGORIAS_MONETARIAS



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
