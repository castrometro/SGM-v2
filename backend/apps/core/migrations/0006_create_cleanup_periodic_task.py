"""
Data migration para programar la tarea de limpieza de TaskResults.

Crea un PeriodicTask en django_celery_beat para ejecutar
core.cleanup_task_results diariamente a las 3:00 AM.

Compliance: ISO 27001:A.8.10, Ley 21.719:Art.25
"""

from django.db import migrations


def create_cleanup_periodic_task(apps, schema_editor):
    """Crea la tarea periodica de limpieza."""
    IntervalSchedule = apps.get_model("django_celery_beat", "IntervalSchedule")
    PeriodicTask = apps.get_model("django_celery_beat", "PeriodicTask")
    
    # Crear intervalo de 24 horas
    schedule, _ = IntervalSchedule.objects.get_or_create(
        every=24,
        period="hours",
    )
    
    # Crear tarea periodica
    PeriodicTask.objects.get_or_create(
        name="Limpieza de TaskResults para auditoria",
        defaults={
            "task": "core.cleanup_task_results",
            "interval": schedule,
            "enabled": True,
            "description": (
                "Elimina TaskResults antiguos segun politica de retencion. "
                "ISO 27001:A.8.10 - Ley 21.719:Art.25"
            ),
        }
    )


def remove_cleanup_periodic_task(apps, schema_editor):
    """Elimina la tarea periodica de limpieza."""
    PeriodicTask = apps.get_model("django_celery_beat", "PeriodicTask")
    
    PeriodicTask.objects.filter(
        task="core.cleanup_task_results"
    ).delete()


class Migration(migrations.Migration):
    
    dependencies = [
        ("core", "0005_add_erp_models"),
        ("django_celery_beat", "0018_improve_crontab_helptext"),
    ]
    
    operations = [
        migrations.RunPython(
            create_cleanup_periodic_task,
            remove_cleanup_periodic_task,
        ),
    ]
