"""
URLs de la app Validador para SGM v2.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

# TODO: Importar viewsets cuando estén definidos

router = DefaultRouter()
# TODO: Registrar viewsets

urlpatterns = [
    path('', include(router.urls)),
]
