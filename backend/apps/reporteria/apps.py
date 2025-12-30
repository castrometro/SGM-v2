from django.apps import AppConfig


class ReporteriaConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.reporteria'
    verbose_name = 'Reportería'
    
    def ready(self):
        pass
