"""
Admin del app Validador.
"""

from django.contrib import admin
from .models import (
    Cierre,
    ArchivoERP,
    ArchivoAnalista,
    CategoriaConcepto,
    ConceptoCliente,
    ConceptoLibro,
    ConceptoNovedades,
    EmpleadoCierre,
    EmpleadoLibro,
    RegistroLibro,
    RegistroNovedades,
    Discrepancia,
    Incidencia,
    ComentarioIncidencia,
    ResumenConsolidado,
    ResumenCategoria,
)


@admin.register(CategoriaConcepto)
class CategoriaConceptoAdmin(admin.ModelAdmin):
    list_display = ['codigo', 'nombre', 'se_compara', 'se_incluye_en_incidencias', 'orden']
    list_editable = ['orden', 'se_compara', 'se_incluye_en_incidencias']
    ordering = ['orden']


@admin.register(Cierre)
class CierreAdmin(admin.ModelAdmin):
    list_display = [
        'cliente', 'periodo', 'estado', 'analista',
        'total_discrepancias', 'total_incidencias', 'fecha_creacion'
    ]
    list_filter = ['estado', 'periodo', 'cliente']
    search_fields = ['cliente__nombre_legal', 'periodo']
    raw_id_fields = ['cliente', 'analista']
    readonly_fields = ['fecha_creacion', 'fecha_actualizacion']
    
    fieldsets = (
        (None, {
            'fields': ('cliente', 'periodo', 'estado', 'analista')
        }),
        ('Contadores', {
            'fields': (
                'total_discrepancias', 'discrepancias_resueltas',
                'total_incidencias', 'incidencias_aprobadas'
            )
        }),
        ('Flags', {
            'fields': (
                'es_primer_cierre', 'requiere_clasificacion', 'requiere_mapeo'
            )
        }),
        ('Timestamps', {
            'fields': (
                'fecha_creacion', 'fecha_actualizacion',
                'fecha_consolidacion', 'fecha_finalizacion'
            )
        }),
    )


class ArchivoERPInline(admin.TabularInline):
    model = ArchivoERP
    extra = 0
    readonly_fields = ['fecha_subida', 'subido_por', 'estado']


class ArchivoAnalistaInline(admin.TabularInline):
    model = ArchivoAnalista
    extra = 0
    readonly_fields = ['fecha_subida', 'subido_por', 'estado']


@admin.register(ArchivoERP)
class ArchivoERPAdmin(admin.ModelAdmin):
    list_display = ['nombre_original', 'cierre', 'tipo', 'estado', 'version', 'fecha_subida']
    list_filter = ['tipo', 'estado', 'es_version_actual']
    search_fields = ['nombre_original', 'cierre__cliente__nombre_legal']
    raw_id_fields = ['cierre', 'subido_por']


@admin.register(ArchivoAnalista)
class ArchivoAnalistaAdmin(admin.ModelAdmin):
    list_display = ['nombre_original', 'cierre', 'tipo', 'estado', 'version', 'fecha_subida']
    list_filter = ['tipo', 'estado', 'es_version_actual']
    search_fields = ['nombre_original', 'cierre__cliente__nombre_legal']
    raw_id_fields = ['cierre', 'subido_por']


@admin.register(ConceptoCliente)
class ConceptoClienteAdmin(admin.ModelAdmin):
    list_display = [
        'nombre_erp', 'cliente', 'categoria', 'clasificado',
        'ignorar_en_comparacion', 'multiplicador'
    ]
    list_filter = ['cliente', 'categoria', 'clasificado']
    search_fields = ['nombre_erp', 'cliente__nombre_legal']
    raw_id_fields = ['cliente', 'clasificado_por']
    list_editable = ['categoria', 'ignorar_en_comparacion']


@admin.register(ConceptoLibro)
class ConceptoLibroAdmin(admin.ModelAdmin):
    list_display = [
        'header_original', 'cliente', 'erp', 'categoria',
        'orden', 'activo'
    ]
    list_filter = ['cliente', 'erp', 'categoria', 'activo']
    search_fields = ['header_original', 'header_normalizado', 'cliente__nombre_legal']
    raw_id_fields = ['cliente', 'erp', 'creado_por']
    list_editable = ['categoria', 'orden']
    readonly_fields = ['header_normalizado', 'fecha_creacion', 'fecha_actualizacion']
    
    fieldsets = (
        (None, {
            'fields': ('cliente', 'erp', 'header_original', 'header_normalizado')
        }),
        ('Clasificación', {
            'fields': ('categoria', 'orden')
        }),
        ('Estado', {
            'fields': ('activo', 'creado_por')
        }),
        ('Timestamps', {
            'fields': ('fecha_creacion', 'fecha_actualizacion'),
            'classes': ('collapse',)
        }),
    )


