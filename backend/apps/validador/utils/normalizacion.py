"""
Utilidades de normalización y sanitización de datos.

Funciones compartidas entre procesamiento de archivos ERP y Analista.
Extraídas para evitar duplicación y mejorar mantenibilidad.

Seguridad:
- mask_rut: Protección de PII según Ley 21.719
- validar_ruta_archivo: Prevención de path traversal (CWE-22)
- sanitizar_datos_raw: Prevención de errores JSON con NaN/Inf
"""

from datetime import date, datetime
from pathlib import Path
from typing import Optional, Union
import pandas as pd
import logging

logger = logging.getLogger(__name__)


def normalizar_rut(rut: Union[str, float, int, None]) -> str:
    """
    Normaliza RUT a formato estándar (sin puntos, con guión).
    
    Args:
        rut: RUT en cualquier formato
    
    Returns:
        RUT normalizado: '12345678-9', o string vacío si inválido
    
    Examples:
        >>> normalizar_rut('12.345.678-9')
        '12345678-9'
        >>> normalizar_rut('123456789')
        '12345678-9'
        >>> normalizar_rut(None)
        ''
    """
    if pd.isna(rut) or rut is None:
        return ''
    
    rut = str(rut).upper().replace('.', '').replace(' ', '').strip()
    
    # Si no tiene guión, agregarlo antes del dígito verificador
    if '-' not in rut and len(rut) > 1:
        rut = f"{rut[:-1]}-{rut[-1]}"
    
    return rut


def mask_rut(rut: str) -> str:
    """
    Enmascara RUT para logs, mostrando solo últimos 4 caracteres.
    Protege PII según Ley 21.719.
    
    Args:
        rut: RUT completo (ej: "12345678-9")
        
    Returns:
        RUT enmascarado (ej: "****78-9")
    
    Examples:
        >>> mask_rut('12345678-9')
        '****78-9'
        >>> mask_rut('123')
        '****'
    """
    if not rut or len(rut) < 5:
        return "****"
    return f"****{rut[-4:]}"


def normalizar_monto(monto: Union[str, float, int, None]) -> float:
    """
    Convierte monto a float, manejando formatos locales chilenos.
    
    Args:
        monto: Monto en cualquier formato
    
    Returns:
        Monto como float, 0.0 si es inválido
    
    Examples:
        >>> normalizar_monto('$1.234.567')
        1234567.0
        >>> normalizar_monto('1234,56')
        1234.56
    """
    if pd.isna(monto) or monto is None:
        return 0.0
    
    if isinstance(monto, (int, float)):
        return float(monto)
    
    # Limpiar formato chileno: $1.234.567 -> 1234567
    monto_str = str(monto).replace('$', '').replace(' ', '').strip()
    
    # Detectar formato: si tiene punto como separador de miles
    if '.' in monto_str and ',' in monto_str:
        # Tiene ambos: 1.234,56 -> quitar puntos, coma a punto
        monto_str = monto_str.replace('.', '').replace(',', '.')
    elif '.' in monto_str:
        # Solo puntos: 1.234.567 (miles) vs 1234.56 (decimal)
        puntos = monto_str.count('.')
        if puntos > 1:
            # Múltiples puntos = separador de miles
            monto_str = monto_str.replace('.', '')
    elif ',' in monto_str:
        # Solo coma: probablemente decimal
        monto_str = monto_str.replace(',', '.')
    
    try:
        return float(monto_str)
    except ValueError:
        return 0.0


def parse_fecha(valor: Union[str, datetime, pd.Timestamp, None]) -> Optional[date]:
    """
    Parsea fecha de archivo Excel/CSV.
    Retorna date object o None.
    
    Soporta formatos:
    - datetime/Timestamp objects
    - Strings: YYYY-MM-DD, DD-MM-YYYY, DD/MM/YYYY, YYYY/MM/DD
    
    Args:
        valor: Valor a parsear
        
    Returns:
        date object o None si no se puede parsear
    """
    if pd.isna(valor) or valor is None:
        return None
    
    if isinstance(valor, date) and not isinstance(valor, datetime):
        return valor
    
    if isinstance(valor, datetime):
        return valor.date()
    
    if isinstance(valor, pd.Timestamp):
        return valor.date()
    
    # Intentar parsear string
    valor_str = str(valor).strip()
    if not valor_str or valor_str.lower() == 'nan':
        return None
    
    formatos = ['%Y-%m-%d', '%d-%m-%Y', '%d/%m/%Y', '%Y/%m/%d']
    
    for fmt in formatos:
        try:
            return datetime.strptime(valor_str, fmt).date()
        except ValueError:
            continue
    
    return None


def sanitizar_datos_raw(datos: dict) -> dict:
    """
    Sanitiza datos_raw para almacenamiento JSON.
    Convierte NaN/Inf a None, tipos no serializables a string.
    
    Previene errores de PostgreSQL jsonb:
    - "Token NaN is invalid"
    - "Token Infinity is invalid"
    
    Args:
        datos: Diccionario con datos crudos de fila Excel
        
    Returns:
        Diccionario sanitizado, seguro para JSON
    """
    if not datos:
        return {}
    
    resultado = {}
    for k, v in datos.items():
        if isinstance(v, float):
            # NaN check: NaN != NaN es True
            if v != v or v == float('inf') or v == float('-inf'):
                resultado[k] = None
                continue
        
        if not isinstance(v, (str, int, float, bool, type(None))):
            resultado[k] = str(v)
        else:
            resultado[k] = v
    
    return resultado


def validar_ruta_archivo(file_path: str) -> bool:
    """
    Valida que la ruta del archivo esté dentro de MEDIA_ROOT.
    Previene ataques de path traversal (CWE-22).
    
    Args:
        file_path: Ruta del archivo a validar
        
    Returns:
        True si la ruta es segura, False si es sospechosa
        
    Raises:
        ValueError: Si la ruta es sospechosa (para uso directo)
    """
    from django.conf import settings
    
    try:
        # Resolver rutas a absolutas y canonicalizadas
        media_root = Path(settings.MEDIA_ROOT).resolve()
        archivo_path = Path(file_path).resolve()
        
        # Verificar que el archivo está dentro de MEDIA_ROOT
        if not str(archivo_path).startswith(str(media_root)):
            logger.warning(f"Intento de acceso a ruta fuera de MEDIA_ROOT: {archivo_path}")
            return False
        
        return True
    except Exception as e:
        logger.error(f"Error validando ruta de archivo: {e}")
        return False


def validar_ruta_archivo_strict(file_path: str) -> None:
    """
    Versión estricta de validar_ruta_archivo que lanza excepción.
    
    Args:
        file_path: Ruta del archivo a validar
        
    Raises:
        ValueError: Si la ruta es sospechosa o inválida
    """
    if not validar_ruta_archivo(file_path):
        raise ValueError("Ruta de archivo no permitida")
