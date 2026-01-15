"""
Serializers para Conceptos y Mapeos.
"""

from rest_framework import serializers
from ..models import CategoriaConcepto, ConceptoCliente, ConceptoNovedades, ConceptoLibro


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


class ConceptoNovedadesSerializer(serializers.ModelSerializer):
    """
    Serializer para ConceptoNovedades.
    
    Representa headers extraídos del archivo de novedades,
    mapeados a ConceptoLibro (headers del libro ERP).
    """
    
    concepto_libro_info = serializers.SerializerMethodField()
    mapeado_por_nombre = serializers.CharField(
        source='mapeado_por.get_full_name',
        read_only=True,
        allow_null=True
    )
    categoria = serializers.CharField(
        read_only=True,
        allow_null=True
    )
    
    class Meta:
        model = ConceptoNovedades
        fields = [
            'id', 'cliente', 'erp',
            'header_original', 'header_normalizado',
            'concepto_libro', 'concepto_libro_info',
            'categoria',  # delegado desde concepto_libro
            'orden', 'activo',
            'mapeado_por', 'mapeado_por_nombre',
            'fecha_mapeo'
        ]
        read_only_fields = ['mapeado_por', 'fecha_mapeo', 'categoria']
    
    def get_concepto_libro_info(self, obj):
        """Info del ConceptoLibro asociado."""
        if not obj.concepto_libro:
            return None
        return {
            'id': obj.concepto_libro.id,
            'header_original': obj.concepto_libro.header_original,
            'categoria': obj.concepto_libro.categoria,
            'categoria_display': obj.concepto_libro.get_categoria_display(),
        }


class ConceptoNovedadesSinMapearSerializer(serializers.ModelSerializer):
    """Serializer para listar conceptos de novedades sin mapear."""
    
    class Meta:
        model = ConceptoNovedades
        fields = ['id', 'header_original', 'orden']
