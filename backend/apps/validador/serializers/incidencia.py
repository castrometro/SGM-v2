"""
Serializers para Incidencias.
"""

from rest_framework import serializers
from ..models import Incidencia, ComentarioIncidencia


class ComentarioIncidenciaSerializer(serializers.ModelSerializer):
    """Serializer para comentarios de incidencias."""
    
    autor_nombre = serializers.CharField(source='autor.get_full_name', read_only=True)
    autor_rol = serializers.CharField(source='autor.rol', read_only=True)
    
    class Meta:
        model = ComentarioIncidencia
        fields = [
            'id', 'incidencia',
            'autor', 'autor_nombre', 'autor_rol',
            'contenido',
            'archivo_adjunto', 'nombre_adjunto',
            'fecha_creacion', 'fecha_edicion', 'editado',
        ]
        read_only_fields = [
            'autor', 'fecha_creacion', 'fecha_edicion', 'editado'
        ]


class ComentarioCrearSerializer(serializers.ModelSerializer):
    """Serializer para crear comentarios."""
    
    class Meta:
        model = ComentarioIncidencia
        fields = ['incidencia', 'contenido', 'archivo_adjunto']
    
    def create(self, validated_data):
        validated_data['autor'] = self.context['request'].user
        if validated_data.get('archivo_adjunto'):
            validated_data['nombre_adjunto'] = validated_data['archivo_adjunto'].name
        return super().create(validated_data)


class IncidenciaSerializer(serializers.ModelSerializer):
    """Serializer para incidencias."""
    
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)
    concepto_nombre = serializers.CharField(source='concepto.nombre_erp', read_only=True)
    categoria_nombre = serializers.CharField(source='categoria.nombre', read_only=True)
    resuelto_por_nombre = serializers.CharField(
        source='resuelto_por.get_full_name',
        read_only=True,
        allow_null=True
    )
    comentarios_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Incidencia
        fields = [
            'id', 'cierre',
            'concepto', 'concepto_nombre',
            'categoria', 'categoria_nombre',
            'monto_mes_anterior', 'monto_mes_actual',
            'diferencia_absoluta', 'variacion_porcentual',
            'es_variacion_positiva',
            'estado', 'estado_display',
            'resuelto_por', 'resuelto_por_nombre',
            'fecha_resolucion', 'motivo_resolucion',
            'fecha_deteccion', 'comentarios_count',
        ]
    
    def get_comentarios_count(self, obj):
        return obj.comentarios.count()


class IncidenciaDetailSerializer(IncidenciaSerializer):
    """Serializer detallado de incidencia con comentarios."""
    
    comentarios = ComentarioIncidenciaSerializer(many=True, read_only=True)
    
    class Meta(IncidenciaSerializer.Meta):
        fields = IncidenciaSerializer.Meta.fields + ['comentarios']


class IncidenciaResolverSerializer(serializers.Serializer):
    """Serializer para aprobar/rechazar incidencia."""
    
    accion = serializers.ChoiceField(choices=['aprobar', 'rechazar'])
    motivo = serializers.CharField(required=False, allow_blank=True)
    
    def validate(self, data):
        if data['accion'] == 'rechazar' and not data.get('motivo'):
            raise serializers.ValidationError({
                'motivo': 'El motivo es requerido al rechazar una incidencia'
            })
        return data


class IncidenciaResumenSerializer(serializers.Serializer):
    """Serializer para resumen de incidencias."""
    
    total = serializers.IntegerField()
    aprobadas = serializers.IntegerField()
    rechazadas = serializers.IntegerField()
    pendientes = serializers.IntegerField()
    por_categoria = serializers.ListField()
