"""
Admin de la app Core para SGM v2.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import Usuario, Cliente, Industria, Servicio, ServicioCliente


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
