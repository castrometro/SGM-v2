"""
Configuración de Celery para SGM v2.

Colas:
- validador_queue: Procesamiento de archivos Excel (concurrencia alta)
- default: Tareas generales
"""

import os
from celery import Celery

# Configurar el módulo de settings de Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('sgm_v2')

# Usar configuración de Django con prefijo CELERY_
app.config_from_object('django.conf:settings', namespace='CELERY')

# Configuración de colas
app.conf.task_queues = {
    'validador_queue': {
        'exchange': 'validador_queue',
        'routing_key': 'validador_queue',
    },
    'default': {
        'exchange': 'default',
        'routing_key': 'default',
    },
}

# Rutas de tareas a sus colas
app.conf.task_routes = {
    'apps.validador.tasks.*': {'queue': 'validador_queue'},
}

# Autodescubrir tareas en todas las apps instaladas
app.autodiscover_tasks()


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """Tarea de debug para verificar que Celery funciona."""
    print(f'Request: {self.request!r}')
