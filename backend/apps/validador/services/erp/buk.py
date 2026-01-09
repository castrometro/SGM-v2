"""
BUK Strategy - Estrategia de parseo para archivos de BUK.

BUK es un sistema de gestión de recursos humanos que exporta archivos
en formato Excel con estructuras específicas.

Tipos de archivo soportados:
- libro_remuneraciones: Libro de remuneraciones mensual
- movimientos_mes: Movimientos del período
"""

import pandas as pd

from .base import ERPStrategy, ParseResult, FormatoEsperado
from .factory import ERPFactory


@ERPFactory.register('buk')
class BukStrategy(ERPStrategy):
    """
    Estrategia de parseo para archivos de BUK.
    
    Formatos soportados:
    - Libro de Remuneraciones (xlsx)
    - Movimientos del Mes (xlsx)
    """
    
    nombre_display = 'BUK'
    
    # Mapeo de columnas BUK -> Normalizado
    MAPEO_COLUMNAS = {
        # Identificación
        'Rut': 'rut',
        'RUT': 'rut',
        'Identificación': 'rut',
        
        # Nombre
        'Nombre': 'nombre',
        'Nombre Completo': 'nombre',
        'Colaborador': 'nombre',
        
        # Concepto
        'Concepto': 'concepto',
        'Item': 'concepto',
        'Ítem': 'concepto',
        'Descripción': 'concepto',
        
        # Código
        'Código': 'codigo_concepto',
        'Codigo': 'codigo_concepto',
        'Cod': 'codigo_concepto',
        
        # Tipo
        'Tipo': 'tipo_concepto',
        'Clasificación': 'tipo_concepto',
        
        # Monto
        'Monto': 'monto',
        'Valor': 'monto',
        'Total': 'monto',
        'Haberes': 'monto',
        'Descuentos': 'monto',
        
        # Adicionales BUK
        'Centro de Costo': 'centro_costo',
        'Sucursal': 'sucursal',
        'Área': 'area',
        'Cargo': 'cargo',
    }
    
    def get_tipos_archivo_soportados(self) -> list[str]:
        """Retorna tipos de archivo que soporta BUK."""
        return ['libro_remuneraciones', 'movimientos_mes']
    
    def parse_archivo(self, file, tipo_archivo: str) -> ParseResult:
        """Parsea archivo de BUK según su tipo."""
        try:
            if tipo_archivo == 'libro_remuneraciones':
                return self._parse_libro_remuneraciones(file)
            elif tipo_archivo == 'movimientos_mes':
                return self._parse_movimientos_mes(file)
            else:
                return ParseResult.fail(
                    f"Tipo de archivo no soportado para BUK: {tipo_archivo}. "
                    f"Soportados: {self.get_tipos_archivo_soportados()}"
                )
        except Exception as e:
            self.logger.error(f"Error parseando archivo BUK ({tipo_archivo}): {e}")
            return ParseResult.fail(f"Error al procesar archivo: {str(e)}")
    
    def _parse_libro_remuneraciones(self, file) -> ParseResult:
        """
        Parsea Libro de Remuneraciones de BUK.
        
        BUK típicamente usa la primera hoja.
        """
        warnings = []
        
        df = self.leer_excel(file, sheet_name=0)
        
        # Mapear columnas
        df = self.mapear_columnas(df, self.MAPEO_COLUMNAS)
        
        # Normalizar datos
        df = self._normalizar_dataframe(df)
        
        # Validar estructura
        es_valido, errores = self.validar_estructura(df, 'libro_remuneraciones')
        if not es_valido:
            return ParseResult.fail(f"Estructura inválida: {', '.join(errores)}")
        
        return ParseResult.ok(df, warnings)
    
    def _parse_movimientos_mes(self, file) -> ParseResult:
        """Parsea Movimientos del Mes de BUK."""
        df = self.leer_excel(file, sheet_name=0)
        df = self.mapear_columnas(df, self.MAPEO_COLUMNAS)
        df = self._normalizar_dataframe(df)
        
        es_valido, errores = self.validar_estructura(df, 'movimientos_mes')
        if not es_valido:
            return ParseResult.fail(f"Estructura inválida: {', '.join(errores)}")
        
        return ParseResult.ok(df)
    
    def _normalizar_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Normaliza las columnas estándar del DataFrame."""
        if 'rut' in df.columns:
            df['rut'] = df['rut'].apply(self.normalizar_rut)
        
        if 'monto' in df.columns:
            df['monto'] = df['monto'].apply(self.normalizar_monto)
        
        for col in ['nombre', 'concepto']:
            if col in df.columns:
                df[col] = df[col].apply(self.limpiar_texto)
        
        return df
    
    def get_formato_esperado(self, tipo_archivo: str) -> FormatoEsperado:
        """Retorna formato esperado para BUK."""
        formatos = {
            'libro_remuneraciones': FormatoEsperado(
                extensiones=['xlsx', 'xls'],
                columnas_requeridas=['rut', 'nombre', 'concepto', 'monto'],
                hoja='Primera hoja',
                fila_header=0,
                descripcion='Libro de Remuneraciones exportado desde BUK',
            ),
            'movimientos_mes': FormatoEsperado(
                extensiones=['xlsx', 'xls'],
                columnas_requeridas=['rut', 'nombre', 'concepto', 'monto'],
                hoja='Primera hoja',
                fila_header=0,
                descripcion='Movimientos del mes exportados desde BUK',
            ),
        }
        return formatos.get(tipo_archivo, FormatoEsperado(
            extensiones=['xlsx', 'xls'],
            columnas_requeridas=[],
            descripcion='Formato desconocido'
        ))
    
    def validar_estructura(self, df: pd.DataFrame, tipo_archivo: str) -> tuple[bool, list[str]]:
        """Valida estructura del DataFrame para BUK."""
        errores = []
        formato = self.get_formato_esperado(tipo_archivo)
        
        es_valido, col_errores = self.validar_columnas_requeridas(
            df, formato.columnas_requeridas
        )
        errores.extend(col_errores)
        
        if df.empty:
            errores.append("El archivo no contiene datos")
        
        return len(errores) == 0, errores
