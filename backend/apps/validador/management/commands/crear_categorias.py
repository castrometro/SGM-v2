"""
Management command para crear las categorías de conceptos iniciales.
"""

from django.core.management.base import BaseCommand
from apps.validador.models import CategoriaConcepto


class Command(BaseCommand):
    help = 'Crea las categorías de conceptos iniciales del sistema'
    
    def handle(self, *args, **options):
        categorias = [
            {
                'codigo': 'haberes_imponibles',
                'nombre': 'Haberes Imponibles',
                'descripcion': 'Ingresos afectos a cotizaciones previsionales (Sueldo Base, Gratificación, Bonos, Comisiones, Horas Extra, etc.)',
                'se_compara': True,
                'se_incluye_en_incidencias': True,
                'orden': 1,
            },
            {
                'codigo': 'haberes_no_imponibles',
                'nombre': 'Haberes No Imponibles',
                'descripcion': 'Ingresos no afectos a cotizaciones (Colación, Movilización, Viáticos, Asignación Familiar, etc.)',
                'se_compara': True,
                'se_incluye_en_incidencias': True,
                'orden': 2,
            },
            {
                'codigo': 'descuentos_legales',
                'nombre': 'Descuentos Legales',
                'descripcion': 'AFP, Salud, Seguro de Cesantía, Impuesto Único',
                'se_compara': True,
                'se_incluye_en_incidencias': False,  # EXCLUIDO de incidencias
                'orden': 3,
            },
            {
                'codigo': 'otros_descuentos',
                'nombre': 'Otros Descuentos',
                'descripcion': 'Anticipos, Préstamos, Cuotas Sindicales, Caja de Compensación, etc.',
                'se_compara': True,
                'se_incluye_en_incidencias': True,
                'orden': 4,
            },
            {
                'codigo': 'aportes_patronales',
                'nombre': 'Aportes Patronales',
                'descripcion': 'Aportes del empleador: Seguro Cesantía Empleador, Mutual, SIS, etc.',
                'se_compara': True,
                'se_incluye_en_incidencias': True,
                'orden': 5,
            },
            {
                'codigo': 'informativos',
                'nombre': 'Informativos',
                'descripcion': 'Información adicional: Días Trabajados, Días Ausencia, Horas Extra (cantidad), etc.',
                'se_compara': False,  # NO SE COMPARA
                'se_incluye_en_incidencias': False,  # EXCLUIDO de incidencias
                'orden': 6,
            },
        ]
        
        creadas = 0
        actualizadas = 0
        
        for cat_data in categorias:
            categoria, created = CategoriaConcepto.objects.update_or_create(
                codigo=cat_data['codigo'],
                defaults={
                    'nombre': cat_data['nombre'],
                    'descripcion': cat_data['descripcion'],
                    'se_compara': cat_data['se_compara'],
                    'se_incluye_en_incidencias': cat_data['se_incluye_en_incidencias'],
                    'orden': cat_data['orden'],
                }
            )
            
            if created:
                creadas += 1
                self.stdout.write(
                    self.style.SUCCESS(f'  ✓ Creada: {categoria.nombre}')
                )
            else:
                actualizadas += 1
                self.stdout.write(
                    self.style.WARNING(f'  ↻ Actualizada: {categoria.nombre}')
                )
        
        self.stdout.write('')
        self.stdout.write(
            self.style.SUCCESS(
                f'Categorías de conceptos: {creadas} creadas, {actualizadas} actualizadas'
            )
        )
