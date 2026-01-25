"""
ArchivoService - Lógica de negocio para Archivos.

Centraliza:
- Subida de archivos
- Versionado
- Procesamiento
- Validaciones
"""

import os
from django.utils import timezone
from django.db import transaction
from typing import Optional, Dict, Any, List

from .base import BaseService, ServiceResult
from ..models import ArchivoERP, ArchivoAnalista, Cierre


class ArchivoService(BaseService):
    """
    Servicio para gestión de Archivos (ERP y Analista).
    
    Maneja:
    - Subida con versionado automático
    - Validaciones de tipo y formato
    - Procesamiento asíncrono
    """
    
    TIPOS_ERP = ['libro_remuneraciones', 'movimientos_mes']
    TIPOS_ANALISTA = ['novedades', 'asistencias', 'finiquitos', 'ingresos']
    
    EXTENSIONES_PERMITIDAS = ['.xlsx', '.xls', '.csv']
    MAX_FILE_SIZE_MB = 50
    
    # Magic bytes para validación de tipo de archivo
    MAGIC_BYTES = {
        '.xlsx': [b'PK\x03\x04'],  # ZIP (OOXML)
        '.xls': [b'\xd0\xcf\x11\xe0'],  # OLE Compound Document
        '.csv': None,  # CSV es texto, no tiene magic bytes específicos
    }
    
    @classmethod
    def validar_archivo(cls, archivo, tipo: str, es_erp: bool = True) -> Optional[str]:
        """
        Validar archivo antes de subir.
        
        Capas de seguridad:
        1. Validar tipo de archivo
        2. Validar extensión
        3. Validar magic bytes (prevenir rename attacks)
        4. Validar tamaño
        5. Sanitizar nombre de archivo
        
        Args:
            archivo: Archivo subido (UploadedFile)
            tipo: Tipo de archivo
            es_erp: Si es archivo ERP o Analista
            
        Returns:
            None si es válido, mensaje de error si no
        """
        import re
        
        # Layer 1: Validar tipo
        tipos_validos = cls.TIPOS_ERP if es_erp else cls.TIPOS_ANALISTA
        if tipo not in tipos_validos:
            return f'Tipo inválido. Tipos válidos: {tipos_validos}'
        
        # Layer 2: Validar extensión
        _, ext = os.path.splitext(archivo.name.lower())
        if ext not in cls.EXTENSIONES_PERMITIDAS:
            return f'Extensión no permitida. Extensiones válidas: {cls.EXTENSIONES_PERMITIDAS}'
        
        # Layer 3: Validar magic bytes (prevenir rename attacks)
        expected_magic = cls.MAGIC_BYTES.get(ext)
        if expected_magic:
            try:
                header = archivo.read(16)
                archivo.seek(0)  # Reset file pointer
                
                if not any(header.startswith(magic) for magic in expected_magic):
                    return f'El contenido del archivo no coincide con la extensión {ext}'
            except Exception:
                return 'Error al validar el tipo de archivo'
        
        # Layer 4: Validar tamaño
        max_size = cls.MAX_FILE_SIZE_MB * 1024 * 1024
        if archivo.size > max_size:
            return f'Archivo muy grande. Máximo: {cls.MAX_FILE_SIZE_MB}MB'
        
        # Layer 5: Sanitizar nombre de archivo (prevenir path traversal)
        if not re.match(r'^[\w\-. ]+$', archivo.name):
            return 'Nombre de archivo contiene caracteres no permitidos'
        
        return None
    
    @classmethod
    def subir_archivo_erp(
        cls,
        cierre: Cierre,
        archivo,
        tipo: str,
        user,
        metadata: Dict[str, Any] = None
    ) -> ServiceResult[ArchivoERP]:
        """
        Subir archivo ERP con versionado automático.
        
        Si ya existe un archivo del mismo tipo para el cierre,
        el anterior se marca como no actual.
        """
        logger = cls.get_logger()
        
        # Validar archivo
        error = cls.validar_archivo(archivo, tipo, es_erp=True)
        if error:
            return ServiceResult.fail(error)
        
        try:
            with transaction.atomic():
                # Marcar versiones anteriores como no actuales
                ArchivoERP.objects.filter(
                    cierre=cierre,
                    tipo=tipo,
                    es_version_actual=True
                ).update(es_version_actual=False)
                
                # Calcular número de versión
                version = ArchivoERP.objects.filter(
                    cierre=cierre,
                    tipo=tipo
                ).count() + 1
                
                # Crear nuevo archivo
                nuevo_archivo = ArchivoERP.objects.create(
                    cierre=cierre,
                    tipo=tipo,
                    archivo=archivo,
                    nombre_original=archivo.name,
                    subido_por=user,
                    es_version_actual=True,
                    version=version,
                    metadata=metadata or {}
                )
                
                cls.log_action(
                    action='subir_archivo_erp',
                    entity_type='archivo_erp',
                    entity_id=nuevo_archivo.id,
                    user=user,
                    extra={
                        'cierre_id': cierre.id,
                        'tipo': tipo,
                        'version': version,
                        'nombre': archivo.name,
                    }
                )
                
                logger.info(
                    f"Archivo ERP '{tipo}' v{version} subido para cierre {cierre.id}"
                )
                
                # Disparar procesamiento asíncrono
                cls._disparar_procesamiento_erp(nuevo_archivo)
                
                return ServiceResult.ok(nuevo_archivo)
                
        except Exception as e:
            logger.error(f"Error al subir archivo ERP: {str(e)}")
            return ServiceResult.fail(f'Error al subir archivo: {str(e)}')
    
    @classmethod
    def subir_archivo_analista(
        cls,
        cierre: Cierre,
        archivo,
        tipo: str,
        user,
        metadata: Dict[str, Any] = None
    ) -> ServiceResult[ArchivoAnalista]:
        """
        Subir archivo de Analista con versionado automático.
        """
        logger = cls.get_logger()
        
        # Validar archivo
        error = cls.validar_archivo(archivo, tipo, es_erp=False)
        if error:
            return ServiceResult.fail(error)
        
        try:
            with transaction.atomic():
                # Marcar versiones anteriores como no actuales
                ArchivoAnalista.objects.filter(
                    cierre=cierre,
                    tipo=tipo,
                    es_version_actual=True
                ).update(es_version_actual=False)
                
                # Calcular número de versión
                version = ArchivoAnalista.objects.filter(
                    cierre=cierre,
                    tipo=tipo
                ).count() + 1
                
                # Crear nuevo archivo
                nuevo_archivo = ArchivoAnalista.objects.create(
                    cierre=cierre,
                    tipo=tipo,
                    archivo=archivo,
                    nombre_original=archivo.name,
                    subido_por=user,
                    es_version_actual=True,
                    version=version,
                    metadata=metadata or {}
                )
                
                cls.log_action(
                    action='subir_archivo_analista',
                    entity_type='archivo_analista',
                    entity_id=nuevo_archivo.id,
                    user=user,
                    extra={
                        'cierre_id': cierre.id,
                        'tipo': tipo,
                        'version': version,
                        'nombre': archivo.name,
                    }
                )
                
                logger.info(
                    f"Archivo Analista '{tipo}' v{version} subido para cierre {cierre.id}"
                )
                
                # Disparar procesamiento asíncrono
                cls._disparar_procesamiento_analista(nuevo_archivo)
                
                return ServiceResult.ok(nuevo_archivo)
                
        except Exception as e:
            logger.error(f"Error al subir archivo Analista: {str(e)}")
            return ServiceResult.fail(f'Error al subir archivo: {str(e)}')
    
    @classmethod
    def eliminar_archivo(
        cls,
        archivo,
        user,
        es_erp: bool = True
    ) -> ServiceResult[bool]:
        """
        Eliminar archivo (soft delete marcando como no actual).
        
        Si hay versiones anteriores, la más reciente se reactiva.
        """
        logger = cls.get_logger()
        modelo = ArchivoERP if es_erp else ArchivoAnalista
        tipo_str = 'ERP' if es_erp else 'Analista'
        
        try:
            with transaction.atomic():
                cierre = archivo.cierre
                tipo = archivo.tipo
                
                # Marcar como eliminado
                archivo.es_version_actual = False
                archivo.eliminado = True
                archivo.fecha_eliminacion = timezone.now()
                archivo.eliminado_por = user
                archivo.save()
                
                # Reactivar versión anterior si existe
                version_anterior = modelo.objects.filter(
                    cierre=cierre,
                    tipo=tipo,
                    eliminado=False
                ).exclude(id=archivo.id).order_by('-version').first()
                
                if version_anterior:
                    version_anterior.es_version_actual = True
                    version_anterior.save()
                    logger.info(
                        f"Reactivada versión {version_anterior.version} de archivo {tipo}"
                    )
                
                cls.log_action(
                    action='eliminar_archivo',
                    entity_type=f'archivo_{tipo_str.lower()}',
                    entity_id=archivo.id,
                    user=user,
                    extra={
                        'cierre_id': cierre.id,
                        'tipo': tipo,
                        'version_reactivada': version_anterior.version if version_anterior else None,
                    }
                )
                
                logger.info(f"Archivo {tipo_str} {archivo.id} eliminado")
                
                return ServiceResult.ok(True)
                
        except Exception as e:
            logger.error(f"Error al eliminar archivo: {str(e)}")
            return ServiceResult.fail(f'Error al eliminar: {str(e)}')
    
    @classmethod
    def obtener_archivos_cierre(cls, cierre: Cierre) -> Dict[str, Any]:
        """
        Obtener todos los archivos de un cierre organizados por tipo.
        """
        archivos_erp = ArchivoERP.objects.filter(
            cierre=cierre,
            es_version_actual=True,
            eliminado=False
        )
        
        archivos_analista = ArchivoAnalista.objects.filter(
            cierre=cierre,
            es_version_actual=True,
            eliminado=False
        )
        
        return {
            'erp': {
                'libro_remuneraciones': cls._archivo_to_dict(
                    archivos_erp.filter(tipo='libro_remuneraciones').first()
                ),
                'movimientos_mes': cls._archivo_to_dict(
                    archivos_erp.filter(tipo='movimientos_mes').first()
                ),
            },
            'analista': {
                tipo: cls._archivo_to_dict(
                    archivos_analista.filter(tipo=tipo).first()
                )
                for tipo in cls.TIPOS_ANALISTA
            },
            'resumen': {
                'total_erp': archivos_erp.count(),
                'total_analista': archivos_analista.count(),
                'completo': archivos_erp.count() >= 1,  # Mínimo libro remuneraciones
            }
        }
    
    @classmethod
    def _archivo_to_dict(cls, archivo) -> Optional[Dict[str, Any]]:
        """Convertir archivo a diccionario."""
        if not archivo:
            return None
        
        return {
            'id': archivo.id,
            'nombre': archivo.nombre_original,
            'tipo': archivo.tipo,
            'version': archivo.version,
            'estado': archivo.estado,
            'fecha_subida': archivo.fecha_subida,
            'subido_por': archivo.subido_por.get_full_name() if archivo.subido_por else None,
            'total_filas': getattr(archivo, 'total_filas', None),
            'filas_procesadas': getattr(archivo, 'filas_procesadas', None),
        }
    
    @classmethod
    def _disparar_procesamiento_erp(cls, archivo: ArchivoERP):
        """Disparar task de procesamiento para archivo ERP."""
        try:
            from ..tasks import procesar_archivo_erp
            procesar_archivo_erp.delay(archivo.id)
        except ImportError:
            cls.get_logger().warning(
                f"Task procesar_archivo_erp no disponible para archivo {archivo.id}"
            )
    
    @classmethod
    def _disparar_procesamiento_analista(cls, archivo: ArchivoAnalista):
        """Disparar task de procesamiento para archivo Analista."""
        try:
            from ..tasks import procesar_archivo_analista
            procesar_archivo_analista.delay(archivo.id)
        except ImportError:
            cls.get_logger().warning(
                f"Task procesar_archivo_analista no disponible para archivo {archivo.id}"
            )
    
    @classmethod
    def marcar_no_aplica(
        cls,
        cierre: Cierre,
        tipo: str,
        user=None
    ) -> ServiceResult[ArchivoAnalista]:
        """
        Marcar un tipo de archivo analista como "No Aplica" para este mes.
        
        Crea un registro de ArchivoAnalista con estado NO_APLICA para indicar
        que este tipo de archivo no tiene datos este mes.
        
        Args:
            cierre: Cierre al que pertenece
            tipo: Tipo de archivo (novedades, asistencias, finiquitos, ingresos)
            user: Usuario que marca
            
        Returns:
            ServiceResult con el archivo creado/actualizado
        """
        from ..constants import EstadoCierre, EstadoArchivoNovedades
        from .cierre_service import CierreService
        
        logger = cls.get_logger()
        
        # Validar tipo
        if tipo not in cls.TIPOS_ANALISTA:
            return ServiceResult.fail(
                f'Tipo de archivo inválido. Tipos válidos: {cls.TIPOS_ANALISTA}'
            )
        
        # Validar estado del cierre
        if cierre.estado != EstadoCierre.CARGA_ARCHIVOS:
            return ServiceResult.fail(
                'Solo se puede marcar "No Aplica" en estado CARGA_ARCHIVOS'
            )
        
        # Verificar si ya existe un archivo de este tipo
        archivo_existente = ArchivoAnalista.objects.filter(
            cierre=cierre,
            tipo=tipo,
            es_version_actual=True
        ).first()
        
        if archivo_existente:
            # Si ya existe y está procesado, no permitir
            if archivo_existente.estado == EstadoArchivoNovedades.PROCESADO:
                return ServiceResult.fail(
                    f'Ya existe un archivo {tipo} procesado. Elimínelo primero.'
                )
            # Si ya está como NO_APLICA, retornar éxito
            if archivo_existente.estado == EstadoArchivoNovedades.NO_APLICA:
                return ServiceResult.ok(archivo_existente)
        
        try:
            with transaction.atomic():
                # Desactivar versiones anteriores si existen
                ArchivoAnalista.objects.filter(
                    cierre=cierre,
                    tipo=tipo,
                    es_version_actual=True
                ).update(es_version_actual=False)
                
                # Crear registro con estado NO_APLICA
                archivo = ArchivoAnalista.objects.create(
                    cierre=cierre,
                    tipo=tipo,
                    estado=EstadoArchivoNovedades.NO_APLICA,
                    nombre_original=f'{tipo}_no_aplica.txt',
                    subido_por=user,
                    es_version_actual=True,
                    version=(archivo_existente.version + 1) if archivo_existente else 1,
                )
                
                cls.log_action(
                    action='marcar_no_aplica',
                    entity_type='archivo_analista',
                    entity_id=archivo.id,
                    user=user,
                    extra={
                        'cierre_id': cierre.id,
                        'tipo': tipo,
                    }
                )
                
                logger.info(
                    f"Archivo analista {tipo} marcado como NO_APLICA para cierre {cierre.id}"
                )
                
                # NOTA: La transición a ARCHIVOS_LISTOS es manual (botón "Continuar")
                
                return ServiceResult.ok(archivo)
                
        except Exception as e:
            logger.error(f"Error al marcar no_aplica: {str(e)}")
            return ServiceResult.fail(f'Error: {str(e)}')
    
    @classmethod
    def desmarcar_no_aplica(
        cls,
        cierre: Cierre,
        tipo: str,
        user=None
    ) -> ServiceResult[None]:
        """
        Eliminar el marcado "No Aplica" de un tipo de archivo.
        
        Permite volver a subir un archivo de este tipo.
        
        Args:
            cierre: Cierre al que pertenece
            tipo: Tipo de archivo
            user: Usuario que desmarca
            
        Returns:
            ServiceResult indicando éxito o error
        """
        from ..constants import EstadoCierre, EstadoArchivoNovedades
        from .cierre_service import CierreService
        
        logger = cls.get_logger()
        
        # Validar estado del cierre
        if cierre.estado not in [EstadoCierre.CARGA_ARCHIVOS, EstadoCierre.ARCHIVOS_LISTOS]:
            return ServiceResult.fail(
                'Solo se puede desmarcar en estados CARGA_ARCHIVOS o ARCHIVOS_LISTOS'
            )
        
        archivo = ArchivoAnalista.objects.filter(
            cierre=cierre,
            tipo=tipo,
            es_version_actual=True,
            estado=EstadoArchivoNovedades.NO_APLICA
        ).first()
        
        if not archivo:
            return ServiceResult.fail(
                f'No hay archivo {tipo} marcado como NO_APLICA'
            )
        
        try:
            with transaction.atomic():
                archivo.es_version_actual = False
                archivo.save()
                
                cls.log_action(
                    action='desmarcar_no_aplica',
                    entity_type='archivo_analista',
                    entity_id=archivo.id,
                    user=user,
                    extra={
                        'cierre_id': cierre.id,
                        'tipo': tipo,
                    }
                )
                
                logger.info(
                    f"Desmarcado NO_APLICA para {tipo} en cierre {cierre.id}"
                )
                
                # Si estaba en ARCHIVOS_LISTOS, volver a CARGA_ARCHIVOS
                if cierre.estado == EstadoCierre.ARCHIVOS_LISTOS:
                    CierreService.volver_a_carga_archivos(
                        cierre, user, 
                        motivo=f'Se desmarcó NO_APLICA del archivo {tipo}'
                    )
                
                return ServiceResult.ok(None)
                
        except Exception as e:
            logger.error(f"Error al desmarcar no_aplica: {str(e)}")
            return ServiceResult.fail(f'Error: {str(e)}')
