"""
Serializers para Cierre.
"""

from rest_framework import serializers
from ..models import Cierre


class CierreListSerializer(serializers.ModelSerializer):
    """Serializer para listar cierres."""
    
    cliente_nombre = serializers.CharField(source='cliente.nombre_display', read_only=True)
    analista_nombre = serializers.CharField(source='analista.get_full_name', read_only=True)
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)
    progreso_discrepancias = serializers.SerializerMethodField()
    progreso_incidencias = serializers.SerializerMethodField()
    
    class Meta:
        model = Cierre
        fields = [
            'id', 'cliente', 'cliente_nombre', 'periodo',
            'estado', 'estado_display', 'analista', 'analista_nombre',
            'total_discrepancias', 'discrepancias_resueltas',
            'total_incidencias', 'incidencias_aprobadas',
            'progreso_discrepancias', 'progreso_incidencias',
            'es_primer_cierre', 'fecha_creacion', 'fecha_finalizacion',
        ]
    
    def get_progreso_discrepancias(self, obj):
        if obj.total_discrepancias == 0:
            return 100
        return round((obj.discrepancias_resueltas / obj.total_discrepancias) * 100)
    
    def get_progreso_incidencias(self, obj):
        if obj.total_incidencias == 0:
            return 100
        return round((obj.incidencias_aprobadas / obj.total_incidencias) * 100)


class CierreDetailSerializer(serializers.ModelSerializer):
    """Serializer detallado de un cierre."""
    
    cliente_nombre = serializers.CharField(source='cliente.nombre_display', read_only=True)
    analista_nombre = serializers.CharField(source='analista.get_full_name', read_only=True)
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)
    archivos_erp_count = serializers.SerializerMethodField()
    archivos_analista_count = serializers.SerializerMethodField()
    puede_consolidar = serializers.BooleanField(read_only=True)
    puede_finalizar = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Cierre
        fields = [
            'id', 'cliente', 'cliente_nombre', 'periodo',
            'estado', 'estado_display', 'analista', 'analista_nombre',
            'total_discrepancias', 'discrepancias_resueltas',
            'total_incidencias', 'incidencias_aprobadas',
            'es_primer_cierre', 'requiere_clasificacion', 'requiere_mapeo',
            'archivos_erp_count', 'archivos_analista_count',
            'puede_consolidar', 'puede_finalizar',
            'fecha_creacion', 'fecha_actualizacion',
            'fecha_consolidacion', 'fecha_finalizacion',
            'observaciones',
        ]
    
    def get_archivos_erp_count(self, obj):
        return obj.archivos_erp.filter(es_version_actual=True).count()
    
    def get_archivos_analista_count(self, obj):
        return obj.archivos_analista.filter(es_version_actual=True).count()


class CierreCreateSerializer(serializers.ModelSerializer):
    """Serializer para crear un cierre."""
    
    class Meta:
        model = Cierre
        fields = ['id', 'cliente', 'periodo', 'analista', 'observaciones']
        read_only_fields = ['id']
    
    def validate(self, data):
        # Verificar que no exista cierre para el mismo cliente/periodo
        if Cierre.objects.filter(
            cliente=data['cliente'],
            periodo=data['periodo']
        ).exists():
            raise serializers.ValidationError({
                'periodo': f"Ya existe un cierre para este cliente en el período {data['periodo']}"
            })
        return data
    
    def create(self, validated_data):
        # Determinar si es primer cierre del cliente
        cliente = validated_data['cliente']
        es_primer_cierre = not Cierre.objects.filter(
            cliente=cliente,
            estado='finalizado'
        ).exists()
        
        validated_data['es_primer_cierre'] = es_primer_cierre
        return super().create(validated_data)
