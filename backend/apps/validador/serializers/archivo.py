"""
Serializers para Archivos (ERP y Analista).
"""

from rest_framework import serializers
from ..models import ArchivoERP, ArchivoAnalista


class ArchivoERPSerializer(serializers.ModelSerializer):
    """Serializer para archivos ERP."""
    
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)
    subido_por_nombre = serializers.CharField(source='subido_por.get_full_name', read_only=True)
    
    class Meta:
        model = ArchivoERP
        fields = [
            'id', 'cierre', 'tipo', 'tipo_display',
            'archivo', 'nombre_original',
            'estado', 'estado_display',
            'filas_procesadas', 'errores_procesamiento',
            'error_mensaje',  # Mensaje de error específico del libro
            'hojas_encontradas',
            'headers_total', 'headers_clasificados',  # Campos específicos del libro
            'version', 'es_version_actual',
            'subido_por', 'subido_por_nombre',
            'fecha_subida', 'fecha_procesamiento',
        ]
        read_only_fields = [
            'estado', 'filas_procesadas', 'errores_procesamiento',
            'error_mensaje', 'hojas_encontradas',
            'headers_total', 'headers_clasificados',
            'version', 'es_version_actual',
            'fecha_subida', 'fecha_procesamiento',
        ]


class ArchivoERPUploadSerializer(serializers.ModelSerializer):
    """Serializer para subir archivo ERP."""
    
    class Meta:
        model = ArchivoERP
        fields = ['cierre', 'tipo', 'archivo']
    
    def validate_archivo(self, value):
        from apps.validador.services import ArchivoService
        
        # Validar usando el servicio centralizado
        error = ArchivoService.validar_archivo(
            value, 
            tipo=self.initial_data.get('tipo', ''),
            es_erp=True
        )
        if error:
            raise serializers.ValidationError(error)
        return value
    
    def create(self, validated_data):
        validated_data['nombre_original'] = validated_data['archivo'].name
        validated_data['subido_por'] = self.context['request'].user
        return super().create(validated_data)


class ArchivoAnalistaSerializer(serializers.ModelSerializer):
    """Serializer para archivos del Analista."""
    
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)
    subido_por_nombre = serializers.CharField(source='subido_por.get_full_name', read_only=True)
    
    class Meta:
        model = ArchivoAnalista
        fields = [
            'id', 'cierre', 'tipo', 'tipo_display',
            'archivo', 'nombre_original',
            'estado', 'estado_display',
            'filas_procesadas', 'errores_procesamiento',
            'version', 'es_version_actual',
            'subido_por', 'subido_por_nombre',
            'fecha_subida', 'fecha_procesamiento',
        ]
        read_only_fields = [
            'estado', 'filas_procesadas', 'errores_procesamiento',
            'version', 'es_version_actual',
            'fecha_subida', 'fecha_procesamiento',
        ]


class ArchivoAnalistaUploadSerializer(serializers.ModelSerializer):
    """Serializer para subir archivo del Analista."""
    
    class Meta:
        model = ArchivoAnalista
        fields = ['cierre', 'tipo', 'archivo']
    
    def validate_archivo(self, value):
        from apps.validador.services import ArchivoService
        
        # Validar usando el servicio centralizado
        error = ArchivoService.validar_archivo(
            value,
            tipo=self.initial_data.get('tipo', ''),
            es_erp=False
        )
        if error:
            raise serializers.ValidationError(error)
        return value
    
    def create(self, validated_data):
        validated_data['nombre_original'] = validated_data['archivo'].name
        validated_data['subido_por'] = self.context['request'].user
        return super().create(validated_data)
