"""
Admin del app Validador.
"""

from django.contrib import admin
from django.contrib import messages
from django.utils.html import format_html
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
    MovimientoMes,
    MovimientoAnalista,
)


class CierreListFilter(admin.SimpleListFilter):
    """
    Filtro por Cierre usando input de texto (ID o búsqueda).
    Evita cargar miles de opciones en el dropdown.
    """
    title = 'Cierre (ID)'
    parameter_name = 'cierre_id'
    
    def lookups(self, request, model_admin):
        # Mostrar solo los últimos 20 cierres para referencia rápida
        cierres = Cierre.objects.select_related('cliente').order_by('-id')[:20]
        return [(c.id, f"{c.id}: {c.cliente.razon_social} - {c.periodo}") for c in cierres]
    
    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(cierre_id=self.value())
        return queryset


class ClienteListFilter(admin.SimpleListFilter):
    """
    Filtro por Cliente usando lista reducida.
    """
    title = 'Cliente'
    parameter_name = 'cliente_id'
    
    def lookups(self, request, model_admin):
        from apps.core.models import Cliente
        # Solo clientes que tienen cierres
        clientes = Cliente.objects.filter(
            cierres__isnull=False
        ).distinct().order_by('razon_social')[:50]
        return [(c.id, c.razon_social) for c in clientes]
    
    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(cierre__cliente_id=self.value())
        return queryset


class BulkDeleteMixin:
    """
    Mixin para permitir eliminación masiva sin página de confirmación detallada.
    Útil para modelos con 10k-20k+ registros.
    """
    
    def delete_queryset(self, request, queryset):
        """Elimina en lotes para evitar timeouts."""
        count = queryset.count()
        # Eliminación directa en lotes de 1000
        batch_size = 1000
        while True:
            batch = list(queryset.values_list('pk', flat=True)[:batch_size])
            if not batch:
                break
            queryset.model.objects.filter(pk__in=batch).delete()
        messages.success(request, f"Se eliminaron {count} registros exitosamente.")
    
    def get_deleted_objects(self, objs, request):
        """
        Override para evitar cargar todos los objetos relacionados en memoria.
        Para lotes grandes, solo muestra resumen.
        """
        from django.contrib.admin.utils import get_deleted_objects
        
        if hasattr(objs, 'count'):
            count = objs.count()
        else:
            count = len(objs)
        
        if count > 100:
            # Para más de 100 objetos, no mostrar lista detallada
            return (
                [f"{count} registros de {self.model._meta.verbose_name_plural}"],
                {},  # model_count
                set(),  # perms_needed
                [],  # protected
            )
        # Para pocos objetos, usar comportamiento normal
        return get_deleted_objects(objs, request, self.admin_site)


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
class EmpleadoLibroAdmin(BulkDeleteMixin, admin.ModelAdmin):
    list_display = ['rut', 'nombre', 'cierre', 'archivo_erp', 'fecha_creacion']
    list_filter = [ClienteListFilter, CierreListFilter, 'archivo_erp__tipo']
    search_fields = ['rut', 'nombre']
    raw_id_fields = ['cierre', 'archivo_erp']
    readonly_fields = ['fecha_creacion']


@admin.register(RegistroLibro)
class RegistroLibroAdmin(BulkDeleteMixin, admin.ModelAdmin):
    list_display = ['empleado', 'concepto', 'monto', 'cierre']
    list_filter = [ClienteListFilter, CierreListFilter, 'concepto__categoria']
    search_fields = ['empleado__rut', 'empleado__nombre']
    raw_id_fields = ['cierre', 'empleado', 'concepto']


@admin.register(RegistroNovedades)
class RegistroNovedadesAdmin(BulkDeleteMixin, admin.ModelAdmin):
    list_display = [
        'rut_empleado', 'nombre_empleado', 'nombre_item', 
        'monto_formateado', 'concepto_novedades', 'cierre_info'
    ]
    list_filter = [ClienteListFilter, CierreListFilter]
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
class DiscrepanciaAdmin(BulkDeleteMixin, admin.ModelAdmin):
    list_display = [
        'cierre', 'tipo', 'rut_empleado', 'concepto',
        'diferencia', 'resuelta', 'fecha_deteccion'
    ]
    list_filter = [ClienteListFilter, CierreListFilter, 'tipo', 'origen', 'resuelta']
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


@admin.register(MovimientoMes)
class MovimientoMesAdmin(BulkDeleteMixin, admin.ModelAdmin):
    list_display = [
        'rut', 'nombre', 'tipo', 'fecha_inicio', 'fecha_fin', 
        'dias', 'tipo_contrato', 'hoja_origen', 'cierre_info'
    ]
    list_filter = [ClienteListFilter, CierreListFilter, 'tipo', 'hoja_origen']
    search_fields = ['rut', 'nombre', 'causal']
    raw_id_fields = ['cierre', 'archivo_erp']
    readonly_fields = ['datos_raw']
    list_per_page = 50
    list_select_related = ['cierre', 'cierre__cliente', 'archivo_erp']
    
    fieldsets = (
        (None, {
            'fields': ('cierre', 'archivo_erp', 'tipo', 'hoja_origen')
        }),
        ('Empleado', {
            'fields': ('rut', 'nombre')
        }),
        ('Fechas y Duración', {
            'fields': ('fecha_inicio', 'fecha_fin', 'dias')
        }),
        ('Detalles', {
            'fields': ('tipo_contrato', 'causal', 'tipo_licencia')
        }),
        ('Datos Raw', {
            'fields': ('datos_raw',),
            'classes': ('collapse',)
        }),
    )
    
    @admin.display(description='Cierre')
    def cierre_info(self, obj):
        return f"{obj.cierre.cliente.razon_social} - {obj.cierre.periodo}"


@admin.register(MovimientoAnalista)
class MovimientoAnalistaAdmin(BulkDeleteMixin, admin.ModelAdmin):
    list_display = [
        'rut', 'nombre', 'tipo', 'origen', 'fecha_inicio', 'fecha_fin',
        'dias', 'causal_truncada', 'cierre_info'
    ]
    list_filter = [ClienteListFilter, CierreListFilter, 'tipo', 'origen']
    search_fields = ['rut', 'nombre', 'causal']
    raw_id_fields = ['cierre', 'archivo_analista']
    readonly_fields = ['datos_raw']
    list_per_page = 50
    list_select_related = ['cierre', 'cierre__cliente', 'archivo_analista']
    
    fieldsets = (
        (None, {
            'fields': ('cierre', 'archivo_analista', 'tipo', 'origen')
        }),
        ('Empleado', {
            'fields': ('rut', 'nombre')
        }),
        ('Fechas y Duración', {
            'fields': ('fecha_inicio', 'fecha_fin', 'dias')
        }),
        ('Detalles', {
            'fields': ('causal', 'tipo_ausentismo')
        }),
        ('Datos Raw', {
            'fields': ('datos_raw',),
            'classes': ('collapse',)
        }),
    )
    
    @admin.display(description='Cierre')
    def cierre_info(self, obj):
        return f"{obj.cierre.cliente.razon_social} - {obj.cierre.periodo}"
    
    @admin.display(description='Causal')
    def causal_truncada(self, obj):
        if obj.causal and len(obj.causal) > 30:
            return obj.causal[:30] + '...'
        return obj.causal or '-'
