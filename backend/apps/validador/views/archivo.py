"""
ViewSets para Archivos.
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser

from ..models import ArchivoERP, ArchivoAnalista, Cierre
from ..serializers import (
    ArchivoERPSerializer,
    ArchivoERPUploadSerializer,
    ArchivoAnalistaSerializer,
    ArchivoAnalistaUploadSerializer,
)


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
        
        # Disparar procesamiento asíncrono con usuario para auditoría
        from ..tasks import procesar_archivo_erp
        procesar_archivo_erp.delay(archivo.id, usuario_id=self.request.user.id)
    
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
        archivo = serializer.save()
        
        # Disparar procesamiento asíncrono con usuario para auditoría
        from ..tasks import procesar_archivo_analista
        procesar_archivo_analista.delay(archivo.id, usuario_id=self.request.user.id)
    
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
