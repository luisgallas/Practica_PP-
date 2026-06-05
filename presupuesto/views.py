from django.http import JsonResponse
from django.shortcuts import render
from rest_framework import generics

from presupuesto.models import Propiedad
from presupuesto.serializers import PropiedadSerializer


def home(request):
    """Pagina principal del backend."""
    propiedades = Propiedad.objects.select_related('id_anfitrion').prefetch_related('amenities')
    return render(request, 'home.html', {
        'propiedades': propiedades,
    })


def api_info(request):
    """Endpoint basico de informacion."""
    return JsonResponse({
        'mensaje': 'API Practica PP',
        'version': '1.0.0',
    })


class PropiedadListAPIView(generics.ListAPIView):
    """Lista todas las propiedades."""
    queryset = Propiedad.objects.select_related('id_anfitrion').prefetch_related('amenities')
    serializer_class = PropiedadSerializer


class PropiedadDetailAPIView(generics.RetrieveAPIView):
    """Muestra el detalle de una propiedad."""
    queryset = Propiedad.objects.select_related('id_anfitrion').prefetch_related('amenities')
    serializer_class = PropiedadSerializer
