"""
Serializers para Conceptos y Mapeos.
"""

from rest_framework import serializers
from ..models import CategoriaConcepto, ConceptoCliente, MapeoItemNovedades


class CategoriaConceptoSerializer(serializers.ModelSerializer):
    """Serializer para categorías de conceptos."""
    
    class Meta:
        model = CategoriaConcepto
        fields = [
            'codigo', 'nombre', 'descripcion',
            'se_compara', 'se_incluye_en_incidencias', 'orden'
        ]


class ConceptoClienteSerializer(serializers.ModelSerializer):
    """Serializer para conceptos de cliente."""
    
    categoria_nombre = serializers.CharField(
        source='categoria.nombre',
        read_only=True,
        allow_null=True
    )
    clasificado_por_nombre = serializers.CharField(
        source='clasificado_por.get_full_name',
        read_only=True,
        allow_null=True
    )
    
    class Meta:
        model = ConceptoCliente
        fields = [
            'id', 'cliente', 'nombre_erp',
            'categoria', 'categoria_nombre',
            'clasificado', 'clasificado_por', 'clasificado_por_nombre',
            'fecha_clasificacion',
            'ignorar_en_comparacion', 'multiplicador',
            'se_compara',
        ]
        read_only_fields = [
            'clasificado', 'clasificado_por', 'fecha_clasificacion'
        ]


class ConceptoClienteClasificarSerializer(serializers.Serializer):
    """Serializer para clasificar múltiples conceptos."""
    
    conceptos = serializers.ListField(
        child=serializers.DictField(
            child=serializers.CharField()
        )
    )
    
    def validate_conceptos(self, value):
        """
        Espera formato:
        [
            {"id": 1, "categoria": "haberes_imponibles"},
            {"id": 2, "categoria": "descuentos_legales"},
        ]
        """
        for item in value:
            if 'id' not in item or 'categoria' not in item:
                raise serializers.ValidationError(
                    "Cada concepto debe tener 'id' y 'categoria'"
                )
            
            # Validar que la categoría existe
            if not CategoriaConcepto.objects.filter(codigo=item['categoria']).exists():
                raise serializers.ValidationError(
                    f"Categoría '{item['categoria']}' no existe"
                )
        
        return value


class ConceptoSinClasificarSerializer(serializers.ModelSerializer):
    """Serializer para listar conceptos sin clasificar."""
    
    class Meta:
        model = ConceptoCliente
        fields = ['id', 'nombre_erp']


class MapeoItemNovedadesSerializer(serializers.ModelSerializer):
    """Serializer para mapeos de items."""
    
    concepto_erp_nombre = serializers.CharField(
        source='concepto_erp.nombre_erp',
        read_only=True
    )
    mapeado_por_nombre = serializers.CharField(
        source='mapeado_por.get_full_name',
        read_only=True,
        allow_null=True
    )
    
    class Meta:
        model = MapeoItemNovedades
        fields = [
            'id', 'cliente', 'nombre_novedades',
            'concepto_erp', 'concepto_erp_nombre',
            'mapeado_por', 'mapeado_por_nombre',
            'fecha_mapeo', 'notas'
        ]
        read_only_fields = ['mapeado_por', 'fecha_mapeo']


class MapeoItemCrearSerializer(serializers.Serializer):
    """Serializer para crear múltiples mapeos."""
    
    mapeos = serializers.ListField(
        child=serializers.DictField()
    )
    
    def validate_mapeos(self, value):
        """
        Espera formato:
        [
            {"nombre_novedades": "Bono Colación", "concepto_erp_id": 5},
            {"nombre_novedades": "Gratificación", "concepto_erp_id": 12},
        ]
        """
        for item in value:
            if 'nombre_novedades' not in item or 'concepto_erp_id' not in item:
                raise serializers.ValidationError(
                    "Cada mapeo debe tener 'nombre_novedades' y 'concepto_erp_id'"
                )
        return value


class ItemSinMapearSerializer(serializers.Serializer):
    """Serializer para listar items sin mapear."""
    
    nombre_novedades = serializers.CharField()
    cantidad_registros = serializers.IntegerField()
