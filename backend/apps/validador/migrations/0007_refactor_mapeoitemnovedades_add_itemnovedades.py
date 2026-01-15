# Generated manually for novedades module refactor

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    """
    Refactoriza MapeoItemNovedades para que apunte a ConceptoLibro
    en vez de ConceptoCliente, y agrega el nuevo modelo ItemNovedades.
    
    Como MapeoItemNovedades esta vacio en produccion, se elimina y recrea.
    """

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('core', '0007_add_auditlog_model'),
        ('validador', '0006_simplify_empleadolibro_add_registrolibro'),
    ]

    operations = [
        # Paso 1: Eliminar la tabla antigua de MapeoItemNovedades
        migrations.DeleteModel(
            name='MapeoItemNovedades',
        ),
        
        # Paso 2: Crear la nueva version de MapeoItemNovedades
        migrations.CreateModel(
            name='MapeoItemNovedades',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre_novedades', models.CharField(help_text='Nombre del item como aparece en el archivo de Novedades', max_length=200)),
                ('activo', models.BooleanField(default=True, help_text='False = mapeo desactivado')),
                ('fecha_mapeo', models.DateTimeField(auto_now_add=True)),
                ('notas', models.TextField(blank=True)),
                ('cliente', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='mapeos_items', to='core.cliente')),
                ('erp', models.ForeignKey(help_text='ERP del cliente (consistente con ConceptoLibro)', on_delete=django.db.models.deletion.CASCADE, related_name='mapeos_items', to='core.erp')),
                ('concepto_libro', models.ForeignKey(help_text='Concepto clasificado del libro de remuneraciones', on_delete=django.db.models.deletion.CASCADE, related_name='mapeos_novedades', to='validador.conceptolibro')),
                ('mapeado_por', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Mapeo Item Novedades',
                'verbose_name_plural': 'Mapeos Items Novedades',
                'ordering': ['cliente', 'erp', 'nombre_novedades'],
                'unique_together': {('cliente', 'erp', 'nombre_novedades')},
            },
        ),
        
        # Paso 3: Crear el nuevo modelo ItemNovedades
        migrations.CreateModel(
            name='ItemNovedades',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre_original', models.CharField(help_text='Nombre exacto como aparece en el Excel', max_length=200)),
                ('orden', models.PositiveIntegerField(default=0, help_text='Orden en que aparece la columna en el Excel')),
                ('fecha_creacion', models.DateTimeField(auto_now_add=True)),
                ('archivo', models.ForeignKey(help_text='Archivo de novedades de origen', on_delete=django.db.models.deletion.CASCADE, related_name='items_novedades', to='validador.archivoanalista')),
                ('cliente', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='items_novedades', to='core.cliente')),
                ('erp', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='items_novedades', to='core.erp')),
                ('mapeo', models.ForeignKey(blank=True, help_text='Mapeo a concepto del libro (null si pendiente)', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='items', to='validador.mapeoitemnovedades')),
            ],
            options={
                'verbose_name': 'Item Novedades',
                'verbose_name_plural': 'Items Novedades',
                'ordering': ['archivo', 'orden'],
                'unique_together': {('archivo', 'nombre_original')},
            },
        ),
    ]
