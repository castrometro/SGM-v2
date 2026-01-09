"""
ERP Strategy Base - Clase abstracta para estrategias de parseo de archivos ERP.

Cada ERP (Talana, BUK, SAP, etc.) implementa su propia estrategia para:
- Parsear archivos (xlsx, csv, txt) en diferentes formatos
- Normalizar datos a un formato común
- Validar estructura de archivos

Uso:
    from apps.validador.services.erp import ERPFactory
    
    strategy = ERPFactory.get_strategy('talana')
    df = strategy.parse_archivo(file, 'libro_remuneraciones')
    formato = strategy.get_formato_esperado('libro_remuneraciones')
"""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Optional
from dataclasses import dataclass
import pandas as pd
import logging

if TYPE_CHECKING:
    from apps.core.models import ERP

logger = logging.getLogger(__name__)


@dataclass
class ParseResult:
    """Resultado del parseo de un archivo."""
    success: bool
    data: Optional[pd.DataFrame] = None
    error: Optional[str] = None
    warnings: list = None
    
    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []
    
    @classmethod
    def ok(cls, data: pd.DataFrame, warnings: list = None) -> 'ParseResult':
        """Crea un resultado exitoso."""
        return cls(success=True, data=data, warnings=warnings or [])
    
    @classmethod
    def fail(cls, error: str) -> 'ParseResult':
        """Crea un resultado fallido."""
        return cls(success=False, error=error)


@dataclass
class FormatoEsperado:
    """Información sobre el formato esperado de un archivo."""
    extensiones: list[str]
    columnas_requeridas: list[str]
    hoja: Optional[str] = None
    fila_header: int = 0
    descripcion: str = ''
    ejemplo_url: Optional[str] = None


