"""
Celery Tasks del app Core.

Incluye tareas de mantenimiento y limpieza del sistema.
"""

from .cleanup import cleanup_task_results

__all__ = [
    "cleanup_task_results",
]
