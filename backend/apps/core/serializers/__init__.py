# Serializers package
from .usuario import UsuarioSerializer, UsuarioCreateSerializer, UsuarioMeSerializer
from .cliente import ClienteSerializer, ClienteDetailSerializer, ClienteCreateSerializer, IndustriaSerializer
from .servicio import ServicioSerializer, ServicioClienteSerializer
from .asignacion import AsignacionClienteUsuarioSerializer

__all__ = [
    'UsuarioSerializer',
    'UsuarioCreateSerializer',
    'UsuarioMeSerializer',
    'IndustriaSerializer',
    'ClienteSerializer',
    'ClienteDetailSerializer',
    'ClienteCreateSerializer',
    'ServicioSerializer',
    'ServicioClienteSerializer',
    'AsignacionClienteUsuarioSerializer',
]
