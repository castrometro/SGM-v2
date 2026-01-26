"""
Serializers para Discrepancias.
"""

from rest_framework import serializers
from ..models import Discrepancia


class DiscrepanciaSerializer(serializers.ModelSerializer):
    """Serializer para discrepancias."""
    
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)
    origen_display = serializers.CharField(source='get_origen_display', read_only=True)
    
    class Meta:
        model = Discrepancia
        fields = [
            'id', 'cierre', 'tipo', 'tipo_display',
            'origen', 'origen_display',
            'rut_empleado', 'nombre_empleado',
            'nombre_item', 'nombre_item_novedades',
            'monto_erp', 'monto_cliente', 'diferencia',
            'tipo_movimiento', 'detalle_movimiento',
            'resuelta', 'fecha_resolucion',
            'descripcion', 'fecha_deteccion',
        ]


class DiscrepanciaResumenSerializer(serializers.Serializer):
    """Serializer para resumen de discrepancias."""
    
    total = serializers.IntegerField()
    resueltas = serializers.IntegerField()
    pendientes = serializers.IntegerField()
    por_tipo = serializers.DictField()
    por_origen = serializers.DictField()
