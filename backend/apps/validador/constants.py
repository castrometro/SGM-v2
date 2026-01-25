"""
Constantes y configuraciones del Validador.

Incluye:
- Estados de cierre y sus transiciones
- Estados de incidencias
- Tipos de archivos
- Categorías de conceptos
"""

from django.db import models


class EstadoCierre(models.TextChoices):
    """
    Estados del proceso de cierre de nómina (8 estados principales).
    
    Flujo principal:
        CARGA_ARCHIVOS (hub único: ERP + clasificación + novedades + mapeo)
        → [Automático cuando todos archivos listos]
        → ARCHIVOS_LISTOS (listo para comparar)
        → [Click manual: Generar Comparación]
        → CON_DISCREPANCIAS / SIN_DISCREPANCIAS
        → [Click manual] → CONSOLIDADO
        → [Detectar Incidencias manual]
        → CON_INCIDENCIAS / SIN_INCIDENCIAS
        → FINALIZADO
    
    IMPORTANTE:
    - CARGA_ARCHIVOS es el hub donde se hace todo el trabajo de preparación
    - Transición a ARCHIVOS_LISTOS es automática cuando todos los archivos están procesados
    - SIN_DISCREPANCIAS requiere click manual para pasar a CONSOLIDADO
    - Se puede volver a CARGA_ARCHIVOS desde ARCHIVOS_LISTOS/CON/SIN_DISCREPANCIAS
    - Detección de incidencias es manual
    
    Uso:
        from apps.validador.constants import EstadoCierre
        
        if cierre.estado == EstadoCierre.CONSOLIDADO:
            ...
        
        if cierre.estado in EstadoCierre.ESTADOS_ACTIVOS:
            ...
    """
    # Estados del flujo (8 principales)
    CARGA_ARCHIVOS = 'carga_archivos', 'Carga de Archivos'
    ARCHIVOS_LISTOS = 'archivos_listos', 'Archivos Listos'
    CON_DISCREPANCIAS = 'con_discrepancias', 'Con Discrepancias'
    SIN_DISCREPANCIAS = 'sin_discrepancias', 'Sin Discrepancias'
    CONSOLIDADO = 'consolidado', 'Consolidado'
    CON_INCIDENCIAS = 'con_incidencias', 'Con Incidencias'
    SIN_INCIDENCIAS = 'sin_incidencias', 'Sin Incidencias'
    FINALIZADO = 'finalizado', 'Finalizado'
    
    # Estados especiales
    CANCELADO = 'cancelado', 'Cancelado'
    ERROR = 'error', 'Error'
    
    # Backward compatibility alias for .choices
    @classmethod
    @property
    def CHOICES(cls):
        return cls.choices
    
    # Grupos de estados
    @classmethod
    @property
    def ESTADOS_ACTIVOS(cls):
        return [
            cls.CARGA_ARCHIVOS,
            cls.ARCHIVOS_LISTOS,
            cls.CON_DISCREPANCIAS,
            cls.SIN_DISCREPANCIAS,
            cls.CONSOLIDADO,
            cls.CON_INCIDENCIAS,
            cls.SIN_INCIDENCIAS,
        ]
    
    @classmethod
    @property
    def ESTADOS_FINALES(cls):
        return [cls.FINALIZADO, cls.CANCELADO]
    
    @classmethod
    @property
    def ESTADOS_CON_ERROR(cls):
        return [cls.ERROR]
    
    @classmethod
    @property
    def ESTADOS_EDITABLES(cls):
        """Estados que permiten edición de archivos (solo en hub)."""
        return [cls.CARGA_ARCHIVOS]
    
    @classmethod
    @property
    def ESTADOS_PUEDEN_RETROCEDER(cls):
        """Estados que permiten volver a CARGA_ARCHIVOS."""
        return [cls.ARCHIVOS_LISTOS, cls.CON_DISCREPANCIAS, cls.SIN_DISCREPANCIAS]
    
    @classmethod
    @property
    def ESTADOS_REQUIEREN_ACCION_MANUAL(cls):
        """Estados que requieren acción manual del usuario."""
        return [cls.ARCHIVOS_LISTOS, cls.SIN_DISCREPANCIAS, cls.SIN_INCIDENCIAS]
    
    @classmethod
    @property
    def ESTADOS_REQUIEREN_ATENCION(cls):
        """Estados que requieren atención/revisión (para dashboard)."""
        return [cls.CON_DISCREPANCIAS, cls.CON_INCIDENCIAS]
    
    @classmethod
    @property
    def ESTADOS_PUEDEN_FINALIZAR(cls):
        """Estados donde se puede finalizar."""
        return [cls.SIN_INCIDENCIAS]
    
    @classmethod
    @property
    def ESTADOS_PUEDEN_CONSOLIDAR(cls):
        """Estados donde se puede consolidar."""
        return [cls.SIN_DISCREPANCIAS]
    
    @classmethod
    @property
    def ESTADOS_PUEDEN_DETECTAR_INCIDENCIAS(cls):
        """Estados donde se puede detectar incidencias."""
        return [cls.CONSOLIDADO]
    
    @classmethod
    @property
    def ESTADOS_PUEDEN_COMPARAR(cls):
        """Estados donde se puede ejecutar comparación."""
        return [cls.ARCHIVOS_LISTOS]
    
    @classmethod
    @property
    def ALL(cls):
        return [choice[0] for choice in cls.choices]
    
    @classmethod
    def es_valido(cls, valor):
        """Verifica si un valor es un estado válido."""
        return valor in cls.values
    
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
    
    @classmethod
    def puede_comparar(cls, estado):
        """Verifica si puede ejecutar comparación ERP vs Analista."""
        return estado in cls.ESTADOS_PUEDEN_COMPARAR


