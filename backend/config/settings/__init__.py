"""
Settings de Django para SGM v2.

Carga automáticamente la configuración según el entorno:
- ENVIRONMENT=local -> desarrollo (DEBUG=True)
- ENVIRONMENT=production -> producción (DEBUG=False)

También se puede forzar usando DJANGO_SETTINGS_MODULE
"""
import os

# Importar base
from .base import *

# Determinar entorno
ENVIRONMENT = os.environ.get('ENVIRONMENT', 'local')
DEBUG = os.environ.get('DEBUG', 'True').lower() in ('true', '1', 'yes')

# Hosts permitidos
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')

# Configuración según entorno
if ENVIRONMENT == 'production' or not DEBUG:
    # Producción
    from .production import *
else:
    # Desarrollo
    from .development import *
