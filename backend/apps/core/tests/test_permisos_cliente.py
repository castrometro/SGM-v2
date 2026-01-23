"""
Tests para permisos de acceso a clientes.

Verifica la lógica de:
- get_clientes_asignados() en Usuario
- get_clientes_supervisados() en Usuario
- CanAccessCliente permission class
"""

import pytest
from django.test import TestCase
from rest_framework.test import APIRequestFactory

from apps.core.models import Usuario, Cliente, Servicio
from apps.core.constants import TipoUsuario
from shared.permissions import CanAccessCliente


class TestUsuarioClientesMethods(TestCase):
    """Tests para métodos de Usuario relacionados con clientes."""
    
    @classmethod
    def setUpTestData(cls):
        """Crear datos de prueba."""
        # Crear servicio
        cls.servicio = Servicio.objects.create(
            nombre='Servicio Test',
            codigo='SRV001'
        )
        
        # Crear usuarios
        cls.gerente = Usuario.objects.create_user(
            email='gerente@test.com',
            password='test123',
            tipo_usuario=TipoUsuario.GERENTE,
            first_name='Gerente',
            last_name='Test'
        )
        
        cls.supervisor = Usuario.objects.create_user(
            email='supervisor@test.com',
            password='test123',
            tipo_usuario=TipoUsuario.SUPERVISOR,
            first_name='Supervisor',
            last_name='Test'
        )
        
        cls.analista = Usuario.objects.create_user(
            email='analista@test.com',
            password='test123',
            tipo_usuario=TipoUsuario.ANALISTA,
            supervisor=cls.supervisor,
            first_name='Analista',
            last_name='Test'
        )
        
        cls.analista2 = Usuario.objects.create_user(
            email='analista2@test.com',
            password='test123',
            tipo_usuario=TipoUsuario.ANALISTA,
            first_name='Analista2',
            last_name='Test'
        )
        
        # Crear clientes
        cls.cliente_analista = Cliente.objects.create(
            razon_social='Cliente Analista',
            rut='12345678-9',
            servicio=cls.servicio,
            usuario_asignado=cls.analista
        )
        
        cls.cliente_supervisor = Cliente.objects.create(
            razon_social='Cliente Supervisor',
            rut='98765432-1',
            servicio=cls.servicio,
            usuario_asignado=cls.supervisor
        )
        
        cls.cliente_sin_asignar = Cliente.objects.create(
            razon_social='Cliente Sin Asignar',
            rut='11111111-1',
            servicio=cls.servicio
        )
    
    def test_analista_get_clientes_asignados(self):
        """Analista solo ve sus clientes asignados."""
        clientes = self.analista.get_clientes_asignados()
        self.assertEqual(clientes.count(), 1)
        self.assertIn(self.cliente_analista, clientes)
    
    def test_supervisor_get_clientes_asignados(self):
        """Supervisor ve sus clientes directos."""
        clientes = self.supervisor.get_clientes_asignados()
        self.assertEqual(clientes.count(), 1)
        self.assertIn(self.cliente_supervisor, clientes)
    
    def test_supervisor_get_clientes_supervisados(self):
        """Supervisor ve clientes de sus analistas supervisados."""
        clientes = self.supervisor.get_clientes_supervisados()
        # Incluye clientes propios + clientes de analistas supervisados
        self.assertIn(self.cliente_analista, clientes)
        self.assertIn(self.cliente_supervisor, clientes)
    
    def test_gerente_get_todos_los_clientes(self):
        """Gerente ve todos los clientes."""
        clientes = self.gerente.get_todos_los_clientes()
        self.assertEqual(clientes.count(), Cliente.objects.count())
    
    def test_analista_sin_supervisor_get_clientes(self):
        """Analista sin supervisor solo ve sus clientes."""
        clientes = self.analista2.get_clientes_asignados()
        self.assertEqual(clientes.count(), 0)


class TestCanAccessClientePermission(TestCase):
    """Tests para CanAccessCliente permission class."""
    
    @classmethod
    def setUpTestData(cls):
        """Crear datos de prueba."""
        cls.servicio = Servicio.objects.create(
            nombre='Servicio Test',
            codigo='SRV002'
        )
        
        cls.analista = Usuario.objects.create_user(
            email='analista_perm@test.com',
            password='test123',
            tipo_usuario=TipoUsuario.ANALISTA,
        )
        
        cls.cliente = Cliente.objects.create(
            razon_social='Cliente Perm Test',
            rut='22222222-2',
            servicio=cls.servicio,
            usuario_asignado=cls.analista
        )
        
        cls.otro_cliente = Cliente.objects.create(
            razon_social='Otro Cliente',
            rut='33333333-3',
            servicio=cls.servicio
        )
    
    def test_analista_puede_acceder_cliente_asignado(self):
        """Analista puede acceder a su cliente asignado."""
        factory = APIRequestFactory()
        request = factory.get('/')
        request.user = self.analista
        
        permission = CanAccessCliente()
        
        # Mock view con cliente_id en kwargs
        class MockView:
            kwargs = {'cliente_id': self.cliente.id}
        
        self.assertTrue(permission.has_permission(request, MockView()))
    
    def test_analista_no_puede_acceder_otro_cliente(self):
        """Analista no puede acceder a cliente no asignado."""
        factory = APIRequestFactory()
        request = factory.get('/')
        request.user = self.analista
        
        permission = CanAccessCliente()
        
        class MockView:
            kwargs = {'cliente_id': self.otro_cliente.id}
        
        self.assertFalse(permission.has_permission(request, MockView()))
