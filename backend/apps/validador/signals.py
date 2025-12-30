"""
Signals del app Validador.
"""

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Discrepancia, Incidencia


@receiver([post_save, post_delete], sender=Discrepancia)
def actualizar_contadores_discrepancias(sender, instance, **kwargs):
    """Actualiza los contadores del cierre cuando cambian las discrepancias."""
    if instance.cierre_id:
        instance.cierre.actualizar_contadores()


@receiver([post_save, post_delete], sender=Incidencia)
def actualizar_contadores_incidencias(sender, instance, **kwargs):
    """Actualiza los contadores del cierre cuando cambian las incidencias."""
    if instance.cierre_id:
        instance.cierre.actualizar_contadores()
