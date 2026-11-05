"""Solo el contrato público versionado, conservando su prefijo real."""
from django.urls import include, path

urlpatterns = [path('api/v1/', include('presupuesto.api_urls'))]
