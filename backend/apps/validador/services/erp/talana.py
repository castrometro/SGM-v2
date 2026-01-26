"""
Talana Strategy - Estrategia de parseo para archivos de Talana.

Talana es un sistema de gestión de recursos humanos que exporta archivos
en formato Excel con estructuras específicas.

Tipos de archivo soportados:
- libro_remuneraciones: Libro de remuneraciones mensual
- movimientos_mes: Movimientos del período (Altas/Bajas, Ausentismos, Vacaciones)
- centralizado: Centralizado de nómina
"""

import pandas as pd
from typing import Optional
from datetime import datetime

from .base import ERPStrategy, ParseResult, FormatoEsperado
from .factory import ERPFactory


@ERPFactory.register('talana')
class TalanaStrategy(ERPStrategy):
    """
    Estrategia de parseo para archivos de Talana.
    
    Formatos soportados:
    - Libro de Remuneraciones (xlsx): Detalle por empleado y concepto
    - Movimientos del Mes (xlsx): Altas, Bajas, Ausentismos, Vacaciones
    - Centralizado de Nómina (xlsx): Resumen por concepto
    """
    
    nombre_display = 'Talana'
    
    # Mapeo de columnas Talana -> Normalizado (Libro de Remuneraciones)
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
    
    # ============================================================
    # MAPEOS PARA MOVIMIENTOS DEL MES
    # ============================================================
    
    # Nombres de hojas esperadas
    HOJA_ALTAS_BAJAS = 'Altas y Bajas'
    HOJA_AUSENTISMOS = 'Ausentismos'
    HOJA_VACACIONES = 'Vacaciones'
    
    # Headers en fila 3 (índice 2), datos desde fila 4 (índice 3)
    MOVIMIENTOS_HEADER_ROW = 2
    
    # Mapeo de columnas para Altas y Bajas
    MAPEO_ALTAS_BAJAS = {
        'Nombre': 'nombre',
        'Rut': 'rut',
        'RUT': 'rut',
        'Fecha Ingreso': 'fecha_inicio',
        'Fecha Retiro': 'fecha_fin',
        'Tipo Contrato': 'tipo_contrato',
        'Alta / Baja': 'tipo_movimiento',
        'Alta/Baja': 'tipo_movimiento',
        'Motivo': 'causal',
    }
    
    # Mapeo de columnas para Ausentismos
    MAPEO_AUSENTISMOS = {
        'Nombre': 'nombre',
        'Rut': 'rut',
        'RUT': 'rut',
        'Fecha Inicio Ausencia': 'fecha_inicio',
        'Fecha Fin Ausencia': 'fecha_fin',
        'Dias': 'dias',
        'Días': 'dias',
        'Tipo de Ausentismo': 'tipo_ausentismo',
    }
    
    # Mapeo de columnas para Vacaciones
    MAPEO_VACACIONES = {
        'Nombre': 'nombre',
        'Rut': 'rut',
        'RUT': 'rut',
        'Fecha Inicial': 'fecha_inicio',
        'Fecha Fin Vacaciones': 'fecha_fin',
        'Cantidad de Dias': 'dias',
        'Cantidad de Días': 'dias',
    }
    
    # Mapeo de Tipo de Ausentismo -> (tipo, tipo_licencia)
    MAPEO_TIPO_AUSENTISMO = {
        'permiso con goce': ('asistencia', 'permiso_con_goce'),
        'permiso sin goce': ('asistencia', 'permiso_sin_goce'),
        'licencia medica': ('asistencia', 'licencia_medica'),
        'licencia médica': ('asistencia', 'licencia_medica'),
        'licencia maternal': ('asistencia', 'licencia_maternal'),
        'ausencia no justificada': ('asistencia', 'ausencia'),
        'ausencia injustificada': ('asistencia', 'ausencia'),
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
        
        Formato Talana:
        - Headers en fila 3 (índice 2)
        - Datos desde fila 4 (índice 3)
        - Hojas: "Altas y Bajas", "Ausentismos", "Vacaciones"
        
        Retorna dict con listas de registros normalizados por tipo.
        """
        warnings = []
        resultado = {
            'altas_bajas': [],
            'ausentismos': [],
            'vacaciones': [],
            'hojas_encontradas': [],
            'warnings': [],
        }
        
        try:
            excel_file = pd.ExcelFile(file)
            hojas_disponibles = excel_file.sheet_names
            resultado['hojas_encontradas'] = hojas_disponibles
        except Exception as e:
            return ParseResult.fail(f"Error al abrir archivo Excel: {str(e)}")
        
        # Procesar hoja Altas y Bajas
        if self.HOJA_ALTAS_BAJAS in hojas_disponibles:
            try:
                registros, warns = self._parse_hoja_altas_bajas(excel_file)
                resultado['altas_bajas'] = registros
                warnings.extend(warns)
            except Exception as e:
                warnings.append(f"Error procesando '{self.HOJA_ALTAS_BAJAS}': {str(e)}")
        else:
            warnings.append(f"Hoja '{self.HOJA_ALTAS_BAJAS}' no encontrada")
        
        # Procesar hoja Ausentismos
        if self.HOJA_AUSENTISMOS in hojas_disponibles:
            try:
                registros, warns = self._parse_hoja_ausentismos(excel_file)
                resultado['ausentismos'] = registros
                warnings.extend(warns)
            except Exception as e:
                warnings.append(f"Error procesando '{self.HOJA_AUSENTISMOS}': {str(e)}")
        else:
            warnings.append(f"Hoja '{self.HOJA_AUSENTISMOS}' no encontrada")
        
        # Procesar hoja Vacaciones
        if self.HOJA_VACACIONES in hojas_disponibles:
            try:
                registros, warns = self._parse_hoja_vacaciones(excel_file)
                resultado['vacaciones'] = registros
                warnings.extend(warns)
            except Exception as e:
                warnings.append(f"Error procesando '{self.HOJA_VACACIONES}': {str(e)}")
        else:
            warnings.append(f"Hoja '{self.HOJA_VACACIONES}' no encontrada")
        
        resultado['warnings'] = warnings
        
        # Verificar que al menos una hoja tenga datos
        total_registros = (
            len(resultado['altas_bajas']) + 
            len(resultado['ausentismos']) + 
            len(resultado['vacaciones'])
        )
        
        if total_registros == 0:
            return ParseResult.fail(
                "No se encontraron registros válidos en ninguna hoja. "
                f"Hojas disponibles: {hojas_disponibles}"
            )
        
        return ParseResult.ok(resultado, warnings)
    
    def _parse_hoja_altas_bajas(self, excel_file: pd.ExcelFile) -> tuple[list[dict], list[str]]:
        """
        Parsea hoja "Altas y Bajas".
        
        Aplica regla RN-001: Si baja + plazo fijo + sin motivo → ignorar
        """
        warnings = []
        registros = []
        
        df = pd.read_excel(
            excel_file,
            sheet_name=self.HOJA_ALTAS_BAJAS,
            header=self.MOVIMIENTOS_HEADER_ROW
        )
        
        # Mapear columnas
        df = self.mapear_columnas(df, self.MAPEO_ALTAS_BAJAS)
        
        for idx, row in df.iterrows():
            rut = self.normalizar_rut(row.get('rut', ''))
            if not rut:
                continue
            
            nombre = self.limpiar_texto(row.get('nombre', ''))
            tipo_mov = str(row.get('tipo_movimiento', '')).strip().lower()
            tipo_contrato = str(row.get('tipo_contrato', '')).strip()
            causal = str(row.get('causal', '')).strip() if pd.notna(row.get('causal')) else ''
            
            # Determinar tipo (ingreso o finiquito)
            if tipo_mov == 'alta':
                tipo = 'ingreso'
                fecha_inicio = self._parse_fecha(row.get('fecha_inicio'))
                fecha_fin = None
            elif tipo_mov == 'baja':
                tipo = 'finiquito'
                fecha_inicio = None
                fecha_fin = self._parse_fecha(row.get('fecha_fin'))
                
                # Regla RN-001: Ignorar baja de plazo fijo sin motivo
                if tipo_contrato.lower() == 'plazo fijo' and not causal:
                    warnings.append(
                        f"Ignorando baja fila {idx + self.MOVIMIENTOS_HEADER_ROW + 2}: "
                        f"Plazo Fijo sin motivo (vencimiento contrato)"
                    )
                    continue
            else:
                warnings.append(f"Tipo de movimiento desconocido en fila {idx + self.MOVIMIENTOS_HEADER_ROW + 2}: '{tipo_mov}'")
                continue
            
            registros.append({
                'tipo': tipo,
                'rut': rut,
                'nombre': nombre,
                'fecha_inicio': fecha_inicio,
                'fecha_fin': fecha_fin,
                'tipo_contrato': tipo_contrato,
                'causal': causal,
                'tipo_licencia': '',
                'dias': None,
                'hoja_origen': self.HOJA_ALTAS_BAJAS,
                'datos_raw': row.to_dict() if hasattr(row, 'to_dict') else dict(row),
            })
        
        return registros, warnings
    
    def _parse_hoja_ausentismos(self, excel_file: pd.ExcelFile) -> tuple[list[dict], list[str]]:
        """Parsea hoja "Ausentismos" (licencias, permisos, ausencias)."""
        warnings = []
        registros = []
        
        df = pd.read_excel(
            excel_file,
            sheet_name=self.HOJA_AUSENTISMOS,
            header=self.MOVIMIENTOS_HEADER_ROW
        )
        
        df = self.mapear_columnas(df, self.MAPEO_AUSENTISMOS)
        
        for idx, row in df.iterrows():
            rut = self.normalizar_rut(row.get('rut', ''))
            if not rut:
                continue
            
            nombre = self.limpiar_texto(row.get('nombre', ''))
            tipo_ausentismo_raw = str(row.get('tipo_ausentismo', '')).strip().lower()
            
            # Mapear tipo de ausentismo
            tipo, tipo_licencia = self.MAPEO_TIPO_AUSENTISMO.get(
                tipo_ausentismo_raw, ('otro', tipo_ausentismo_raw)
            )
            
            if tipo == 'otro':
                warnings.append(
                    f"Tipo de ausentismo no reconocido en fila {idx + self.MOVIMIENTOS_HEADER_ROW + 2}: "
                    f"'{tipo_ausentismo_raw}'"
                )
            
            dias = self._parse_int(row.get('dias'))
            
            registros.append({
                'tipo': tipo,
                'rut': rut,
                'nombre': nombre,
                'fecha_inicio': self._parse_fecha(row.get('fecha_inicio')),
                'fecha_fin': self._parse_fecha(row.get('fecha_fin')),
                'tipo_contrato': '',
                'causal': '',
                'tipo_licencia': tipo_licencia,
                'dias': dias,
                'hoja_origen': self.HOJA_AUSENTISMOS,
                'datos_raw': row.to_dict() if hasattr(row, 'to_dict') else dict(row),
            })
        
        return registros, warnings
    
    def _parse_hoja_vacaciones(self, excel_file: pd.ExcelFile) -> tuple[list[dict], list[str]]:
        """Parsea hoja "Vacaciones"."""
        warnings = []
        registros = []
        
        df = pd.read_excel(
            excel_file,
            sheet_name=self.HOJA_VACACIONES,
            header=self.MOVIMIENTOS_HEADER_ROW
        )
        
        df = self.mapear_columnas(df, self.MAPEO_VACACIONES)
        
        for idx, row in df.iterrows():
            rut = self.normalizar_rut(row.get('rut', ''))
            if not rut:
                continue
            
            nombre = self.limpiar_texto(row.get('nombre', ''))
            dias = self._parse_int(row.get('dias'))
            
            registros.append({
                'tipo': 'vacaciones',
                'rut': rut,
                'nombre': nombre,
                'fecha_inicio': self._parse_fecha(row.get('fecha_inicio')),
                'fecha_fin': self._parse_fecha(row.get('fecha_fin')),
                'tipo_contrato': '',
                'causal': '',
                'tipo_licencia': '',
                'dias': dias,
                'hoja_origen': self.HOJA_VACACIONES,
                'datos_raw': row.to_dict() if hasattr(row, 'to_dict') else dict(row),
            })
        
        return registros, warnings
    
    def _parse_fecha(self, valor) -> Optional[str]:
        """Convierte valor a fecha ISO (YYYY-MM-DD) o None."""
        if pd.isna(valor) or valor is None or str(valor).strip() == '':
            return None
        
        if isinstance(valor, datetime):
            return valor.strftime('%Y-%m-%d')
        
        if isinstance(valor, pd.Timestamp):
            return valor.strftime('%Y-%m-%d')
        
        # Intentar parsear string
        valor_str = str(valor).strip()
        formatos = ['%Y-%m-%d', '%d-%m-%Y', '%d/%m/%Y', '%Y/%m/%d']
        
        for fmt in formatos:
            try:
                return datetime.strptime(valor_str, fmt).strftime('%Y-%m-%d')
            except ValueError:
                continue
        
        return None
    
    def _parse_int(self, valor) -> Optional[int]:
        """Convierte valor a entero o None."""
        if pd.isna(valor) or valor is None:
            return None
        try:
            return int(float(valor))
        except (ValueError, TypeError):
            return None
    
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
                columnas_requeridas=['rut', 'nombre'],
                hoja='Altas y Bajas, Ausentismos, Vacaciones',
                fila_header=2,  # Headers en fila 3 (índice 2)
                descripcion=(
                    'Movimientos del mes de Talana. '
                    'Hojas: "Altas y Bajas", "Ausentismos", "Vacaciones". '
                    'Headers en fila 3.'
                ),
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
