from django.urls import path

from presupuesto.views import (
    AgentChatAPIView,
    AgentSystemPromptAPIView,
    AmenityListAPIView,
    AvailabilityAPIView,
    PropiedadDetailAPIView,
    PropiedadListAPIView,
    ReservationListCreateAPIView,
    api_info,
)


urlpatterns = [
    path('', api_info, name='api_info'), #ruta para el endpoint de informacion basica
    path('propiedades/', PropiedadListAPIView.as_view(), name='propiedad-list'), #ruta para listar todas las propiedades usando la vista basada en clases PropiedadListAPIView
    path('propiedades/<int:pk>/', PropiedadDetailAPIView.as_view(), name='propiedad-detail'), #muestra el detalle de una propiedad por su ID
    path('properties/', PropiedadListAPIView.as_view(), name='property-list'),
    path('properties/<int:pk>/', PropiedadDetailAPIView.as_view(), name='property-detail'),
    path('amenities/', AmenityListAPIView.as_view(), name='amenity-list'),
    path('availability/', AvailabilityAPIView.as_view(), name='availability'),
    path('reservations/', ReservationListCreateAPIView.as_view(), name='reservation-list-create'),
    path('agent/chat/', AgentChatAPIView.as_view(), name='agent-chat'),
    path('agent/system-prompt/', AgentSystemPromptAPIView.as_view(), name='agent-system-prompt'),
]
