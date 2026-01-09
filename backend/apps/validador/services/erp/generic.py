"""
Generic Strategy - Estrategia genérica/fallback para ERPs sin implementación específica.

Esta estrategia se usa cuando:
1. Un cliente tiene un ERP que no tiene implementación específica
2. Se quiere procesar un archivo con formato estándar

Asume un formato básico de Excel con columnas estándar.
"""

import pandas as pd
from typing import Optional

from .base import ERPStrategy, ParseResult, FormatoEsperado
from .factory import ERPFactory


@ERPFactory.register('generic')
class GenericStrategy(ERPStrategy):
    """
    Estrategia genérica para archivos ERP sin formato específico.
    
    Intenta detectar automáticamente las columnas y normalizarlas.
    Útil como fallback o para ERPs no implementados aún.
    """
    
    nombre_display = 'Genérico'
    
    # Mapeo extenso para detectar columnas comunes
    MAPEO_COLUMNAS_FLEXIBLE = {
        # RUT - múltiples variantes
        'rut': 'rut',
        'RUT': 'rut',
        'Rut': 'rut',
        'rut empleado': 'rut',
        'RUT Empleado': 'rut',
        'rut_empleado': 'rut',
        'identificacion': 'rut',
        'cedula': 'rut',
        
        # Nombre - múltiples variantes
        'nombre': 'nombre',
        'Nombre': 'nombre',
        'NOMBRE': 'nombre',
        'nombre completo': 'nombre',
        'Nombre Completo': 'nombre',
        'empleado': 'nombre',
        'Empleado': 'nombre',
        'trabajador': 'nombre',
        'Trabajador': 'nombre',
        
        # Concepto
        'concepto': 'concepto',
        'Concepto': 'concepto',
        'CONCEPTO': 'concepto',
        'descripcion': 'concepto',
        'Descripcion': 'concepto',
        'descripción': 'concepto',
        'Descripción': 'concepto',
        'detalle': 'concepto',
        'Detalle': 'concepto',
        
        # Monto
        'monto': 'monto',
        'Monto': 'monto',
        'MONTO': 'monto',
        'valor': 'monto',
        'Valor': 'monto',
        'VALOR': 'monto',
        'total': 'monto',
        'Total': 'monto',
        'TOTAL': 'monto',
        'importe': 'monto',
        'Importe': 'monto',
        'cantidad': 'monto',
        'Cantidad': 'monto',
        
        # Código concepto
        'codigo': 'codigo_concepto',
        'Codigo': 'codigo_concepto',
        'código': 'codigo_concepto',
        'Código': 'codigo_concepto',
        'cod': 'codigo_concepto',
        'Cod': 'codigo_concepto',
        'codigo_concepto': 'codigo_concepto',
        
        # Tipo concepto
        'tipo': 'tipo_concepto',
        'Tipo': 'tipo_concepto',
        'tipo_concepto': 'tipo_concepto',
        'clasificacion': 'tipo_concepto',
        'Clasificacion': 'tipo_concepto',
    }
    
    def get_tipos_archivo_soportados(self) -> list[str]:
        """Retorna tipos de archivo que soporta la estrategia genérica."""
        return ['libro_remuneraciones', 'movimientos_mes', 'centralizado', 'generico']
    
    def parse_archivo(self, file, tipo_archivo: str) -> ParseResult:
        """
        Parsea archivo con estrategia genérica.
        
        Intenta detectar automáticamente el formato y normalizar.
        """
        try:
            # Detectar extensión
            filename = getattr(file, 'name', 'archivo.xlsx')
            extension = self.detectar_extension(filename)
            
            # Leer archivo según extensión
            if extension in ['xlsx', 'xls']:
                df = self._leer_excel_inteligente(file)
            elif extension == 'csv':
                df = self._leer_csv_inteligente(file)
            else:
                return ParseResult.fail(
                    f"Extensión no soportada: {extension}. "
                    f"Use xlsx, xls o csv"
                )
            
            # Mapear columnas
            df = self.mapear_columnas(df, self.MAPEO_COLUMNAS_FLEXIBLE)
            
            # Normalizar datos
            df = self._normalizar_dataframe(df)
            
            # Generar warnings sobre columnas no mapeadas
            warnings = self._detectar_columnas_no_mapeadas(df)
            
            # Validar estructura básica
            es_valido, errores = self.validar_estructura(df, tipo_archivo)
            if not es_valido:
                return ParseResult.fail(f"Estructura inválida: {', '.join(errores)}")
            
            return ParseResult.ok(df, warnings)
            
        except Exception as e:
            self.logger.error(f"Error parseando archivo genérico: {e}")
            return ParseResult.fail(f"Error al procesar archivo: {str(e)}")
    
    def _leer_excel_inteligente(self, file) -> pd.DataFrame:
        """
        Lee Excel intentando detectar la hoja correcta.
        """
        # Primero intentar leer todas las hojas disponibles
        try:
            excel_file = pd.ExcelFile(file)
            hojas = excel_file.sheet_names
            
            # Buscar hojas con nombres comunes
            hojas_prioritarias = ['libro', 'datos', 'remuneraciones', 'nomina', 'hoja1', 'sheet1']
            
            for hoja in hojas:
                if hoja.lower() in hojas_prioritarias:
                    return pd.read_excel(file, sheet_name=hoja)
            
            # Si no encuentra, usar primera hoja
            return pd.read_excel(file, sheet_name=0)
            
        except Exception:
            # Fallback simple
            return self.leer_excel(file, sheet_name=0)
    
    def _leer_csv_inteligente(self, file) -> pd.DataFrame:
        """
        Lee CSV detectando automáticamente delimitador y encoding.
        """
        # Intentar diferentes configuraciones
        configuraciones = [
            {'delimiter': ',', 'encoding': 'utf-8'},
            {'delimiter': ';', 'encoding': 'utf-8'},
            {'delimiter': ',', 'encoding': 'latin-1'},
            {'delimiter': ';', 'encoding': 'latin-1'},
            {'delimiter': '\t', 'encoding': 'utf-8'},
        ]
        
        for config in configuraciones:
            try:
                file.seek(0)  # Resetear posición del archivo
                df = self.leer_csv(file, **config)
                if len(df.columns) > 1:  # Si parseó correctamente
                    return df
            except Exception:
                continue
        
        # Último intento con configuración por defecto
        file.seek(0)
        return self.leer_csv(file)
    
    def _normalizar_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Normaliza las columnas estándar del DataFrame."""
        # Normalizar RUT
        if 'rut' in df.columns:
            df['rut'] = df['rut'].apply(self.normalizar_rut)
        
        # Normalizar montos
        if 'monto' in df.columns:
            df['monto'] = df['monto'].apply(self.normalizar_monto)
        
        # Limpiar textos
        for col in ['nombre', 'concepto']:
            if col in df.columns:
                df[col] = df[col].apply(self.limpiar_texto)
        
        return df
    
    def _detectar_columnas_no_mapeadas(self, df: pd.DataFrame) -> list[str]:
        """Detecta columnas que no pudieron mapearse."""
        warnings = []
        columnas_normalizadas = {'rut', 'nombre', 'concepto', 'monto', 'codigo_concepto', 'tipo_concepto'}
        
        for col in df.columns:
            if col not in columnas_normalizadas:
                warnings.append(f"Columna no mapeada: '{col}'")
        
        return warnings
    
    def get_formato_esperado(self, tipo_archivo: str) -> FormatoEsperado:
        """Retorna formato esperado genérico."""
        return FormatoEsperado(
            extensiones=['xlsx', 'xls', 'csv'],
            columnas_requeridas=['rut', 'concepto', 'monto'],
            hoja='Primera hoja',
            fila_header=0,
            descripcion='Formato genérico. Se detectarán automáticamente las columnas.',
        )
    
    def validar_estructura(self, df: pd.DataFrame, tipo_archivo: str) -> tuple[bool, list[str]]:
        """Valida estructura básica del DataFrame."""
        errores = []
        
        # Verificar que no esté vacío
        if df.empty:
            errores.append("El archivo no contiene datos")
            return False, errores
        
        # Para genérico, ser más flexible con las columnas requeridas
        # Al menos debe tener alguna columna identificadora y algún monto
        tiene_identificador = 'rut' in df.columns or 'nombre' in df.columns
        tiene_monto = 'monto' in df.columns
        tiene_concepto = 'concepto' in df.columns
        
        if not tiene_identificador:
            errores.append("No se encontró columna de identificación (rut o nombre)")
        
        if not tiene_monto:
            errores.append("No se encontró columna de monto")
        
        if not tiene_concepto:
            errores.append("No se encontró columna de concepto")
        
        return len(errores) == 0, errores
