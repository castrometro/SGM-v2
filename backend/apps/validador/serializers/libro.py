"""
Serializers para Libro de Remuneraciones.
"""

from rest_framework import serializers
from apps.validador.models import ConceptoLibro, EmpleadoLibro
from apps.validador.constants import CategoriaConceptoLibro


class ConceptoLibroSerializer(serializers.ModelSerializer):
    """Serializer para ConceptoLibro."""
    
    categoria_display = serializers.CharField(
        source='get_categoria_display',
        read_only=True
    )
    clasificado = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = ConceptoLibro
        fields = [
            'id',
            'cliente',
            'erp',
            'header_original',
            'header_normalizado',
            'categoria',
            'categoria_display',
            'es_identificador',
            'orden',
            'activo',
            'clasificado',
            'creado_por',
            'fecha_creacion',
            'fecha_actualizacion',
        ]
        read_only_fields = [
            'id',
            'header_normalizado',
            'fecha_creacion',
            'fecha_actualizacion',
        ]


class ConceptoLibroListSerializer(serializers.ModelSerializer):
    """Serializer simplificado para listado de conceptos."""
    
    categoria_display = serializers.CharField(
        source='get_categoria_display',
        read_only=True
    )
    
    class Meta:
        model = ConceptoLibro
        fields = [
            'id',
            'header_original',
            'categoria',
            'categoria_display',
            'es_identificador',
            'orden',
            'clasificado',
        ]


class ConceptoLibroClasificarSerializer(serializers.Serializer):
    """
    Serializer para clasificar un concepto del libro.
    
    Uso:
        {
            "header": "SUELDO BASE",
            "categoria": "haberes_imponibles",
            "es_identificador": false
        }
    """
    header = serializers.CharField(max_length=200)
    categoria = serializers.ChoiceField(
        choices=CategoriaConceptoLibro.CHOICES,
        allow_null=True,
        required=False
    )
    es_identificador = serializers.BooleanField(default=False)
    
    def validate_categoria(self, value):
        """Validar que la categoría sea válida."""
        if value and not CategoriaConceptoLibro.es_valido(value):
            raise serializers.ValidationError(
                f"Categoría inválida: {value}"
            )
        return value


class ClasificacionMasivaSerializer(serializers.Serializer):
    """
    Serializer para clasificación masiva de conceptos.
    
    Uso:
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
    """
    clasificaciones = serializers.ListField(
        child=ConceptoLibroClasificarSerializer(),
        min_length=1
    )


class EmpleadoLibroSerializer(serializers.ModelSerializer):
    """Serializer completo para EmpleadoLibro."""
    
    class Meta:
        model = EmpleadoLibro
        fields = [
            'id',
            'cierre',
            'archivo_erp',
            'rut',
            'nombre',
            'cargo',
            'centro_costo',
            'area',
            'fecha_ingreso',
            'datos_json',
            'total_haberes_imponibles',
            'total_haberes_no_imponibles',
            'total_descuentos_legales',
            'total_otros_descuentos',
            'total_aportes_patronales',
            'total_liquido',
            'fecha_creacion',
        ]
        read_only_fields = ['id', 'fecha_creacion']


class EmpleadoLibroListSerializer(serializers.ModelSerializer):
    """Serializer simplificado para listado de empleados del libro."""
    
    class Meta:
        model = EmpleadoLibro
        fields = [
            'id',
            'rut',
            'nombre',
            'cargo',
            'total_haberes_imponibles',
            'total_descuentos_legales',
            'total_liquido',
        ]


class EmpleadoLibroResumenSerializer(serializers.Serializer):
    """Serializer para resumen de empleados procesados."""
    
    total_empleados = serializers.IntegerField()
    total_haberes = serializers.DecimalField(max_digits=15, decimal_places=2)
    total_descuentos = serializers.DecimalField(max_digits=15, decimal_places=2)
    total_liquido = serializers.DecimalField(max_digits=15, decimal_places=2)
    promedio_liquido = serializers.DecimalField(max_digits=15, decimal_places=2)


class HeadersResponseSerializer(serializers.Serializer):
    """Serializer para respuesta de extracción de headers."""
    
    headers_total = serializers.IntegerField()
    headers_clasificados = serializers.IntegerField()
    progreso = serializers.IntegerField()
    headers = serializers.ListField(child=serializers.CharField())
    conceptos = ConceptoLibroListSerializer(many=True)


class ProcesamientoResponseSerializer(serializers.Serializer):
    """Serializer para respuesta de procesamiento del libro."""
    
    empleados_procesados = serializers.IntegerField()
    total_filas = serializers.IntegerField()
    errores = serializers.IntegerField()
    warnings = serializers.ListField(child=serializers.CharField())
    task_id = serializers.CharField(required=False)


class ProgresoLibroSerializer(serializers.Serializer):
    """Serializer para estado de progreso del procesamiento."""
    
    estado = serializers.ChoiceField(
        choices=[
            ('procesando', 'Procesando'),
            ('completado', 'Completado'),
            ('error', 'Error')
        ]
    )
    progreso = serializers.IntegerField(min_value=0, max_value=100)
    empleados_procesados = serializers.IntegerField(required=False)
    mensaje = serializers.CharField()