class ERPStrategy(ABC):
    """
    Estrategia base para procesamiento de archivos ERP.
    
    Cada ERP implementa su propia estrategia heredando de esta clase
    e implementando los métodos abstractos.
    
    Attributes:
        erp_slug: Slug único del ERP (asignado por Factory.register)
        nombre_display: Nombre para mostrar del ERP
        config: Configuración de parseo del modelo ERP
    """
    
    erp_slug: str = None
    nombre_display: str = None
    
    def __init__(self, erp_config: dict = None):
        """
        Args:
            erp_config: Configuración de parseo del modelo ERP.configuracion_parseo
        """
        self.config = erp_config or {}
        self.logger = logging.getLogger(f'{__name__}.{self.__class__.__name__}')
    
    @abstractmethod
    def parse_archivo(self, file, tipo_archivo: str) -> ParseResult:
        """
        Parsea un archivo del ERP y retorna DataFrame normalizado.
        
        Args:
            file: Archivo subido (InMemoryUploadedFile o similar)
            tipo_archivo: Tipo de archivo ('libro_remuneraciones', 'movimientos_mes', etc.)
        
        Returns:
            ParseResult con DataFrame normalizado o error
        """
        pass
    
    @abstractmethod
    def get_formato_esperado(self, tipo_archivo: str) -> FormatoEsperado:
        """
        Retorna el formato esperado del archivo.
        
        Args:
            tipo_archivo: Tipo de archivo
        
        Returns:
            FormatoEsperado con información del formato
        """
        pass
    
    @abstractmethod
    def validar_estructura(self, df: pd.DataFrame, tipo_archivo: str) -> tuple[bool, list[str]]:
        """
        Valida que el DataFrame tenga la estructura correcta.
        
        Args:
            df: DataFrame a validar
            tipo_archivo: Tipo de archivo
        
        Returns:
            Tuple (es_valido, lista_errores)
        """
        pass
    
    @abstractmethod
    def get_tipos_archivo_soportados(self) -> list[str]:
        """
        Retorna lista de tipos de archivo que soporta este ERP.
        
        Returns:
            Lista de tipos: ['libro_remuneraciones', 'movimientos_mes', etc.]
        """
        pass
    
    # =========================================================================
    # Métodos de utilidad (compartidos por todas las estrategias)
    # =========================================================================
    
    def normalizar_rut(self, rut) -> str:
        """
        Normaliza RUT a formato estándar (sin puntos, con guión).
        
        Args:
            rut: RUT en cualquier formato
        
        Returns:
            RUT normalizado: '12345678-9'
        
        Examples:
            >>> strategy.normalizar_rut('12.345.678-9')
            '12345678-9'
            >>> strategy.normalizar_rut('123456789')
            '12345678-9'
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
        
        Examples:
            >>> strategy.normalizar_monto('$1.234.567')
            1234567.0
            >>> strategy.normalizar_monto('1234,56')
            1234.56
        """
        if pd.isna(monto) or monto is None:
            return 0.0
        
        if isinstance(monto, (int, float)):
            return float(monto)
        
        # Limpiar formato chileno: $1.234.567 -> 1234567
        monto_str = str(monto).replace('$', '').replace(' ', '').strip()
        
        # Detectar formato: si tiene punto como separador de miles
        # El formato chileno usa punto para miles y coma para decimales
        if '.' in monto_str and ',' in monto_str:
            # Tiene ambos: 1.234,56 -> quitar puntos, coma a punto
            monto_str = monto_str.replace('.', '').replace(',', '.')
        elif '.' in monto_str:
            # Solo puntos: podría ser 1.234.567 (miles) o 1234.56 (decimal)
            # Contar puntos: si hay más de uno, son separadores de miles
            if monto_str.count('.') > 1:
                monto_str = monto_str.replace('.', '')
            # Si solo hay un punto, asumimos que es decimal (formato internacional)
        elif ',' in monto_str:
            # Solo coma: 1234,56 -> 1234.56
            monto_str = monto_str.replace(',', '.')
        
        try:
            return float(monto_str)
        except ValueError:
            self.logger.warning(f"No se pudo convertir monto: {monto}")
            return 0.0
    
    def normalizar_fecha(self, fecha, formato: str = None) -> Optional[str]:
        """
        Normaliza fecha a formato ISO (YYYY-MM-DD).
        
        Args:
            fecha: Fecha en cualquier formato
            formato: Formato específico de entrada (opcional)
        
        Returns:
            Fecha en formato ISO o None si no se puede parsear
        """
        if pd.isna(fecha) or fecha is None:
            return None
        
        try:
            if formato:
                parsed = pd.to_datetime(fecha, format=formato)
            else:
                parsed = pd.to_datetime(fecha, dayfirst=True)
            return parsed.strftime('%Y-%m-%d')
        except Exception as e:
            self.logger.warning(f"No se pudo parsear fecha '{fecha}': {e}")
            return None
    
    def limpiar_texto(self, texto) -> str:
        """Limpia y normaliza texto."""
        if pd.isna(texto) or texto is None:
            return ''
        return str(texto).strip()
    
    def detectar_extension(self, filename: str) -> str:
        """Detecta la extensión de un archivo."""
        if '.' in filename:
            return filename.rsplit('.', 1)[-1].lower()
        return ''
    
    def leer_excel(self, file, sheet_name=0, header=0, **kwargs) -> pd.DataFrame:
        """
        Lee un archivo Excel con configuración estándar.
        
        Args:
            file: Archivo Excel
            sheet_name: Nombre o índice de la hoja
            header: Fila del encabezado
            **kwargs: Argumentos adicionales para read_excel
        
        Returns:
            DataFrame
        """
        return pd.read_excel(
            file,
            sheet_name=sheet_name,
            header=header,
            **kwargs
        )
    
    def leer_csv(self, file, delimiter=',', encoding='utf-8', **kwargs) -> pd.DataFrame:
        """
        Lee un archivo CSV con configuración estándar.
        
        Args:
            file: Archivo CSV
            delimiter: Delimitador de campos
            encoding: Codificación del archivo
            **kwargs: Argumentos adicionales para read_csv
        
        Returns:
            DataFrame
        """
        return pd.read_csv(
            file,
            delimiter=delimiter,
            encoding=encoding,
            **kwargs
        )
    
    def mapear_columnas(self, df: pd.DataFrame, mapeo: dict) -> pd.DataFrame:
        """
        Renombra columnas según un mapeo.
        
        Args:
            df: DataFrame original
            mapeo: Dict de {nombre_original: nombre_normalizado}
        
        Returns:
            DataFrame con columnas renombradas
        """
        # Solo renombrar columnas que existen
        mapeo_existente = {k: v for k, v in mapeo.items() if k in df.columns}
        return df.rename(columns=mapeo_existente)
    
    def validar_columnas_requeridas(
        self, 
        df: pd.DataFrame, 
        columnas_requeridas: list[str]
    ) -> tuple[bool, list[str]]:
        """
        Valida que el DataFrame tenga las columnas requeridas.
        
        Args:
            df: DataFrame a validar
            columnas_requeridas: Lista de columnas que deben existir
        
        Returns:
            Tuple (es_valido, errores)
        """
        errores = []
        columnas_df = [c.lower() for c in df.columns]
        
        for col in columnas_requeridas:
            if col.lower() not in columnas_df:
                errores.append(f"Columna requerida faltante: {col}")
        
        return len(errores) == 0, errores
