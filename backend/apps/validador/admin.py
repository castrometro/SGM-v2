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
    MapeoItemNovedades,
    EmpleadoCierre,
    EmpleadoLibro,
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


@admin.register(MapeoItemNovedades)
class MapeoItemNovedadesAdmin(admin.ModelAdmin):
    list_display = ['nombre_novedades', 'concepto_erp', 'cliente', 'fecha_mapeo']
    list_filter = ['cliente']
    search_fields = ['nombre_novedades', 'concepto_erp__nombre_erp']
    raw_id_fields = ['cliente', 'concepto_erp', 'mapeado_por']


@admin.register(EmpleadoCierre)
class EmpleadoCierreAdmin(admin.ModelAdmin):
    list_display = ['rut', 'nombre', 'cierre', 'total_haberes', 'total_descuentos', 'liquido']
    list_filter = ['cierre__cliente', 'cierre__periodo']
    search_fields = ['rut', 'nombre']
    raw_id_fields = ['cierre']


@admin.register(EmpleadoLibro)
class EmpleadoLibroAdmin(admin.ModelAdmin):
    list_display = [
        'rut', 'nombre', 'cierre', 'archivo_erp',
        'total_haberes_imponibles', 'total_liquido'
    ]
    list_filter = ['cierre__cliente', 'cierre__periodo', 'archivo_erp__tipo']
    search_fields = ['rut', 'nombre']
    raw_id_fields = ['cierre', 'archivo_erp']
    readonly_fields = ['fecha_creacion']
    
    fieldsets = (
        ('Identificación', {
            'fields': ('cierre', 'archivo_erp', 'rut', 'nombre')
        }),
        ('Datos Adicionales', {
            'fields': ('cargo', 'centro_costo', 'area', 'fecha_ingreso'),
            'classes': ('collapse',)
        }),
        ('Detalle JSON', {
            'fields': ('datos_json',)
        }),
        ('Totales', {
            'fields': (
                'total_haberes_imponibles', 'total_haberes_no_imponibles',
                'total_descuentos_legales', 'total_otros_descuentos',
                'total_aportes_patronales', 'total_liquido'
            )
        }),
        ('Timestamps', {
            'fields': ('fecha_creacion',),
            'classes': ('collapse',)
        }),
    )


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
