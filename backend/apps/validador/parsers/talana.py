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
    """
    
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
    
    def extraer_headers(self, archivo) -> List[str]:
        """
        Extrae los headers del Libro de Talana.
        
        Args:
            archivo: Archivo Excel
        
        Returns:
            Lista de headers (strings)
        """
        try:
            # Intentar leer hoja "Libro"
            try:
                df = self.leer_excel(archivo, sheet_name='Libro', header=self.fila_headers)
            except ValueError:
                # Si no existe, usar primera hoja
                df = self.leer_excel(archivo, sheet_name=0, header=self.fila_headers)
                self.logger.info("Hoja 'Libro' no encontrada, usando primera hoja")
            
            # Obtener headers (nombres de columnas)
            headers = [str(col).strip() for col in df.columns if not str(col).startswith('Unnamed')]
            
            self.logger.info(f"Extraídos {len(headers)} headers del libro Talana")
            return headers
            
        except Exception as e:
            self.logger.error(f"Error extrayendo headers de Talana: {e}")
            raise
    
    def parsear_empleado(self, fila: Dict, conceptos_clasificados: Dict) -> Dict:
        """
        Parsea una fila de empleado del libro de Talana.
        
        Args:
            fila: Dict con los datos de la fila (columna -> valor)
            conceptos_clasificados: Dict de {header: ConceptoLibro}
        
        Returns:
            Dict con datos del empleado estructurados
        """
        empleado_data = {
            'rut': '',
            'nombre': '',
            'cargo': '',
            'centro_costo': '',
            'area': '',
            'fecha_ingreso': None,
            'datos_json': {},
        }
        
        # Diccionario para acumular datos por categoría
        categorias_data = {}
        
        # Procesar cada columna de la fila
        for header, valor in fila.items():
            if pd.isna(valor) or valor == '':
                continue
            
            # Buscar concepto clasificado para este header
            concepto = conceptos_clasificados.get(header)
            
            if not concepto:
                # Header no clasificado, saltar
                continue
            
            categoria = concepto.categoria
            
            # Manejar campos especiales
            if categoria == 'identificador' or concepto.es_identificador:
                if not empleado_data['rut']:
                    empleado_data['rut'] = self.normalizar_rut(valor)
                continue
            
            if categoria == 'ignorar':
                continue
            
            if categoria == 'info_adicional':
                # Detectar campos conocidos
                header_lower = header.lower()
                if 'nombre' in header_lower and not empleado_data['nombre']:
                    empleado_data['nombre'] = self.limpiar_texto(valor)
                elif 'cargo' in header_lower:
                    empleado_data['cargo'] = self.limpiar_texto(valor)
                elif 'centro' in header_lower and 'costo' in header_lower:
                    empleado_data['centro_costo'] = self.limpiar_texto(valor)
                elif 'area' in header_lower:
                    empleado_data['area'] = self.limpiar_texto(valor)
                continue
            
            # Para categorías monetarias, acumular montos
            if categoria in ['haberes_imponibles', 'haberes_no_imponibles',
                            'descuentos_legales', 'otros_descuentos', 'aportes_patronales']:
                
                monto = self.normalizar_monto(valor)
                
                if categoria not in categorias_data:
                    categorias_data[categoria] = {}
                
                categorias_data[categoria][header] = monto
        
        # Calcular totales por categoría
        for categoria, conceptos in categorias_data.items():
            total = sum(conceptos.values())
            conceptos['total'] = total
            empleado_data['datos_json'][categoria] = conceptos
        
        # Calcular totales finales
        totales = self.calcular_totales_por_categoria(empleado_data['datos_json'])
        empleado_data.update(totales)
        
        return empleado_data
    
    def procesar_libro(self, archivo, conceptos_clasificados: Dict) -> ProcessResult:
        """
        Procesa el libro completo de Talana.
        
        Args:
            archivo: Archivo Excel del libro
            conceptos_clasificados: Dict de {header: ConceptoLibro}
        
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
            
            self.logger.info(f"Procesando {len(df)} filas del libro Talana")
            
            # Procesar cada fila
            empleados = []
            errores_fila = []
            
            for idx, row in df.iterrows():
                try:
                    # Convertir fila a dict
                    fila_dict = row.to_dict()
                    
                    # Parsear empleado
                    empleado_data = self.parsear_empleado(fila_dict, conceptos_clasificados)
                    
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
            }
            
            self.logger.info(
                f"Libro Talana procesado: {len(empleados)} empleados de {len(df)} filas"
            )
            
            # Extraer headers
            headers = [str(col).strip() for col in df.columns if not str(col).startswith('Unnamed')]
            
            return ProcessResult.ok(
                data=empleados,
                headers=headers,
                warnings=warnings,
                metadata=metadata
            )
            
        except Exception as e:
            self.logger.error(f"Error procesando libro Talana: {e}")
            return ProcessResult.fail(f"Error al procesar archivo: {str(e)}")
