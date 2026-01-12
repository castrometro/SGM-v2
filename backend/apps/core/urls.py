"""
URLs de la app Core para SGM v2.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    UsuarioViewSet,
    MeView,
    ClienteViewSet,
    IndustriaViewSet,
    ServicioViewSet,
    ServicioClienteViewSet,
    ERPViewSet,
    ConfiguracionERPClienteViewSet,
    AuditLogViewSet,
)

router = DefaultRouter()
router.register(r'usuarios', UsuarioViewSet, basename='usuario')
router.register(r'clientes', ClienteViewSet, basename='cliente')
router.register(r'industrias', IndustriaViewSet, basename='industria')
router.register(r'servicios', ServicioViewSet, basename='servicio')
router.register(r'servicios-cliente', ServicioClienteViewSet, basename='servicio-cliente')
router.register(r'erps', ERPViewSet, basename='erp')
router.register(r'configuraciones-erp', ConfiguracionERPClienteViewSet, basename='configuracion-erp')
router.register(r'audit-logs', AuditLogViewSet, basename='audit-log')

urlpatterns = [
    path('me/', MeView.as_view(), name='me'),
    path('', include(router.urls)),
]
