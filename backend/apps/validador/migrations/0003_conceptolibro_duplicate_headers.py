# Generated manually for handling duplicate headers in ConceptoLibro

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('validador', '0002_archivoerp_empleados_procesados_and_more'),
    ]

    operations = [
        # Add new fields for duplicate header handling
        migrations.AddField(
            model_name='conceptolibro',
            name='header_pandas',
            field=models.CharField(blank=True, help_text='Nombre como pandas lo lee (ej: "BONO.1" para el segundo BONO)', max_length=200),
        ),
        migrations.AddField(
            model_name='conceptolibro',
            name='ocurrencia',
            field=models.PositiveIntegerField(default=1, help_text='Número de ocurrencia si el header está duplicado (1, 2, 3...)'),
        ),
        migrations.AddField(
            model_name='conceptolibro',
            name='es_duplicado',
            field=models.BooleanField(default=False, help_text='True si este header aparece múltiples veces en el Excel'),
        ),
        
        # Update unique_together constraint
        migrations.AlterUniqueTogether(
            name='conceptolibro',
            unique_together={('cliente', 'erp', 'header_original', 'ocurrencia')},
        ),
        
        # Add new index for header_pandas
        migrations.AddIndex(
            model_name='conceptolibro',
            index=models.Index(fields=['cliente', 'erp', 'header_pandas'], name='validador_cl_erp_h_pandas_idx'),
        ),
        
        # Update ordering
        migrations.AlterModelOptions(
            name='conceptolibro',
            options={
                'ordering': ['cliente', 'erp', 'orden', 'header_original', 'ocurrencia'],
                'verbose_name': 'Concepto Libro',
                'verbose_name_plural': 'Conceptos Libro'
            },
        ),
    ]
