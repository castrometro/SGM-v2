"""
SAP Strategy - Estrategia de parseo para archivos de SAP.

SAP exporta archivos en diferentes formatos según el módulo.
Esta estrategia soporta los formatos más comunes de SAP HCM.

Tipos de archivo soportados:
- libro_remuneraciones: Infotipo de nómina
- movimientos_mes: Transacciones del período
"""

import pandas as pd

from .base import ERPStrategy, ParseResult, FormatoEsperado
from .factory import ERPFactory


@ERPFactory.register('sap')
class SAPStrategy(ERPStrategy):
    """
    Estrategia de parseo para archivos de SAP HCM.
    
    SAP tiene formatos más complejos con códigos de infotipo.
    Esta implementación cubre los casos más comunes.
    """
    
    nombre_display = 'SAP'
    
    # Mapeo de columnas SAP -> Normalizado
    MAPEO_COLUMNAS = {
        # Identificación SAP
        'PERNR': 'rut',  # Número de personal (se mapea a RUT)
        'Nº personal': 'rut',
        'No. Personal': 'rut',
        'RUT': 'rut',
        'DNI': 'rut',
        
        # Nombre
        'ENAME': 'nombre',
        'Nombre empleado': 'nombre',
        'Apellidos/Nombre': 'nombre',
        'Nombre': 'nombre',
        
        # Concepto
        'LGART': 'codigo_concepto',  # Código de concepto de nómina
        'Cc.nómina': 'codigo_concepto',
        'Concepto nómina': 'concepto',
        'Texto Cc.nómina': 'concepto',
        'Denominación': 'concepto',
        
        # Tipo
        'Clase': 'tipo_concepto',
        'Tipo': 'tipo_concepto',
        
        # Monto
        'BETRG': 'monto',
        'Importe': 'monto',
        'Monto': 'monto',
        'Total': 'monto',
        
        # Adicionales SAP
        'BUKRS': 'sociedad',
        'Sociedad': 'sociedad',
        'KOSTL': 'centro_costo',
        'Centro coste': 'centro_costo',
        'ORGEH': 'unidad_organizativa',
        'Posición': 'cargo',
    }
    
    def get_tipos_archivo_soportados(self) -> list[str]:
        """Retorna tipos de archivo que soporta SAP."""
        return ['libro_remuneraciones', 'movimientos_mes']
    
    def parse_archivo(self, file, tipo_archivo: str) -> ParseResult:
        """Parsea archivo de SAP según su tipo."""
        try:
            if tipo_archivo == 'libro_remuneraciones':
                return self._parse_libro_remuneraciones(file)
            elif tipo_archivo == 'movimientos_mes':
                return self._parse_movimientos_mes(file)
            else:
                return ParseResult.fail(
                    f"Tipo de archivo no soportado para SAP: {tipo_archivo}. "
                    f"Soportados: {self.get_tipos_archivo_soportados()}"
                )
        except Exception as e:
            self.logger.error(f"Error parseando archivo SAP ({tipo_archivo}): {e}")
            return ParseResult.fail(f"Error al procesar archivo: {str(e)}")
    
    def _parse_libro_remuneraciones(self, file) -> ParseResult:
        """
        Parsea exportación de nómina de SAP.
        
        SAP puede exportar en Excel o TXT con delimitadores.
        """
        warnings = []
        filename = getattr(file, 'name', 'archivo.xlsx')
        extension = self.detectar_extension(filename)
        
        if extension in ['xlsx', 'xls']:
            df = self.leer_excel(file, sheet_name=0)
        elif extension == 'txt':
            # SAP a veces exporta TXT con tabuladores
            df = self.leer_csv(file, delimiter='\t', encoding='utf-8')
        else:
            df = self.leer_excel(file, sheet_name=0)
        
        df = self.mapear_columnas(df, self.MAPEO_COLUMNAS)
        df = self._normalizar_dataframe(df)
        
        es_valido, errores = self.validar_estructura(df, 'libro_remuneraciones')
        if not es_valido:
            return ParseResult.fail(f"Estructura inválida: {', '.join(errores)}")
        
        return ParseResult.ok(df, warnings)
    
    def _parse_movimientos_mes(self, file) -> ParseResult:
        """Parsea Movimientos del Mes de SAP."""
        df = self.leer_excel(file, sheet_name=0)
        df = self.mapear_columnas(df, self.MAPEO_COLUMNAS)
        df = self._normalizar_dataframe(df)
        
        es_valido, errores = self.validar_estructura(df, 'movimientos_mes')
        if not es_valido:
            return ParseResult.fail(f"Estructura inválida: {', '.join(errores)}")
        
        return ParseResult.ok(df)
    
    def _normalizar_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Normaliza las columnas estándar del DataFrame."""
        # SAP puede usar PERNR como ID, intentar convertir a RUT si es posible
        if 'rut' in df.columns:
            # Si parece ser número de personal de SAP (solo números)
            df['rut'] = df['rut'].apply(self._normalizar_identificador_sap)
        
        if 'monto' in df.columns:
            df['monto'] = df['monto'].apply(self.normalizar_monto)
        
        for col in ['nombre', 'concepto']:
            if col in df.columns:
                df[col] = df[col].apply(self.limpiar_texto)
        
        return df
    
    def _normalizar_identificador_sap(self, valor) -> str:
        """
        Normaliza identificador de SAP.
        
        Si es un RUT chileno, lo normaliza. Si es PERNR, lo deja como está.
        """
        if pd.isna(valor) or valor is None:
            return ''
        
        valor_str = str(valor).strip()
        
        # Si tiene guión o más de 8 caracteres, probablemente es RUT
        if '-' in valor_str or len(valor_str) > 8:
            return self.normalizar_rut(valor_str)
        
        # Si es solo números (PERNR de SAP), dejarlo como ID
        return valor_str
    
    def get_formato_esperado(self, tipo_archivo: str) -> FormatoEsperado:
        """Retorna formato esperado para SAP."""
        formatos = {
            'libro_remuneraciones': FormatoEsperado(
                extensiones=['xlsx', 'xls', 'txt'],
                columnas_requeridas=['rut', 'concepto', 'monto'],
                hoja='Primera hoja',
                fila_header=0,
                descripcion='Exportación de nómina desde SAP HCM',
            ),
            'movimientos_mes': FormatoEsperado(
                extensiones=['xlsx', 'xls', 'txt'],
                columnas_requeridas=['rut', 'concepto', 'monto'],
                hoja='Primera hoja',
                fila_header=0,
                descripcion='Transacciones del período desde SAP',
            ),
        }
        return formatos.get(tipo_archivo, FormatoEsperado(
            extensiones=['xlsx', 'xls', 'txt'],
            columnas_requeridas=[],
            descripcion='Formato desconocido'
        ))
    
    def validar_estructura(self, df: pd.DataFrame, tipo_archivo: str) -> tuple[bool, list[str]]:
        """Valida estructura del DataFrame para SAP."""
        errores = []
        formato = self.get_formato_esperado(tipo_archivo)
        
        es_valido, col_errores = self.validar_columnas_requeridas(
            df, formato.columnas_requeridas
        )
        errores.extend(col_errores)
        
        if df.empty:
            errores.append("El archivo no contiene datos")
        
        return len(errores) == 0, errores