class EstadoIncidencia(models.TextChoices):
    """
    Estados de una incidencia detectada.
    
    Flujo:
        PENDIENTE → EN_REVISION → APROBADA/RECHAZADA
    
    Uso:
        from apps.validador.constants import EstadoIncidencia
        
        if incidencia.estado == EstadoIncidencia.PENDIENTE:
            incidencia.estado = EstadoIncidencia.EN_REVISION
    """
    PENDIENTE = 'pendiente', 'Pendiente de Revisión'
    EN_REVISION = 'en_revision', 'En Revisión'
    APROBADA = 'aprobada', 'Aprobada'
    RECHAZADA = 'rechazada', 'Rechazada'
    
    # Backward compatibility alias for .choices
    @classmethod
    @property
    def CHOICES(cls):
        return cls.choices
    
    # Grupos de estados
    @classmethod
    @property
    def ESTADOS_ABIERTOS(cls):
        return [cls.PENDIENTE, cls.EN_REVISION]
    
    @classmethod
    @property
    def ESTADOS_RESUELTOS(cls):
        return [cls.APROBADA, cls.RECHAZADA]
    
    @classmethod
    @property
    def ALL(cls):
        return [choice[0] for choice in cls.choices]
    
    @classmethod
    def es_valido(cls, valor):
        """Verifica si un valor es un estado válido."""
        return valor in cls.values
    
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


class EstadoArchivoLibro(models.TextChoices):
    """
    Estados específicos para el procesamiento del Libro de Remuneraciones.
    
    Flujo:
        SUBIDO → EXTRAYENDO_HEADERS → PENDIENTE_CLASIFICACION → 
        LISTO → PROCESANDO → PROCESADO
                                                      ↓
                                                    ERROR
    """
    SUBIDO = 'subido', 'Subido'
    EXTRAYENDO_HEADERS = 'extrayendo_headers', 'Extrayendo Headers'
    PENDIENTE_CLASIFICACION = 'pendiente_clasificacion', 'Pendiente Clasificación'
    LISTO = 'listo', 'Listo para Procesar'
    PROCESANDO = 'procesando', 'Procesando'
    PROCESADO = 'procesado', 'Procesado'
    ERROR = 'error', 'Error'
    
    # Backward compatibility alias for .choices
    @classmethod
    @property
    def CHOICES(cls):
        return cls.choices
    
    # Estados que permiten extracción de headers
    @classmethod
    @property
    def ESTADOS_PUEDE_EXTRAER_HEADERS(cls):
        return [cls.SUBIDO]
    
    # Estados que permiten clasificación
    @classmethod
    @property
    def ESTADOS_PUEDE_CLASIFICAR(cls):
        return [cls.PENDIENTE_CLASIFICACION, cls.LISTO]
    
    # Estados que permiten procesamiento
    @classmethod
    @property
    def ESTADOS_PUEDE_PROCESAR(cls):
        return [cls.LISTO]
    
    # Estados en proceso (no terminados)
    @classmethod
    @property
    def ESTADOS_EN_PROCESO(cls):
        return [cls.EXTRAYENDO_HEADERS, cls.PROCESANDO]
    
    # Estados que indican que el archivo está "resuelto" (listo para comparación)
    @classmethod
    @property
    def ESTADOS_RESUELTOS(cls):
        return [cls.PROCESADO]
    
    @classmethod
    @property
    def ALL(cls):
        return [choice[0] for choice in cls.choices]
    
    @classmethod
    def es_valido(cls, valor):
        return valor in cls.values
    
    @classmethod
    def puede_extraer_headers(cls, estado):
        return estado in cls.ESTADOS_PUEDE_EXTRAER_HEADERS
    
    @classmethod
    def puede_clasificar(cls, estado):
        return estado in cls.ESTADOS_PUEDE_CLASIFICAR
    
    @classmethod
    def puede_procesar(cls, estado):
        return estado in cls.ESTADOS_PUEDE_PROCESAR
    
    @classmethod
    def esta_resuelto(cls, estado):
        """Verifica si el archivo está listo para comparación."""
        return estado in cls.ESTADOS_RESUELTOS


