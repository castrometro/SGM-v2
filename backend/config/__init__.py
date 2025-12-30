"""
Configuración del proyecto SGM v2.

Este módulo exporta la app de Celery para asegurar que se cargue
cuando Django inicia.
"""

from .celery import app as celery_app

__all__ = ('celery_app',)
