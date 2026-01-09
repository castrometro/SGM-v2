"""
Admin de la app Core para SGM v2.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import Usuario, Cliente, Industria, Servicio, ServicioCliente, ERP, ConfiguracionERPCliente


@admin.register(Usuario)
class UsuarioAdmin(BaseUserAdmin):
    list_display = ['email', 'nombre', 'apellido', 'tipo_usuario', 'is_active']
    list_filter = ['tipo_usuario', 'is_active', 'is_staff']
    search_fields = ['email', 'nombre', 'apellido']
    ordering = ['apellido', 'nombre']
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Información Personal', {'fields': ('nombre', 'apellido', 'cargo')}),
        ('Rol y Supervisión', {'fields': ('tipo_usuario', 'supervisor')}),
        ('Permisos', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Fechas', {'fields': ('last_login', 'fecha_registro')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'nombre', 'apellido', 'tipo_usuario', 'password1', 'password2'),
        }),
    )
    
    readonly_fields = ['fecha_registro']


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ['razon_social', 'rut', 'industria', 'usuario_asignado', 'activo']
    list_filter = ['industria', 'activo', 'bilingue', 'usuario_asignado__tipo_usuario']
    search_fields = ['razon_social', 'nombre_comercial', 'rut']
    ordering = ['razon_social']
    raw_id_fields = ['usuario_asignado']


@admin.register(Industria)
class IndustriaAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'activa']
    search_fields = ['nombre']


@admin.register(Servicio)
class ServicioAdmin(admin.ModelAdmin):
    list_display = ['codigo', 'nombre', 'activo']
    search_fields = ['codigo', 'nombre']


@admin.register(ServicioCliente)
class ServicioClienteAdmin(admin.ModelAdmin):
    list_display = ['cliente', 'servicio', 'activo', 'fecha_inicio', 'fecha_fin']
    list_filter = ['servicio', 'activo']
    search_fields = ['cliente__razon_social']


@admin.register(ERP)
class ERPAdmin(admin.ModelAdmin):
    """Admin para catálogo de ERPs."""
    
    list_display = ['nombre', 'slug', 'requiere_api', 'formatos_display', 'activo']
    list_filter = ['activo', 'requiere_api']
    search_fields = ['nombre', 'slug', 'descripcion']
    ordering = ['nombre']
    prepopulated_fields = {'slug': ('nombre',)}
    
    fieldsets = (
        (None, {
            'fields': ('nombre', 'slug', 'descripcion', 'activo')
        }),
        ('Integración', {
            'fields': ('requiere_api', 'formatos_soportados'),
            'description': 'Configuración de integración y formatos de archivo'
        }),
        ('Configuración Técnica', {
            'fields': ('schema_credenciales', 'configuracion_parseo'),
            'classes': ('collapse',),
            'description': 'JSON para validación de credenciales y configuración de parseo'
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']
    
    def formatos_display(self, obj):
        """Muestra los formatos soportados."""
        return obj.formatos_display
    formatos_display.short_description = 'Formatos'


class ConfiguracionERPClienteInline(admin.TabularInline):
    """Inline para mostrar configuraciones ERP en el admin de Cliente."""
    
    model = ConfiguracionERPCliente
    extra = 0
    fields = ['erp', 'fecha_activacion', 'fecha_expiracion', 'activo']
    readonly_fields = ['created_at']
    autocomplete_fields = ['erp']


@admin.register(ConfiguracionERPCliente)
class ConfiguracionERPClienteAdmin(admin.ModelAdmin):
    """Admin para configuraciones ERP de clientes."""
    
    list_display = ['cliente', 'erp', 'fecha_activacion', 'fecha_expiracion', 'activo', 'esta_vigente_display']
    list_filter = ['erp', 'activo', 'fecha_activacion']
    search_fields = ['cliente__razon_social', 'cliente__rut', 'erp__nombre']
    ordering = ['cliente', 'erp']
    autocomplete_fields = ['cliente', 'erp']
    date_hierarchy = 'fecha_activacion'
    
    fieldsets = (
        (None, {
            'fields': ('cliente', 'erp', 'activo')
        }),
        ('Vigencia', {
            'fields': ('fecha_activacion', 'fecha_expiracion'),
        }),
        ('Credenciales', {
            'fields': ('credenciales',),
            'classes': ('collapse',),
            'description': 'Credenciales de acceso (almacenadas en JSON)'
        }),
        ('Notas', {
            'fields': ('notas',),
            'classes': ('collapse',),
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']
    
    def esta_vigente_display(self, obj):
        """Muestra si la configuración está vigente."""
        return '✅' if obj.esta_vigente else '❌'
    esta_vigente_display.short_description = 'Vigente'