class EstadoArchivoNovedades(models.TextChoices):
    """
    Estados específicos para el procesamiento del archivo de Novedades.
    
    Flujo (similar al libro):
        SUBIDO → EXTRAYENDO_HEADERS → PENDIENTE_MAPEO → 
        LISTO → PROCESANDO → PROCESADO
                                              ↓
                                            ERROR
    
    Alternativa (sin archivo este mes):
        NO_APLICA (marcado manualmente cuando no hay datos)
    
    La diferencia con el libro es que en vez de "clasificar" conceptos,
    se "mapean" items del cliente a conceptos ya clasificados del libro.
    """
    SUBIDO = 'subido', 'Subido'
    EXTRAYENDO_HEADERS = 'extrayendo_headers', 'Extrayendo Headers'
    PENDIENTE_MAPEO = 'pendiente_mapeo', 'Pendiente Mapeo'
    LISTO = 'listo', 'Listo para Procesar'
    PROCESANDO = 'procesando', 'Procesando'
    PROCESADO = 'procesado', 'Procesado'
    NO_APLICA = 'no_aplica', 'No Aplica'
    ERROR = 'error', 'Error'
    
    # Backward compatibility alias for .choices
    @classmethod
    @property
    def CHOICES(cls):
        return cls.choices
    
    # Estados que permiten extracción de headers
    @classmethod
    @property
    def ESTADOS_PUEDE_EXTRAER_HEADERS(cls):
        return [cls.SUBIDO]
    
    # Estados que permiten mapeo
    @classmethod
    @property
    def ESTADOS_PUEDE_MAPEAR(cls):
        return [cls.PENDIENTE_MAPEO, cls.LISTO]
    
    # Estados que permiten procesamiento
    @classmethod
    @property
    def ESTADOS_PUEDE_PROCESAR(cls):
        return [cls.LISTO]
    
    # Estados en proceso (no terminados)
    @classmethod
    @property
    def ESTADOS_EN_PROCESO(cls):
        return [cls.EXTRAYENDO_HEADERS, cls.PROCESANDO]
    
    # Estados que indican que el archivo está "resuelto" (listo para comparación)
    @classmethod
    @property
    def ESTADOS_RESUELTOS(cls):
        return [cls.PROCESADO, cls.NO_APLICA]
    
    @classmethod
    @property
    def ALL(cls):
        return [choice[0] for choice in cls.choices]
    
    @classmethod
    def es_valido(cls, valor):
        return valor in cls.values
    
    @classmethod
    def puede_extraer_headers(cls, estado):
        return estado in cls.ESTADOS_PUEDE_EXTRAER_HEADERS
    
    @classmethod
    def puede_mapear(cls, estado):
        return estado in cls.ESTADOS_PUEDE_MAPEAR
    
    @classmethod
    def puede_procesar(cls, estado):
        return estado in cls.ESTADOS_PUEDE_PROCESAR
    
    @classmethod
    def esta_resuelto(cls, estado):
        """Verifica si el archivo está listo para comparación (procesado o no aplica)."""
        return estado in cls.ESTADOS_RESUELTOS


class CategoriaConceptoLibro(models.TextChoices):
    """
    Categorías para clasificar conceptos del Libro de Remuneraciones.
    """
    HABERES_IMPONIBLES = 'haberes_imponibles', 'Haberes Imponibles'
    HABERES_NO_IMPONIBLES = 'haberes_no_imponibles', 'Haberes No Imponibles'
    DESCUENTOS_LEGALES = 'descuentos_legales', 'Descuentos Legales'
    OTROS_DESCUENTOS = 'otros_descuentos', 'Otros Descuentos'
    APORTES_PATRONALES = 'aportes_patronales', 'Aportes Patronales'
    INFO_ADICIONAL = 'info_adicional', 'Información Adicional'
    IGNORAR = 'ignorar', 'Ignorar'
    
    # Backward compatibility alias for .choices
    @classmethod
    @property
    def CHOICES(cls):
        return cls.choices
    
    # Categorías que se suman para calcular totales
    @classmethod
    @property
    def CATEGORIAS_MONETARIAS(cls):
        return [
            cls.HABERES_IMPONIBLES,
            cls.HABERES_NO_IMPONIBLES,
            cls.DESCUENTOS_LEGALES,
            cls.OTROS_DESCUENTOS,
            cls.APORTES_PATRONALES,
        ]
    
    # Categorías que no se procesan
    @classmethod
    @property
    def CATEGORIAS_NO_MONETARIAS(cls):
        return [
            cls.INFO_ADICIONAL,
            cls.IGNORAR,
        ]
    
    @classmethod
    @property
    def ALL(cls):
        return [choice[0] for choice in cls.choices]
    
    @classmethod
    def es_valido(cls, valor):
        return valor in cls.values
    
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
