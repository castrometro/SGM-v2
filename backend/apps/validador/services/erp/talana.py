"""
Talana Strategy - Estrategia de parseo para archivos de Talana.

Talana es un sistema de gestión de recursos humanos que exporta archivos
en formato Excel con estructuras específicas.

Tipos de archivo soportados:
- libro_remuneraciones: Libro de remuneraciones mensual
- movimientos_mes: Movimientos del período
- centralizado: Centralizado de nómina
"""

import pandas as pd
from typing import Optional

from .base import ERPStrategy, ParseResult, FormatoEsperado
from .factory import ERPFactory


@ERPFactory.register('talana')
class TalanaStrategy(ERPStrategy):
    """
    Estrategia de parseo para archivos de Talana.
    
    Formatos soportados:
    - Libro de Remuneraciones (xlsx): Detalle por empleado y concepto
    - Movimientos del Mes (xlsx): Novedades del período
    - Centralizado de Nómina (xlsx): Resumen por concepto
    """
    
    nombre_display = 'Talana'
    
    # Mapeo de columnas Talana -> Normalizado
    MAPEO_COLUMNAS = {
        # Identificación
        'Rut': 'rut',
        'RUT': 'rut',
        'Rut Empleado': 'rut',
        'RUT Empleado': 'rut',
        
        # Nombre
        'Nombre Completo': 'nombre',
        'Nombre': 'nombre',
        'Empleado': 'nombre',
        'Nombre Empleado': 'nombre',
        
        # Concepto
        'Concepto': 'concepto',
        'Código Concepto': 'codigo_concepto',
        'Cod. Concepto': 'codigo_concepto',
        'Tipo Concepto': 'tipo_concepto',
        'Tipo': 'tipo_concepto',
        
        # Montos
        'Monto': 'monto',
        'Valor': 'monto',
        'Total': 'monto',
        'Importe': 'monto',
        
        # Adicionales
        'Centro de Costo': 'centro_costo',
        'Área': 'area',
        'Cargo': 'cargo',
        'Fecha Ingreso': 'fecha_ingreso',
        'Días Trabajados': 'dias_trabajados',
    }
    
    def get_tipos_archivo_soportados(self) -> list[str]:
        """Retorna tipos de archivo que soporta Talana."""
        return ['libro_remuneraciones', 'movimientos_mes', 'centralizado']
    
    def parse_archivo(self, file, tipo_archivo: str) -> ParseResult:
        """Parsea archivo de Talana según su tipo."""
        try:
            if tipo_archivo == 'libro_remuneraciones':
                return self._parse_libro_remuneraciones(file)
            elif tipo_archivo == 'movimientos_mes':
                return self._parse_movimientos_mes(file)
            elif tipo_archivo == 'centralizado':
                return self._parse_centralizado(file)
            else:
                return ParseResult.fail(
                    f"Tipo de archivo no soportado para Talana: {tipo_archivo}. "
                    f"Soportados: {self.get_tipos_archivo_soportados()}"
                )
        except Exception as e:
            self.logger.error(f"Error parseando archivo Talana ({tipo_archivo}): {e}")
            return ParseResult.fail(f"Error al procesar archivo: {str(e)}")
    
    def _parse_libro_remuneraciones(self, file) -> ParseResult:
        """
        Parsea Libro de Remuneraciones de Talana.
        
        Formato esperado:
        - Hoja: "Libro" o primera hoja
        - Columnas: Rut, Nombre Completo, Concepto, Monto
        """
        warnings = []
        
        # Intentar leer hoja "Libro", si no existe usar primera hoja
        try:
            df = self.leer_excel(file, sheet_name='Libro')
        except ValueError:
            df = self.leer_excel(file, sheet_name=0)
            warnings.append("No se encontró hoja 'Libro', usando primera hoja")
        
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
        """
        Parsea Movimientos del Mes de Talana.
        
        Formato esperado:
        - Primera hoja
        - Columnas: Rut, Nombre, Concepto, Monto
        """
        df = self.leer_excel(file, sheet_name=0)
        df = self.mapear_columnas(df, self.MAPEO_COLUMNAS)
        df = self._normalizar_dataframe(df)
        
        es_valido, errores = self.validar_estructura(df, 'movimientos_mes')
        if not es_valido:
            return ParseResult.fail(f"Estructura inválida: {', '.join(errores)}")
        
        return ParseResult.ok(df)
    
    def _parse_centralizado(self, file) -> ParseResult:
        """
        Parsea Centralizado de Nómina de Talana.
        
        Formato esperado:
        - Primera hoja
        - Columnas: Concepto, Total (puede ser resumen sin RUT individual)
        """
        df = self.leer_excel(file, sheet_name=0)
        df = self.mapear_columnas(df, self.MAPEO_COLUMNAS)
        
        # Para centralizado, normalizar montos pero RUT puede no existir
        if 'monto' in df.columns:
            df['monto'] = df['monto'].apply(self.normalizar_monto)
        
        if 'rut' in df.columns:
            df['rut'] = df['rut'].apply(self.normalizar_rut)
        
        es_valido, errores = self.validar_estructura(df, 'centralizado')
        if not es_valido:
            return ParseResult.fail(f"Estructura inválida: {', '.join(errores)}")
        
        return ParseResult.ok(df)
    
    def _normalizar_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Normaliza las columnas estándar del DataFrame."""
        # Normalizar RUT
        if 'rut' in df.columns:
            df['rut'] = df['rut'].apply(self.normalizar_rut)
        
        # Normalizar montos
        if 'monto' in df.columns:
            df['monto'] = df['monto'].apply(self.normalizar_monto)
        
        # Limpiar textos
        if 'nombre' in df.columns:
            df['nombre'] = df['nombre'].apply(self.limpiar_texto)
        
        if 'concepto' in df.columns:
            df['concepto'] = df['concepto'].apply(self.limpiar_texto)
        
        return df
    
    def get_formato_esperado(self, tipo_archivo: str) -> FormatoEsperado:
        """Retorna formato esperado para Talana."""
        formatos = {
            'libro_remuneraciones': FormatoEsperado(
                extensiones=['xlsx', 'xls'],
                columnas_requeridas=['rut', 'nombre', 'concepto', 'monto'],
                hoja='Libro (o primera hoja)',
                fila_header=0,
                descripcion='Libro de Remuneraciones exportado desde Talana',
            ),
            'movimientos_mes': FormatoEsperado(
                extensiones=['xlsx', 'xls'],
                columnas_requeridas=['rut', 'nombre', 'concepto', 'monto'],
                hoja='Primera hoja',
                fila_header=0,
                descripcion='Movimientos del mes exportados desde Talana',
            ),
            'centralizado': FormatoEsperado(
                extensiones=['xlsx', 'xls'],
                columnas_requeridas=['concepto', 'monto'],
                hoja='Primera hoja',
                fila_header=0,
                descripcion='Centralizado de nómina exportado desde Talana',
            ),
        }
        return formatos.get(tipo_archivo, FormatoEsperado(
            extensiones=['xlsx', 'xls'],
            columnas_requeridas=[],
            descripcion='Formato desconocido'
        ))
    
    def validar_estructura(self, df: pd.DataFrame, tipo_archivo: str) -> tuple[bool, list[str]]:
        """Valida estructura del DataFrame para Talana."""
        errores = []
        formato = self.get_formato_esperado(tipo_archivo)
        
        # Verificar columnas requeridas
        es_valido, col_errores = self.validar_columnas_requeridas(
            df, formato.columnas_requeridas
        )
        errores.extend(col_errores)
        
        # Verificar que no esté vacío
        if df.empty:
            errores.append("El archivo no contiene datos")
        
        # Validaciones específicas por tipo
        if tipo_archivo in ['libro_remuneraciones', 'movimientos_mes']:
            # Verificar que hay RUTs válidos
            if 'rut' in df.columns:
                ruts_validos = df['rut'].apply(lambda x: bool(x) and len(str(x)) > 5)
                if not ruts_validos.any():
                    errores.append("No se encontraron RUTs válidos en el archivo")
        
        return len(errores) == 0, errores
