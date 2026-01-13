"""
Base Parser para Libro de Remuneraciones.

Define la interfaz que todos los parsers de libro deben implementar.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from dataclasses import dataclass
import pandas as pd
import logging

logger = logging.getLogger(__name__)


@dataclass
class HeaderInfo:
    """
    Información de un header del Excel.
    
    Attributes:
        original: Nombre original del header antes de ser procesado por pandas
        pandas_name: Nombre como lo lee pandas (puede tener .1, .2 para duplicados)
        occurrence: Número de ocurrencia si es duplicado (1, 2, 3...)
        is_duplicate: True si este header está duplicado en el archivo
    """
    original: str
    pandas_name: str
    occurrence: int = 1
    is_duplicate: bool = False


@dataclass
class ProcessResult:
    """
    Resultado del procesamiento del libro.
    
    Attributes:
        success: True si el procesamiento fue exitoso
        data: Lista de diccionarios con datos de empleados
        headers: Lista de headers encontrados en el archivo
        headers_info: Lista de HeaderInfo con detalles de cada header
        error: Mensaje de error si hubo falla
        warnings: Lista de advertencias
        metadata: Información adicional del procesamiento
    """
    success: bool
    data: Optional[List[Dict]] = None
    headers: Optional[List[str]] = None
    headers_info: Optional[List[HeaderInfo]] = None
    error: Optional[str] = None
    warnings: Optional[List[str]] = None
    metadata: Optional[Dict] = None
    
    def __post_init__(self):
        if self.data is None:
            self.data = []
        if self.headers is None:
            self.headers = []
        if self.headers_info is None:
            self.headers_info = []
        if self.warnings is None:
            self.warnings = []
        if self.metadata is None:
            self.metadata = {}
    
    @classmethod
    def ok(cls, data: List[Dict], headers: List[str], headers_info: List['HeaderInfo'] = None, 
           warnings: List[str] = None, metadata: Dict = None):
        """Crea un resultado exitoso."""
        return cls(
            success=True,
            data=data,
            headers=headers,
            headers_info=headers_info or [],
            warnings=warnings or [],
            metadata=metadata or {}
        )
    
    @classmethod
    def fail(cls, error: str):
        """Crea un resultado fallido."""
        return cls(success=False, error=error)


class BaseLibroParser(ABC):
    """
    Clase base abstracta para parsers de Libro de Remuneraciones.
    
    Cada ERP debe implementar su propia versión heredando de esta clase
    e implementando los métodos abstractos.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(f'{__name__}.{self.__class__.__name__}')
    
    @property
    @abstractmethod
    def erp_codigo(self) -> str:
        """
        Código del ERP: 'buk', 'talana', 'softland', 'rex'.
        
        Returns:
            Código único del ERP
        """
        pass
    
    @property
    @abstractmethod
    def fila_headers(self) -> int:
        """
        Número de fila donde están los headers (0-indexed).
        
        Returns:
            Índice de la fila de headers
        """
        pass
    
    @property
    @abstractmethod
    def fila_datos_inicio(self) -> int:
        """
        Primera fila donde empiezan los datos de empleados (0-indexed).
        
        Returns:
            Índice de la primera fila de datos
        """
        pass
    
    @abstractmethod
    def extraer_headers(self, archivo) -> List[str]:
        """
        Extrae los headers del Excel del Libro.
        
        Args:
            archivo: Archivo Excel (file-like object o path)
        
        Returns:
            Lista de headers encontrados (strings)
        
        Raises:
            Exception: Si hay error leyendo el archivo
        """
        pass
    
    @abstractmethod
    def parsear_empleado(self, fila: Dict, conceptos_clasificados: Dict) -> Dict:
        """
        Parsea una fila de empleado según los conceptos clasificados.
        
        Args:
            fila: Dict con los datos de la fila (columna -> valor)
            conceptos_clasificados: Dict de {header: ConceptoLibro}
        
        Returns:
            Dict con estructura:
            {
                'rut': '12345678-9',
                'nombre': 'Juan Pérez',
                'cargo': 'Analista',
                'datos_json': {
                    'haberes_imponibles': {'SUELDO': 1000000, 'total': 1000000},
                    'descuentos_legales': {'AFP': 120000, 'total': 120000},
                    ...
                },
                'total_haberes_imponibles': 1000000,
                ...
            }
        """
        pass
    
    @abstractmethod
    def procesar_libro(self, archivo, conceptos_clasificados: Dict) -> ProcessResult:
        """
        Procesa el libro completo y retorna los datos de todos los empleados.
        
        Args:
            archivo: Archivo Excel (file-like object o path)
            conceptos_clasificados: Dict de {header: ConceptoLibro}
        
        Returns:
            ProcessResult con lista de empleados procesados o error
        """
        pass
    
    # =========================================================================
    # Métodos opcionales para auto-clasificación (override en subclases)
    # =========================================================================
    
    def get_clasificacion_automatica(self, orden: int) -> tuple:
        """
        Retorna clasificación automática para un header según su posición.
        
        Override en subclases para auto-clasificar headers conocidos
        (ej: primeras N columnas siempre son datos del empleado).
        
        Args:
            orden: Índice del header (0-based)
        
        Returns:
            Categoría (str) o None si no aplica clasificación automática
        """
        return None
    
    def es_header_empleado(self, orden: int) -> bool:
        """
        Verifica si un header es dato de empleado (no monetario).
        
        Args:
            orden: Índice del header
        
        Returns:
            True si el header es dato del empleado
        """
        categoria = self.get_clasificacion_automatica(orden)
        return categoria is not None
    
    # =========================================================================
    # Métodos auxiliares (compartidos)
    # =========================================================================
    
    def normalizar_rut(self, rut) -> str:
        """
        Normaliza RUT a formato estándar (sin puntos, con guión).
        
        Args:
            rut: RUT en cualquier formato
        
        Returns:
            RUT normalizado: '12345678-9'
        """
        if pd.isna(rut) or rut is None:
            return ''
        
        rut = str(rut).upper().replace('.', '').replace(' ', '').strip()
        
        # Si no tiene guión, agregarlo antes del dígito verificador
        if '-' not in rut and len(rut) > 1:
            rut = f"{rut[:-1]}-{rut[-1]}"
        
        return rut
    
    def normalizar_monto(self, monto) -> float:
        """
        Convierte monto a float, manejando formatos locales chilenos.
        
        Args:
            monto: Monto en cualquier formato
        
        Returns:
            Monto como float
        """
        if pd.isna(monto) or monto is None:
            return 0.0
        
        if isinstance(monto, (int, float)):
            return float(monto)
        
        # Limpiar formato chileno
        monto_str = str(monto).replace('$', '').replace(' ', '').strip()
        
        # Detectar formato
        if '.' in monto_str and ',' in monto_str:
            # 1.234,56 -> 1234.56
            monto_str = monto_str.replace('.', '').replace(',', '.')
        elif '.' in monto_str:
            # Si hay múltiples puntos son separadores de miles
            if monto_str.count('.') > 1:
                monto_str = monto_str.replace('.', '')
        elif ',' in monto_str:
            # 1234,56 -> 1234.56
            monto_str = monto_str.replace(',', '.')
        
        try:
            return float(monto_str)
        except ValueError:
            self.logger.warning(f"No se pudo convertir monto: {monto}")
            return 0.0
    
    def limpiar_texto(self, texto) -> str:
        """Limpia y normaliza texto."""
        if pd.isna(texto) or texto is None:
            return ''
        return str(texto).strip()
    
    def leer_excel(self, archivo, sheet_name=0, header=None, skiprows=None) -> pd.DataFrame:
        """
        Lee un archivo Excel con configuración estándar.
        
        Args:
            archivo: Archivo Excel
            sheet_name: Nombre o índice de la hoja
            header: Fila del encabezado (None para no usar header)
            skiprows: Filas a saltar
        
        Returns:
            DataFrame
        """
        return pd.read_excel(
            archivo,
            sheet_name=sheet_name,
            header=header,
            skiprows=skiprows
        )
    
    def analizar_headers_duplicados(self, df_columns) -> List[HeaderInfo]:
        """
        Analiza las columnas del DataFrame para detectar headers duplicados.
        
        Pandas automáticamente renombra headers duplicados agregando .1, .2, etc.
        Esta función detecta esos casos y genera HeaderInfo para cada columna.
        
        Args:
            df_columns: Columnas del DataFrame (df.columns)
        
        Returns:
            Lista de HeaderInfo con información de cada header
        """
        headers_info = []
        seen_originals = {}  # {original: count}
        
        for col in df_columns:
            col_str = str(col).strip()
            
            # Ignorar columnas sin nombre
            if col_str.startswith('Unnamed'):
                continue
            
            # Detectar si pandas agregó sufijo .N para duplicados
            original = col_str
            occurrence = 1
            is_duplicate = False
            
            # Pandas agrega .1, .2, .3 para duplicados
            import re
            match = re.match(r'^(.+)\.(\d+)$', col_str)
            if match:
                original = match.group(1)
                occurrence = int(match.group(2)) + 1  # .1 es la segunda ocurrencia
                is_duplicate = True
            
            # Actualizar contador de originales
            if original not in seen_originals:
                seen_originals[original] = 0
            seen_originals[original] += 1
            
            # Si es la primera vez que vemos este original pero ya hay .1, es duplicado
            if not is_duplicate and occurrence == 1:
                # Verificar si existe una versión .1 más adelante
                for future_col in df_columns:
                    if str(future_col).startswith(f"{original}."):
                        is_duplicate = True
                        break
            
            headers_info.append(HeaderInfo(
                original=original,
                pandas_name=col_str,
                occurrence=occurrence,
                is_duplicate=is_duplicate
            ))
        
        # Segunda pasada: marcar todos los originales que tienen duplicados
        for info in headers_info:
            if seen_originals.get(info.original, 0) > 1:
                info.is_duplicate = True
        
        return headers_info
    
    def calcular_totales_por_categoria(self, datos_json: Dict) -> Dict:
        """
        Calcula los totales desde datos_json.
        
        Args:
            datos_json: Dict con estructura {categoria: {concepto: monto}}
        
        Returns:
            Dict con totales calculados
        """
        from decimal import Decimal
        
        totales = {
            'total_haberes_imponibles': Decimal('0.00'),
            'total_haberes_no_imponibles': Decimal('0.00'),
            'total_descuentos_legales': Decimal('0.00'),
            'total_otros_descuentos': Decimal('0.00'),
            'total_aportes_patronales': Decimal('0.00'),
        }
        
        mapeo = {
            'haberes_imponibles': 'total_haberes_imponibles',
            'haberes_no_imponibles': 'total_haberes_no_imponibles',
            'descuentos_legales': 'total_descuentos_legales',
            'otros_descuentos': 'total_otros_descuentos',
            'aportes_patronales': 'total_aportes_patronales',
        }
        
        for categoria, campo_total in mapeo.items():
            if categoria in datos_json:
                total = datos_json[categoria].get('total', 0)
                totales[campo_total] = Decimal(str(total))
        
        # Calcular líquido
        totales['total_liquido'] = (
            totales['total_haberes_imponibles'] +
            totales['total_haberes_no_imponibles'] -
            totales['total_descuentos_legales'] -
            totales['total_otros_descuentos']
        )
        
        return totales
