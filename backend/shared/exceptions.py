"""
Manejo de excepciones personalizado para SGM v2.
"""

from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
from django.core.exceptions import ValidationError as DjangoValidationError
from django.http import Http404


def custom_exception_handler(exc, context):
    """
    Manejador de excepciones personalizado que proporciona 
    respuestas de error consistentes.
    """
    # Primero, obtener la respuesta estándar de DRF
    response = exception_handler(exc, context)
    
    # Si DRF no manejó la excepción, manejamos casos especiales
    if response is None:
        if isinstance(exc, DjangoValidationError):
            return Response(
                {
                    'error': True,
                    'message': 'Error de validación',
                    'details': exc.messages if hasattr(exc, 'messages') else str(exc)
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Para cualquier otra excepción no manejada
        return Response(
            {
                'error': True,
                'message': 'Error interno del servidor',
                'details': str(exc) if context.get('request') and 
                          hasattr(context['request'], 'user') and 
                          context['request'].user.is_staff else None
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    
    # Formatear la respuesta de DRF de manera consistente
    if response is not None:
        custom_response_data = {
            'error': True,
            'message': _get_error_message(response),
            'details': response.data,
            'status_code': response.status_code
        }
        response.data = custom_response_data
    
    return response


def _get_error_message(response):
    """Obtiene un mensaje de error legible basado en el código de estado."""
    status_messages = {
        400: 'Solicitud incorrecta',
        401: 'No autenticado',
        403: 'Permiso denegado',
        404: 'Recurso no encontrado',
        405: 'Método no permitido',
        409: 'Conflicto',
        422: 'Entidad no procesable',
        429: 'Demasiadas solicitudes',
        500: 'Error interno del servidor',
    }
    return status_messages.get(response.status_code, 'Error')


class SGMException(Exception):
    """Excepción base para errores del sistema SGM."""
    
    def __init__(self, message, code=None, details=None):
        self.message = message
        self.code = code
        self.details = details
        super().__init__(message)


class ArchivoInvalidoError(SGMException):
    """Error cuando un archivo no tiene el formato esperado."""
    pass


class ProcesoEnCursoError(SGMException):
    """Error cuando se intenta una operación con un proceso en curso."""
    pass


class EstadoInvalidoError(SGMException):
    """Error cuando una operación no es válida para el estado actual."""
    pass
