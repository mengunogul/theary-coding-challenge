"""
Main URL configuration for the Theary coding challenge project.

This module defines the root URL patterns that route requests to appropriate
applications and API documentation endpoints.

URL Patterns:
    - admin/: Django admin interface
    - api/tree/: Tree management API endpoints
    - api/schema/: OpenAPI schema endpoint
    - api/swagger: Interactive API documentation (Swagger UI)
"""

from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    # Django admin interface
    path("admin/", admin.site.urls),
    # Tree API endpoints
    path("api/tree/", include("api.tree.urls")),
    # API documentation endpoints
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/swagger/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
]
