"""
Paginación personalizada para SGM v2.
"""

from rest_framework.pagination import PageNumberPagination


class StandardResultsSetPagination(PageNumberPagination):
    """Paginación estándar con 20 elementos por página."""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class LargeResultsSetPagination(PageNumberPagination):
    """Paginación para listados grandes con 50 elementos por página."""
    page_size = 50
    page_size_query_param = 'page_size'
    max_page_size = 200


class SmallResultsSetPagination(PageNumberPagination):
    """Paginación para listados pequeños con 10 elementos por página."""
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 50
