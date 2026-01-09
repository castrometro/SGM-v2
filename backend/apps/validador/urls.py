"""
URLs del app Validador.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CierreViewSet,
    ArchivoERPViewSet,
    ArchivoAnalistaViewSet,
    CategoriaConceptoViewSet,
    ConceptoClienteViewSet,
    MapeoItemNovedadesViewSet,
    LibroViewSet,
    DiscrepanciaViewSet,
    IncidenciaViewSet,
    ComentarioIncidenciaViewSet,
    DashboardViewSet,
    ResumenConsolidadoViewSet,
)

router = DefaultRouter()
router.register(r'cierres', CierreViewSet, basename='cierre')
router.register(r'archivos-erp', ArchivoERPViewSet, basename='archivo-erp')
router.register(r'archivos-analista', ArchivoAnalistaViewSet, basename='archivo-analista')
router.register(r'categorias-concepto', CategoriaConceptoViewSet, basename='categoria-concepto')
router.register(r'conceptos', ConceptoClienteViewSet, basename='concepto')
router.register(r'mapeos', MapeoItemNovedadesViewSet, basename='mapeo')
router.register(r'libro', LibroViewSet, basename='libro')
router.register(r'discrepancias', DiscrepanciaViewSet, basename='discrepancia')
router.register(r'incidencias', IncidenciaViewSet, basename='incidencia')
router.register(r'comentarios', ComentarioIncidenciaViewSet, basename='comentario')
router.register(r'dashboard', DashboardViewSet, basename='dashboard')
router.register(r'resumenes', ResumenConsolidadoViewSet, basename='resumen')

urlpatterns = [
    path('', include(router.urls)),
]
