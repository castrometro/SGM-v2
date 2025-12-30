from django.apps import AppConfig


class ValidadorConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.validador'
    verbose_name = 'Validador de Nómina'
    
    def ready(self):
        """Importar signals cuando la app está lista."""
        try:
            import apps.validador.signals  # noqa
        except ImportError:
            pass
