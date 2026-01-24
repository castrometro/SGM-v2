"""
ViewSets para Archivos.
"""

from rest_framework import viewsets, status, serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser

from ..models import ArchivoERP, ArchivoAnalista, Cierre, ConceptoNovedades, ConceptoLibro
from ..serializers import (
    ArchivoERPSerializer,
    ArchivoERPUploadSerializer,
    ArchivoAnalistaSerializer,
    ArchivoAnalistaUploadSerializer,
)
from ..constants import TipoArchivoERP, EstadoArchivoLibro, EstadoArchivoNovedades
from ..tasks import extraer_headers_libro, procesar_archivo_erp, procesar_archivo_analista, extraer_headers_novedades
from shared.audit import audit_create, audit_delete


class ArchivoERPViewSet(viewsets.ModelViewSet):
    """ViewSet para archivos ERP."""
    
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    
    def get_queryset(self):
        queryset = ArchivoERP.objects.select_related('cierre', 'subido_por').all()
        
        cierre_id = self.request.query_params.get('cierre')
        if cierre_id:
            queryset = queryset.filter(cierre_id=cierre_id)
        
        # Por defecto, solo versiones actuales
        solo_actuales = self.request.query_params.get('solo_actuales', 'true')
        if solo_actuales.lower() == 'true':
            queryset = queryset.filter(es_version_actual=True)
        
        return queryset.order_by('-fecha_subida')
    
    def get_serializer_class(self):
        if self.action == 'create':
            return ArchivoERPUploadSerializer
        return ArchivoERPSerializer
    
    def perform_create(self, serializer):
        archivo = serializer.save()
        audit_create(self.request, archivo)  # Registrar en auditoría
        
        # Disparar tarea según el tipo de archivo
        if archivo.tipo == TipoArchivoERP.LIBRO_REMUNERACIONES:
            # El libro necesita extracción de headers y clasificación primero
            extraer_headers_libro.delay(archivo.id, usuario_id=self.request.user.id)
        else:
            # Otros archivos se procesan directamente
            procesar_archivo_erp.delay(archivo.id, usuario_id=self.request.user.id)
    
    def perform_destroy(self, instance):
        """Registrar eliminación en auditoría."""
        audit_delete(self.request, instance)
        instance.delete()
    
    @action(detail=False, methods=['get'])
    def por_cierre(self, request):
        """Obtener archivos agrupados por tipo para un cierre."""
        cierre_id = request.query_params.get('cierre_id')
        if not cierre_id:
            return Response(
                {'error': 'cierre_id es requerido'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        archivos = ArchivoERP.objects.filter(
            cierre_id=cierre_id,
            es_version_actual=True
        )
        
        return Response({
            'libro_remuneraciones': ArchivoERPSerializer(
                archivos.filter(tipo='libro_remuneraciones').first()
            ).data if archivos.filter(tipo='libro_remuneraciones').exists() else None,
            
            'movimientos_mes': ArchivoERPSerializer(
                archivos.filter(tipo='movimientos_mes').first()
            ).data if archivos.filter(tipo='movimientos_mes').exists() else None,
        })


class ArchivoAnalistaViewSet(viewsets.ModelViewSet):
    """ViewSet para archivos del Analista."""
    
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    
    def get_queryset(self):
        queryset = ArchivoAnalista.objects.select_related('cierre', 'subido_por').all()
        
        cierre_id = self.request.query_params.get('cierre')
        if cierre_id:
            queryset = queryset.filter(cierre_id=cierre_id)
        
        solo_actuales = self.request.query_params.get('solo_actuales', 'true')
        if solo_actuales.lower() == 'true':
            queryset = queryset.filter(es_version_actual=True)
        
        return queryset.order_by('-fecha_subida')
    
    def get_serializer_class(self):
        if self.action == 'create':
            return ArchivoAnalistaUploadSerializer
        return ArchivoAnalistaSerializer
    
    def perform_create(self, serializer):
        """
        Crea archivo del analista con validaciones específicas por tipo.
        
        Para NOVEDADES:
            - Valida que el libro esté procesado
            - Dispara extracción de headers (no procesamiento directo)
        
        Para otros tipos:
            - Dispara procesamiento directo
        """
        # Obtener datos antes de guardar para validar
        cierre = serializer.validated_data.get('cierre')
        tipo = serializer.validated_data.get('tipo')
        
        # Validación: si es novedades, el libro debe estar procesado
        if tipo == 'novedades':
            libro = ArchivoERP.objects.filter(
                cierre=cierre,
                tipo=TipoArchivoERP.LIBRO_REMUNERACIONES,
                es_version_actual=True
            ).first()
            
            if not libro:
                raise serializers.ValidationError({
                    'tipo': 'No se puede subir novedades: primero debe subir el Libro de Remuneraciones'
                })
            
            if libro.estado != EstadoArchivoLibro.PROCESADO:
                raise serializers.ValidationError({
                    'tipo': f'No se puede subir novedades: el Libro debe estar procesado (estado actual: {libro.estado})'
                })
        
        archivo = serializer.save()
        audit_create(self.request, archivo)
        
        # Disparar tarea según tipo
        if tipo == 'novedades':
            # Novedades: extraer headers primero (como el libro)
            extraer_headers_novedades.delay(archivo.id, usuario_id=self.request.user.id)
        else:
            # Otros archivos: procesar directamente
            procesar_archivo_analista.delay(archivo.id, usuario_id=self.request.user.id)
    
    def perform_destroy(self, instance):
        """Registrar eliminación en auditoría."""
        audit_delete(self.request, instance)
        instance.delete()
    
    @action(detail=True, methods=['get'])
    def headers(self, request, pk=None):
        """
        Obtiene los headers/conceptos extraídos del archivo de novedades.
        
        Retorna:
            - conceptos: Lista de ConceptoNovedades con estado de mapeo
            - conceptos_libro: ConceptosLibro del cliente disponibles para mapear
            - resumen: Conteos de conceptos mapeados/pendientes
        """
        archivo = self.get_object()
        
        if archivo.tipo != 'novedades':
            return Response(
                {'error': 'Este endpoint solo aplica para archivos de novedades'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Obtener cliente y ERP
        cliente = archivo.cierre.cliente
        config_erp = cliente.configuraciones_erp.filter(activo=True).select_related('erp').first()
        if not config_erp:
            return Response(
                {'error': 'Cliente no tiene ERP activo configurado'},
                status=status.HTTP_400_BAD_REQUEST
            )
        erp = config_erp.erp
        
        # Obtener ConceptoNovedades del cliente+ERP
        conceptos = ConceptoNovedades.objects.filter(
            cliente=cliente,
            erp=erp,
            activo=True
        ).select_related('concepto_libro').order_by('orden')
        
        conceptos_data = []
        for concepto in conceptos:
            conceptos_data.append({
                'id': concepto.id,
                'header_original': concepto.header_original,
                'orden': concepto.orden,
                'mapeado': concepto.mapeado,  # True si tiene concepto_libro O sin_asignacion
                'sin_asignacion': concepto.sin_asignacion,
                'concepto_libro': {
                    'id': concepto.concepto_libro.id,
                    'header_original': concepto.concepto_libro.header_original,
                    'categoria': concepto.concepto_libro.categoria,
                    'categoria_display': concepto.concepto_libro.get_categoria_display(),
                } if concepto.concepto_libro else None
            })
        
        # Obtener conceptos del libro disponibles para mapear
        conceptos_libro = ConceptoLibro.objects.filter(
            cliente=cliente,
            erp=erp,
            activo=True,
            categoria__isnull=False  # Solo clasificados
        ).exclude(
            categoria='ignorar'
        ).order_by('categoria', 'orden', 'header_original')
        
        conceptos_libro_data = [
            {
                'id': c.id,
                'header_original': c.header_original,
                'categoria': c.categoria,
                'categoria_display': c.get_categoria_display(),
            }
            for c in conceptos_libro
        ]
        
        # Resumen - mapeado = tiene concepto_libro O sin_asignacion
        total = conceptos.count()
        con_concepto_libro = conceptos.filter(concepto_libro__isnull=False).count()
        con_sin_asignacion = conceptos.filter(sin_asignacion=True, concepto_libro__isnull=True).count()
        mapeados = con_concepto_libro + con_sin_asignacion
        
        return Response({
            'archivo_id': archivo.id,
            'estado': archivo.estado,
            'conceptos': conceptos_data,
            'conceptos_libro': conceptos_libro_data,
            'resumen': {
                'total': total,
                'mapeados': mapeados,
                'con_concepto_libro': con_concepto_libro,
                'sin_asignacion': con_sin_asignacion,
                'pendientes': total - mapeados,
                'progreso': round(mapeados / total * 100, 1) if total > 0 else 0,
            }
        })
    
    @action(detail=True, methods=['post'])
    def extraer_headers(self, request, pk=None):
        """Re-extrae los headers del archivo de novedades."""
        archivo = self.get_object()
        
        if archivo.tipo != 'novedades':
            return Response(
                {'error': 'Este endpoint solo aplica para archivos de novedades'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if archivo.estado not in [EstadoArchivoNovedades.SUBIDO, EstadoArchivoNovedades.ERROR]:
            return Response(
                {'error': f'No se puede re-extraer en estado {archivo.estado}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        extraer_headers_novedades.delay(archivo.id, usuario_id=request.user.id)
        
        return Response({
            'mensaje': 'Extracción de headers iniciada',
            'archivo_id': archivo.id,
        })
    
    @action(detail=True, methods=['post'])
    def procesar(self, request, pk=None):
        """
        Procesa el archivo de novedades creando RegistroNovedades.
        
        Prerequisitos:
            - Archivo debe estar en estado LISTO (todos los headers mapeados/sin_asignacion)
        
        Dispara la tarea procesar_archivo_analista que:
            - Lee el archivo Excel/CSV
            - Crea RegistroNovedades por cada (RUT, item, monto)
            - Ignora items marcados como sin_asignacion
        
        Rate limit: 10/hour por usuario (scope: procesamiento)
        """
        archivo = self.get_object()
        
        if archivo.tipo != 'novedades':
            return Response(
                {'error': 'Este endpoint solo aplica para archivos de novedades'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if archivo.estado != EstadoArchivoNovedades.LISTO:
            return Response(
                {'error': f'El archivo debe estar en estado LISTO para procesar (estado actual: {archivo.estado})'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Disparar tarea de procesamiento
        procesar_archivo_analista.delay(archivo.id, usuario_id=request.user.id)
        
        return Response({
            'mensaje': 'Procesamiento iniciado',
            'archivo_id': archivo.id,
        })
    
    @action(detail=False, methods=['get'])
    def por_cierre(self, request):
        """Obtener archivos agrupados por tipo para un cierre."""
        cierre_id = request.query_params.get('cierre_id')
        if not cierre_id:
            return Response(
                {'error': 'cierre_id es requerido'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        archivos = ArchivoAnalista.objects.filter(
            cierre_id=cierre_id,
            es_version_actual=True
        )
        
        resultado = {}
        for tipo in ['novedades', 'asistencias', 'finiquitos', 'ingresos']:
            archivo = archivos.filter(tipo=tipo).first()
            resultado[tipo] = ArchivoAnalistaSerializer(archivo).data if archivo else None
        
        return Response(resultado)
