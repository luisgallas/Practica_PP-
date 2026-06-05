from django.urls import path

from presupuesto.views import api_info, PropiedadDetailAPIView, PropiedadListAPIView


urlpatterns = [
    path('', api_info, name='api_info'),
    path('propiedades/', PropiedadListAPIView.as_view(), name='propiedad-list'),
    path('propiedades/<int:pk>/', PropiedadDetailAPIView.as_view(), name='propiedad-detail'),
]