@admin.register(ConceptoNovedades)
class ConceptoNovedadesAdmin(admin.ModelAdmin):
    list_display = ['header_original_truncado', 'concepto_libro', 'cliente', 'erp', 'activo', 'fecha_mapeo']
    list_filter = ['cliente', 'erp', 'activo']
    search_fields = ['header_original', 'concepto_libro__header_original']
    raw_id_fields = ['cliente', 'erp', 'concepto_libro', 'creado_por', 'mapeado_por']
    readonly_fields = ['header_normalizado', 'fecha_creacion', 'fecha_actualizacion']
    
    def header_original_truncado(self, obj):
        return obj.header_original[:50] + '...' if len(obj.header_original) > 50 else obj.header_original
    header_original_truncado.short_description = 'Header Original'
    readonly_fields = ['fecha_creacion']


@admin.register(EmpleadoCierre)
class EmpleadoCierreAdmin(admin.ModelAdmin):
    list_display = ['rut', 'nombre', 'cierre', 'total_haberes', 'total_descuentos', 'liquido']
    list_filter = ['cierre__cliente', 'cierre__periodo']
    search_fields = ['rut', 'nombre']
    raw_id_fields = ['cierre']


@admin.register(EmpleadoLibro)
class EmpleadoLibroAdmin(admin.ModelAdmin):
    list_display = ['rut', 'nombre', 'cierre', 'archivo_erp', 'fecha_creacion']
    list_filter = ['cierre__cliente', 'cierre__periodo', 'archivo_erp__tipo']
    search_fields = ['rut', 'nombre']
    raw_id_fields = ['cierre', 'archivo_erp']
    readonly_fields = ['fecha_creacion']


@admin.register(RegistroLibro)
class RegistroLibroAdmin(admin.ModelAdmin):
    list_display = ['empleado', 'concepto', 'monto', 'cierre']
    list_filter = ['cierre__cliente', 'cierre__periodo', 'concepto__categoria']
    search_fields = ['empleado__rut', 'empleado__nombre', 'concepto__nombre']
    raw_id_fields = ['cierre', 'empleado', 'concepto']


@admin.register(RegistroNovedades)
class RegistroNovedadesAdmin(admin.ModelAdmin):
    list_display = [
        'rut_empleado', 'nombre_empleado', 'nombre_item', 
        'monto_formateado', 'concepto_novedades', 'cierre_info'
    ]
    list_filter = [
        'cierre__cliente', 
        'cierre__periodo',
        ('concepto_novedades', admin.RelatedOnlyFieldListFilter),
    ]
    search_fields = ['rut_empleado', 'nombre_empleado', 'nombre_item']
    raw_id_fields = ['cierre', 'concepto_novedades']
    list_per_page = 50
    list_select_related = ['cierre', 'cierre__cliente', 'concepto_novedades']
    
    @admin.display(description='Monto')
    def monto_formateado(self, obj):
        return f"${obj.monto:,.0f}"
    
    @admin.display(description='Cierre')
    def cierre_info(self, obj):
        return f"{obj.cierre.cliente.razon_social} - {obj.cierre.periodo}"


@admin.register(Discrepancia)
class DiscrepanciaAdmin(admin.ModelAdmin):
    list_display = [
        'cierre', 'tipo', 'rut_empleado', 'concepto',
        'diferencia', 'resuelta', 'fecha_deteccion'
    ]
    list_filter = ['tipo', 'origen', 'resuelta', 'cierre__cliente']
    search_fields = ['rut_empleado', 'nombre_empleado']
    raw_id_fields = ['cierre', 'concepto']


@admin.register(Incidencia)
class IncidenciaAdmin(admin.ModelAdmin):
    list_display = [
        'cierre', 'concepto', 'categoria', 'variacion_porcentual',
        'estado', 'fecha_deteccion'
    ]
    list_filter = ['estado', 'categoria', 'cierre__cliente']
    search_fields = ['concepto__nombre_erp']
    raw_id_fields = ['cierre', 'concepto', 'resuelto_por']


@admin.register(ComentarioIncidencia)
class ComentarioIncidenciaAdmin(admin.ModelAdmin):
    list_display = ['incidencia', 'autor', 'fecha_creacion', 'editado']
    list_filter = ['incidencia__estado']
    raw_id_fields = ['incidencia', 'autor']


@admin.register(ResumenConsolidado)
class ResumenConsolidadoAdmin(admin.ModelAdmin):
    list_display = ['cierre', 'categoria', 'concepto', 'total_monto', 'cantidad_empleados']
    list_filter = ['categoria', 'cierre__cliente']


@admin.register(ResumenCategoria)
class ResumenCategoriaAdmin(admin.ModelAdmin):
    list_display = ['cierre', 'categoria', 'total_monto', 'cantidad_conceptos']
    list_filter = ['categoria', 'cierre__cliente']
