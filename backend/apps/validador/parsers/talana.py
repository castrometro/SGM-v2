"""
Parser para Libro de Remuneraciones de Talana.

Talana exporta el libro en formato Excel con una estructura específica.
"""

import pandas as pd
from typing import List, Dict
from decimal import Decimal

from .base import BaseLibroParser, ProcessResult
from .factory import ParserFactory


@ParserFactory.register('talana')
class TalanaLibroParser(BaseLibroParser):
    """
    Parser para archivos de Libro de Remuneraciones de Talana.
    
    Formato esperado:
    - Archivo Excel (.xlsx, .xls)
    - Hoja: "Libro" o primera hoja disponible
    - Fila 0: Headers
    - Fila 1+: Datos de empleados
    - Columnas típicas: RUT, Nombre, [Conceptos variados según cliente]
    
    Los primeros 8 headers SIEMPRE son datos del empleado (no conceptos monetarios).
    """
    
    # ==========================================================================
    # Headers fijos de Talana (primeras 8 columnas siempre son datos del empleado)
    # ==========================================================================
    # Estructura típica del libro de Talana:
    #   0: Año
    #   1: Mes
    #   2: Rut de la Empresa
    #   3: Rut del Trabajador  <- IDENTIFICADOR
    #   4: Nombre
    #   5: Apellido Paterno
    #   6: Apellido Materno
    #   7: Días Trabajados
    #   8+: Conceptos monetarios (requieren clasificación manual)
    
    COLUMNAS_EMPLEADO_CANTIDAD = 8
    
    # Índice de la columna que contiene el RUT del trabajador
    COLUMNA_RUT_TRABAJADOR = 3
    
    # Mapeo de índices a categoría para clasificación automática
    # Todas las primeras 8 columnas son info_adicional (datos del empleado)
    CLASIFICACION_AUTO_EMPLEADO = {
        0: 'info_adicional',  # Año
        1: 'info_adicional',  # Mes
        2: 'info_adicional',  # Rut de la Empresa
        3: 'info_adicional',  # Rut del Trabajador (identificador por posición)
        4: 'info_adicional',  # Nombre
        5: 'info_adicional',  # Apellido Paterno
        6: 'info_adicional',  # Apellido Materno
        7: 'info_adicional',  # Días Trabajados
    }
    
    @property
    def erp_codigo(self) -> str:
        return 'talana'
    
    @property
    def fila_headers(self) -> int:
        """Headers en la primera fila (índice 0)."""
        return 0
    
    @property
    def fila_datos_inicio(self) -> int:
        """Datos empiezan en fila 1 (índice 1)."""
        return 1
    
    def get_clasificacion_automatica(self, orden: int) -> str:
        """
        Retorna la clasificación automática para un header según su posición.
        
        Los primeros 8 headers de Talana SIEMPRE son datos del empleado,
        no conceptos monetarios. Esto reduce el ruido en la clasificación manual.
        
        Args:
            orden: Índice/posición del header (0-based)
        
        Returns:
            Categoría (str) o None si no aplica clasificación automática
        
        Examples:
            >>> parser.get_clasificacion_automatica(0)
            'info_adicional'  # Año
            >>> parser.get_clasificacion_automatica(3)
            'info_adicional'  # RUT (identificador por posición)
            >>> parser.get_clasificacion_automatica(10)
            None  # Header monetario, requiere clasificación manual
        """
        if orden < self.COLUMNAS_EMPLEADO_CANTIDAD:
            return self.CLASIFICACION_AUTO_EMPLEADO.get(orden, 'info_adicional')
        return None
    
    def es_header_empleado(self, orden: int) -> bool:
        """
        Verifica si un header (por posición) es dato de empleado.
        
        Args:
            orden: Índice del header
        
        Returns:
            True si es de las primeras 8 columnas (datos del empleado)
        """
        return orden < self.COLUMNAS_EMPLEADO_CANTIDAD
    
    def extraer_headers(self, archivo) -> List[str]:
        """
        Extrae los headers del Libro de Talana.
        
        Args:
            archivo: Archivo Excel
        
        Returns:
            Lista de headers (strings) - incluye duplicados con sufijos
        """
        try:
            # Intentar leer hoja "Libro"
            try:
                df = self.leer_excel(archivo, sheet_name='Libro', header=self.fila_headers)
            except ValueError:
                # Si no existe, usar primera hoja
                df = self.leer_excel(archivo, sheet_name=0, header=self.fila_headers)
                self.logger.info("Hoja 'Libro' no encontrada, usando primera hoja")
            
            # Analizar headers y detectar duplicados
            headers_info = self.analizar_headers_duplicados(df.columns)
            
            # Retornar lista de nombres de pandas (con .1, .2 si hay duplicados)
            headers = [info.pandas_name for info in headers_info]
            
            # Log de duplicados detectados
            duplicados = [info for info in headers_info if info.is_duplicate]
            if duplicados:
                originales_duplicados = set(info.original for info in duplicados)
                self.logger.warning(
                    f"Detectados {len(originales_duplicados)} headers duplicados: "
                    f"{', '.join(originales_duplicados)}"
                )
            
            self.logger.info(f"Extraídos {len(headers)} headers del libro Talana")
            return headers
            
        except Exception as e:
            self.logger.error(f"Error extrayendo headers de Talana: {e}")
            raise
    
    def parsear_empleado(
        self, 
        fila: Dict, 
        conceptos_clasificados: Dict, 
        headers_info: List = None,
        columnas_ordenadas: List = None
    ) -> Dict:
        """
        Parsea una fila de empleado del libro de Talana.
        
        Args:
            fila: Dict con los datos de la fila (columna -> valor)
            conceptos_clasificados: Dict de {pandas_name: ConceptoLibro}
            headers_info: Lista de HeaderInfo opcional (para logging)
            columnas_ordenadas: Lista de nombres de columnas en el orden del DataFrame
        
        Returns:
            Dict con datos del empleado:
            {
                'rut': '12345678-9',
                'nombre': 'Juan Pérez',
                'registros': [
                    {'concepto': ConceptoLibro, 'monto': Decimal(1500000)},
                    ...
                ]
            }
        """
        empleado_data = {
            'rut': '',
            'nombre': '',
            'registros': [],  # Lista de {concepto, monto}
        }
        
        # Categorías válidas para guardar en RegistroLibro
        CATEGORIAS_VALIDAS = {
            'haberes_imponibles',
            'haberes_no_imponibles',
            'descuentos_legales',
            'otros_descuentos',
            'aportes_patronales',
        }
        
        # Usar columnas ordenadas si se proporcionan, sino usar keys del dict
        columnas = columnas_ordenadas if columnas_ordenadas else list(fila.keys())
        
        # Debug: mostrar primeras columnas para verificar estructura
        if self.logger.isEnabledFor(10):  # DEBUG level
            self.logger.debug(f"Primeras 5 columnas: {columnas[:5]}")
        
        # Extraer RUT por posición (columna 3)
        if len(columnas) > self.COLUMNA_RUT_TRABAJADOR:
            rut_col = columnas[self.COLUMNA_RUT_TRABAJADOR]
            rut_valor = fila.get(rut_col)
            
            # Debug: mostrar valor de RUT encontrado
            if self.logger.isEnabledFor(10):  # DEBUG level
                self.logger.debug(f"Columna RUT '{rut_col}': valor='{rut_valor}'")
            
            if rut_valor and not pd.isna(rut_valor):
                empleado_data['rut'] = self.normalizar_rut(rut_valor)
        
        # Extraer nombre concatenando columnas 4, 5, 6 (Nombre, Apellido Paterno, Materno)
        nombre_partes = []
        for idx in [4, 5, 6]:
            if len(columnas) > idx:
                col = columnas[idx]
                valor = fila.get(col)
                if valor and not pd.isna(valor):
                    nombre_partes.append(self.limpiar_texto(str(valor)))
        
        if nombre_partes:
            empleado_data['nombre'] = ' '.join(nombre_partes)
        
        # Procesar cada columna de la fila
        for pandas_name, valor in fila.items():
            if pd.isna(valor) or valor == '':
                continue
            
            # Buscar concepto clasificado para este pandas_name
            concepto = conceptos_clasificados.get(pandas_name)
            
            if not concepto:
                # Header no clasificado, saltar
                continue
            
            categoria = concepto.categoria
            
            # Solo procesar categorías válidas (no info_adicional, no ignorar)
            if categoria not in CATEGORIAS_VALIDAS:
                continue
            
            # Normalizar monto
            monto = self.normalizar_monto(valor)
            
            # Solo guardar si monto > 0
            if monto > 0:
                empleado_data['registros'].append({
                    'concepto': concepto,
                    'monto': monto,
                })
        
        return empleado_data
    
    def procesar_libro(self, archivo, conceptos_clasificados: Dict) -> ProcessResult:
        """
        Procesa el libro completo de Talana.
        
        Args:
            archivo: Archivo Excel del libro
            conceptos_clasificados: Dict de {pandas_name: ConceptoLibro}
        
        Returns:
            ProcessResult con lista de empleados procesados
        """
        warnings = []
        
        try:
            # Leer archivo
            try:
                df = self.leer_excel(archivo, sheet_name='Libro', header=self.fila_headers)
            except ValueError:
                df = self.leer_excel(archivo, sheet_name=0, header=self.fila_headers)
                warnings.append("Hoja 'Libro' no encontrada, usando primera hoja")
            
            # Validar que hay datos
            if df.empty:
                return ProcessResult.fail("El archivo no contiene datos de empleados")
            
            # Analizar headers para detectar duplicados
            headers_info = self.analizar_headers_duplicados(df.columns)
            
            self.logger.info(f"Procesando {len(df)} filas del libro Talana")
            
            # Procesar cada fila
            empleados = []
            errores_fila = []
            
            # Obtener orden real de columnas del DataFrame
            columnas_ordenadas = list(df.columns)
            
            for idx, row in df.iterrows():
                try:
                    # Convertir fila a dict
                    fila_dict = row.to_dict()
                    
                    # Parsear empleado (pasamos columnas ordenadas)
                    empleado_data = self.parsear_empleado(
                        fila_dict, conceptos_clasificados, headers_info, columnas_ordenadas
                    )
                    
                    # Validar que tenga RUT (obligatorio)
                    if not empleado_data['rut']:
                        errores_fila.append(f"Fila {idx + 2}: No se encontró RUT")
                        continue
                    
                    empleados.append(empleado_data)
                    
                except Exception as e:
                    self.logger.error(f"Error procesando fila {idx + 2}: {e}")
                    errores_fila.append(f"Fila {idx + 2}: {str(e)}")
            
            # Agregar errores como warnings
            if errores_fila:
                warnings.extend(errores_fila[:10])  # Limitar a 10 primeros errores
                if len(errores_fila) > 10:
                    warnings.append(f"... y {len(errores_fila) - 10} errores más")
            
            # Validar que se procesó al menos un empleado
            if not empleados:
                return ProcessResult.fail(
                    "No se pudo procesar ningún empleado. "
                    "Verifique que los headers estén clasificados correctamente."
                )
            
            metadata = {
                'total_filas': len(df),
                'empleados_procesados': len(empleados),
                'errores': len(errores_fila),
                'headers_duplicados': len([h for h in headers_info if h.is_duplicate]),
            }
            
            self.logger.info(
                f"Libro Talana procesado: {len(empleados)} empleados de {len(df)} filas"
            )
            
            # Extraer headers (nombres pandas)
            headers = [info.pandas_name for info in headers_info]
            
            return ProcessResult.ok(
                data=empleados,
                headers=headers,
                headers_info=headers_info,
                warnings=warnings,
                metadata=metadata
            )
            
        except Exception as e:
            self.logger.error(f"Error procesando libro Talana: {e}")
            return ProcessResult.fail(f"Error al procesar archivo: {str(e)}")
