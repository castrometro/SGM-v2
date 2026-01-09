"""
Views para gestión del Libro de Remuneraciones.
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404

from apps.validador.models import ArchivoERP, ConceptoLibro, EmpleadoLibro
from apps.validador.serializers import (
    ConceptoLibroSerializer,
    ConceptoLibroListSerializer,
    ClasificacionMasivaSerializer,
    EmpleadoLibroSerializer,
    EmpleadoLibroListSerializer,
    HeadersResponseSerializer,
    ProcesamientoResponseSerializer,
    ProgresoLibroSerializer,
)
from apps.validador.services import LibroService
from apps.validador.constants import EstadoArchivoLibro
from apps.validador.tasks import (
    extraer_headers_libro,
    procesar_libro_remuneraciones,
    obtener_progreso_libro,
)


class LibroViewSet(viewsets.ViewSet):
    """
    ViewSet para operaciones del Libro de Remuneraciones.
    
    Endpoints:
    - GET    /archivos-erp/{id}/libro/headers/     - Obtener headers y clasificación
    - POST   /archivos-erp/{id}/libro/extraer/     - Extraer headers (async)
    - POST   /archivos-erp/{id}/libro/clasificar/  - Clasificar conceptos
    - POST   /archivos-erp/{id}/libro/procesar/    - Procesar libro completo (async)
    - GET    /archivos-erp/{id}/libro/progreso/    - Obtener progreso del procesamiento
    - GET    /archivos-erp/{id}/libro/empleados/   - Listar empleados procesados
    """
    
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['get'], url_path='(?P<archivo_id>[^/.]+)/headers')
    def headers(self, request, archivo_id=None):
        """
        Obtiene los headers del libro y su estado de clasificación.
        
        GET /api/v1/validador/libro/{archivo_id}/headers/
        
        Response:
            {
                "headers_total": 45,
                "headers_clasificados": 42,
                "progreso": 93,
                "headers": ["RUT", "NOMBRE", "SUELDO BASE", ...],
                "conceptos": [
                    {
                        "id": 1,
                        "header_original": "SUELDO BASE",
                        "categoria": "haberes_imponibles",
                        "categoria_display": "Haberes Imponibles",
                        "es_identificador": false,
                        "orden": 2,
                        "clasificado": true
                    },
                    ...
                ]
            }
        """
        archivo_erp = get_object_or_404(ArchivoERP, id=archivo_id)
        
        # Obtener conceptos
        cierre = archivo_erp.cierre
        config_erp = cierre.cliente.configuraciones_erp.filter(activo=True).first()
        
        if not config_erp:
            return Response(
                {'error': 'Cliente no tiene ERP configurado'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        conceptos = ConceptoLibro.objects.filter(
            cliente=cierre.cliente,
            erp=config_erp.erp,
            activo=True
        ).order_by('orden')
        
        headers = [c.header_original for c in conceptos]
        
        data = {
            'headers_total': archivo_erp.headers_total,
            'headers_clasificados': archivo_erp.headers_clasificados,
            'progreso': archivo_erp.progreso_clasificacion,
            'headers': headers,
            'conceptos': ConceptoLibroListSerializer(conceptos, many=True).data
        }
        
        return Response(data)
    
    @action(detail=False, methods=['post'], url_path='(?P<archivo_id>[^/.]+)/extraer')
    def extraer(self, request, archivo_id=None):
        """
        Inicia la extracción de headers del libro (tarea asíncrona).
        
        POST /api/v1/validador/libro/{archivo_id}/extraer/
        
        Response:
            {
                "task_id": "abc123...",
                "message": "Extracción iniciada"
            }
        """
        archivo_erp = get_object_or_404(ArchivoERP, id=archivo_id)
        
        # Validar que es libro
        if archivo_erp.tipo != 'libro_remuneraciones':
            return Response(
                {'error': 'El archivo no es de tipo libro_remuneraciones'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Iniciar tarea
        task = extraer_headers_libro.delay(archivo_erp.id)
        
        return Response({
            'task_id': task.id,
            'message': 'Extracción de headers iniciada'
        }, status=status.HTTP_202_ACCEPTED)
    
    @action(detail=False, methods=['post'], url_path='(?P<archivo_id>[^/.]+)/clasificar')
    def clasificar(self, request, archivo_id=None):
        """
        Clasifica los conceptos del libro.
        
        POST /api/v1/validador/libro/{archivo_id}/clasificar/
        
        Body:
            {
                "clasificaciones": [
                    {
                        "header": "SUELDO BASE",
                        "categoria": "haberes_imponibles",
                        "es_identificador": false
                    },
                    ...
                ]
            }
        
        Response:
            {
                "clasificados": 3,
                "total": 45,
                "progreso": 93,
                "listo_para_procesar": false
            }
        """
        archivo_erp = get_object_or_404(ArchivoERP, id=archivo_id)
        
        serializer = ClasificacionMasivaSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        # Clasificar
        result = LibroService.clasificar_conceptos(
            archivo_erp,
            serializer.validated_data['clasificaciones'],
            request.user
        )
        
        if result.success:
            return Response(result.data)
        else:
            return Response(
                {'error': result.error},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['post'], url_path='(?P<archivo_id>[^/.]+)/procesar')
    def procesar(self, request, archivo_id=None):
        """
        Inicia el procesamiento completo del libro (tarea asíncrona).
        
        POST /api/v1/validador/libro/{archivo_id}/procesar/
        
        Response:
            {
                "task_id": "xyz789...",
                "message": "Procesamiento iniciado"
            }
        """
        archivo_erp = get_object_or_404(ArchivoERP, id=archivo_id)
        
        # Validar que todos los headers están clasificados
        if not archivo_erp.todos_headers_clasificados:
            return Response(
                {
                    'error': f'Faltan {archivo_erp.headers_total - archivo_erp.headers_clasificados} headers por clasificar'
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Iniciar tarea
        task = procesar_libro_remuneraciones.delay(archivo_erp.id)
        
        return Response({
            'task_id': task.id,
            'message': 'Procesamiento del libro iniciado'
        }, status=status.HTTP_202_ACCEPTED)
    
    @action(detail=False, methods=['get'], url_path='(?P<archivo_id>[^/.]+)/progreso')
    def progreso(self, request, archivo_id=None):
        """
        Obtiene el progreso del procesamiento del libro.
        
        GET /api/v1/validador/libro/{archivo_id}/progreso/
        
        Response:
            {
                "estado": "procesando",  // "procesando" | "completado" | "error"
                "progreso": 50,          // 0-100
                "empleados_procesados": 1234,
                "mensaje": "Procesando empleados..."
            }
        """
        archivo_erp = get_object_or_404(ArchivoERP, id=archivo_id)
        
        # Obtener progreso desde cache
        progreso_data = obtener_progreso_libro(archivo_erp.id)
        
        if progreso_data:
            return Response(progreso_data)
        
        # Si no hay progreso en cache, retornar estado del archivo
        return Response({
            'estado': archivo_erp.estado,
            'progreso': 100 if archivo_erp.estado == EstadoArchivoLibro.PROCESADO else 0,
            'empleados_procesados': archivo_erp.empleados_procesados,
            'mensaje': f'Estado: {archivo_erp.get_estado_display()}'
        })
    
    @action(detail=False, methods=['get'], url_path='(?P<archivo_id>[^/.]+)/empleados')
    def empleados(self, request, archivo_id=None):
        """
        Lista los empleados procesados del libro.
        
        GET /api/v1/validador/libro/{archivo_id}/empleados/
        
        Query params:
            - page: Página (default: 1)
            - page_size: Tamaño de página (default: 100)
        
        Response:
            {
                "count": 2456,
                "next": "...",
                "previous": null,
                "results": [
                    {
                        "id": 1,
                        "rut": "12345678-9",
                        "nombre": "Juan Pérez",
                        "cargo": "Analista",
                        "total_haberes_imponibles": 1500000.00,
                        "total_descuentos_legales": 180000.00,
                        "total_liquido": 1320000.00
                    },
                    ...
                ]
            }
        """
        archivo_erp = get_object_or_404(ArchivoERP, id=archivo_id)
        
        empleados = EmpleadoLibro.objects.filter(
            archivo_erp=archivo_erp
        ).order_by('nombre', 'rut')
        
        # Paginación
        page = self.paginate_queryset(empleados)
        if page is not None:
            serializer = EmpleadoLibroListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = EmpleadoLibroListSerializer(empleados, many=True)
        return Response(serializer.data)
