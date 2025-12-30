"""
Constantes y configuraciones del Validador.
"""

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
