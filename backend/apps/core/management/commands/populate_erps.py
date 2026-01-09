"""
Management command para poblar ERPs iniciales.

Uso:
    python manage.py populate_erps
"""

from django.core.management.base import BaseCommand
from apps.core.models import ERP


class Command(BaseCommand):
    help = 'Crea los ERPs iniciales en la base de datos'

    def handle(self, *args, **options):
        erps_data = [
            {
                'slug': 'talana',
                'nombre': 'Talana',
                'descripcion': 'Sistema de gestión de recursos humanos Talana. Soporta exportación de libros de remuneraciones y movimientos.',
                'requiere_api': True,
                'formatos_soportados': ['xlsx', 'xls'],
                'schema_credenciales': {
                    'type': 'object',
                    'required': ['token', 'base_url'],
                    'properties': {
                        'token': {'type': 'string', 'description': 'API Token de Talana'},
                        'base_url': {'type': 'string', 'description': 'URL base de la API'},
                    }
                },
                'configuracion_parseo': {
                    'libro_remuneraciones': {
                        'hoja': 'Libro',
                        'header_row': 0,
                    },
                },
            },
            {
                'slug': 'buk',
                'nombre': 'BUK',
                'descripcion': 'Sistema de gestión de recursos humanos BUK. Soporta exportación de libros de remuneraciones.',
                'requiere_api': True,
                'formatos_soportados': ['xlsx', 'xls'],
                'schema_credenciales': {
                    'type': 'object',
                    'required': ['api_key', 'company_id'],
                    'properties': {
                        'api_key': {'type': 'string', 'description': 'API Key de BUK'},
                        'company_id': {'type': 'string', 'description': 'ID de la empresa'},
                    }
                },
            },
            {
                'slug': 'sap',
                'nombre': 'SAP',
                'descripcion': 'SAP HCM. Soporta exportación en Excel y TXT.',
                'requiere_api': False,
                'formatos_soportados': ['xlsx', 'xls', 'txt'],
            },
            {
                'slug': 'nubox',
                'nombre': 'Nubox',
                'descripcion': 'Sistema contable Nubox. Exportación de nóminas en Excel.',
                'requiere_api': False,
                'formatos_soportados': ['xlsx', 'xls'],
            },
            {
                'slug': 'softland',
                'nombre': 'Softland',
                'descripcion': 'ERP Softland. Exportación de nóminas en Excel.',
                'requiere_api': False,
                'formatos_soportados': ['xlsx', 'xls'],
            },
            {
                'slug': 'generic',
                'nombre': 'Genérico',
                'descripcion': 'Formato genérico para ERPs sin implementación específica. Intenta detectar automáticamente las columnas.',
                'requiere_api': False,
                'formatos_soportados': ['xlsx', 'xls', 'csv'],
            },
        ]

        created_count = 0
        updated_count = 0

        for erp_data in erps_data:
            erp, created = ERP.objects.update_or_create(
                slug=erp_data['slug'],
                defaults={
                    'nombre': erp_data['nombre'],
                    'descripcion': erp_data.get('descripcion', ''),
                    'requiere_api': erp_data.get('requiere_api', False),
                    'formatos_soportados': erp_data.get('formatos_soportados', []),
                    'schema_credenciales': erp_data.get('schema_credenciales', {}),
                    'configuracion_parseo': erp_data.get('configuracion_parseo', {}),
                    'activo': True,
                }
            )
            
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f'✅ Creado ERP: {erp.nombre}'))
            else:
                updated_count += 1
                self.stdout.write(self.style.WARNING(f'🔄 Actualizado ERP: {erp.nombre}'))

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(
            f'Resumen: {created_count} creados, {updated_count} actualizados'
        ))
