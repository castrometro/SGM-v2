# Core app
from .models.usuario import Usuario, UsuarioManager
from .models.cliente import Cliente, Industria
from .models.servicio import Servicio, ServicioCliente
from .models.asignacion import AsignacionClienteUsuario

__all__ = [
    'Usuario',
    'UsuarioManager',
    'Cliente',
    'Industria',
    'Servicio',
    'ServicioCliente',
    'AsignacionClienteUsuario',
]
