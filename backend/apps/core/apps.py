from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.core'
    verbose_name = 'Core - Usuarios y Clientes'
    
    def ready(self):
        # Importar signals cuando la app esté lista
        pass
