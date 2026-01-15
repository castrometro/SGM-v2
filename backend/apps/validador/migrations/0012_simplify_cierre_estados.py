"""
Migración para simplificar estados de cierre.
"""
from django.db import migrations, models


def eliminar_cierres_existentes(apps, schema_editor):
    Cierre = apps.get_model('validador', 'Cierre')
    count = Cierre.objects.count()
    if count > 0:
        print(f"\nEliminando {count} cierres existentes...")
        Cierre.objects.all().delete()
        print(f"{count} cierres eliminados.\n")


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('validador', '0011_replace_mapeo_with_concepto_novedades'),
    ]

    operations = [
        migrations.RunPython(
            eliminar_cierres_existentes,
            reverse_code=noop,
        ),
        migrations.AlterField(
            model_name='cierre',
            name='estado',
            field=models.CharField(
                choices=[
                    ('carga_archivos', 'Carga de Archivos'),
                    ('con_discrepancias', 'Con Discrepancias'),
                    ('sin_discrepancias', 'Sin Discrepancias'),
                    ('consolidado', 'Consolidado'),
                    ('con_incidencias', 'Con Incidencias'),
                    ('sin_incidencias', 'Sin Incidencias'),
                    ('finalizado', 'Finalizado'),
                    ('error', 'Error'),
                    ('cancelado', 'Cancelado'),
                ],
                default='carga_archivos',
                max_length=50,
                verbose_name='Estado'
            ),
        ),
    ]
