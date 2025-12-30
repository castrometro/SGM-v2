"""
Serializers para Consolidación y Resúmenes.
"""

from rest_framework import serializers
from ..models import ResumenConsolidado, ResumenCategoria, ResumenMovimientos


class ResumenConsolidadoSerializer(serializers.ModelSerializer):
    """Serializer para resumen consolidado por concepto."""
    
    categoria_nombre = serializers.CharField(source='categoria.nombre', read_only=True)
    concepto_nombre = serializers.CharField(source='concepto.nombre_erp', read_only=True)
    
    class Meta:
        model = ResumenConsolidado
        fields = [
            'id', 'cierre',
            'categoria', 'categoria_nombre',
            'concepto', 'concepto_nombre',
            'total_monto', 'cantidad_empleados',
            'monto_promedio', 'monto_minimo', 'monto_maximo',
        ]


class ResumenCategoriaSerializer(serializers.ModelSerializer):
    """Serializer para resumen por categoría."""
    
    categoria_nombre = serializers.CharField(source='categoria.nombre', read_only=True)
    
    class Meta:
        model = ResumenCategoria
        fields = [
            'id', 'cierre',
            'categoria', 'categoria_nombre',
            'total_monto', 'cantidad_conceptos', 'cantidad_empleados_afectados',
        ]


class ResumenMovimientosSerializer(serializers.ModelSerializer):
    """Serializer para resumen de movimientos."""
    
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)
    
    class Meta:
        model = ResumenMovimientos
        fields = [
            'id', 'cierre',
            'tipo', 'tipo_display',
            'cantidad', 'total_dias', 'empleados',
        ]


class DashboardLibroSerializer(serializers.Serializer):
    """Serializer para dashboard del Libro de Remuneraciones."""
    
    periodo = serializers.CharField()
    cliente_nombre = serializers.CharField()
    
    total_empleados = serializers.IntegerField()
    total_haberes = serializers.DecimalField(max_digits=18, decimal_places=2)
    total_descuentos = serializers.DecimalField(max_digits=18, decimal_places=2)
    total_liquido = serializers.DecimalField(max_digits=18, decimal_places=2)
    
    por_categoria = serializers.ListField()
    top_conceptos = serializers.ListField()


class DashboardMovimientosSerializer(serializers.Serializer):
    """Serializer para dashboard de Movimientos."""
    
    periodo = serializers.CharField()
    cliente_nombre = serializers.CharField()
    
    total_altas = serializers.IntegerField()
    total_bajas = serializers.IntegerField()
    total_licencias = serializers.IntegerField()
    total_vacaciones = serializers.IntegerField()
    
    movimientos = serializers.ListField()
