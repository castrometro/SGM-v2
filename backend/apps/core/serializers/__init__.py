# Serializers package
from .usuario import (
    UsuarioSerializer, 
    UsuarioCreateSerializer, 
    UsuarioMeSerializer,
    UsuarioUpdateSerializer,
    ResetPasswordSerializer,
    ChangePasswordSerializer,
)
from .cliente import (
    ClienteSerializer, 
    ClienteDetailSerializer, 
    ClienteCreateSerializer, 
    IndustriaSerializer,
    UsuarioAsignadoSerializer,
)
from .servicio import ServicioSerializer, ServicioClienteSerializer
from .erp import (
    ERPSerializer,
    ERPDetailSerializer,
    ERPCreateSerializer,
    ConfiguracionERPClienteSerializer,
    ConfiguracionERPClienteDetailSerializer,
    ConfiguracionERPClienteCreateSerializer,
    ConfiguracionERPClienteMinimalSerializer,
)
from .audit import AuditLogSerializer, AuditLogListSerializer

__all__ = [
    'UsuarioSerializer',
    'UsuarioCreateSerializer',
    'UsuarioMeSerializer',
    'UsuarioUpdateSerializer',
    'ResetPasswordSerializer',
    'ChangePasswordSerializer',
    'IndustriaSerializer',
    'ClienteSerializer',
    'ClienteDetailSerializer',
    'ClienteCreateSerializer',
    'ServicioSerializer',
    'ServicioClienteSerializer',
    'UsuarioAsignadoSerializer',
    # ERP
    'ERPSerializer',
    'ERPDetailSerializer',
    'ERPCreateSerializer',
    'ConfiguracionERPClienteSerializer',
    'ConfiguracionERPClienteDetailSerializer',
    'ConfiguracionERPClienteCreateSerializer',
    'ConfiguracionERPClienteMinimalSerializer',
    # Audit
    'AuditLogSerializer',
    'AuditLogListSerializer',
]
