from django.shortcuts import render  # Importa nombres concretos desde un módulo.
from django.http import JsonResponse  # Importa nombres concretos desde un módulo.


def home(request):  # Define una función / método.
    """Página principal del backend"""
    from presupuesto.models import Propiedad  # Importa nombres concretos desde un módulo.

    propiedades = Propiedad.objects.select_related('id_anfitrion').prefetch_related('amenities')  # Consulta o crea objetos en la base de datos.
    return render(request, 'home.html', {  # Devuelve un valor desde la función.
        'propiedades': propiedades,
    })


def api_info(request):  # Define una función / método.
    """Endpoint básico de información"""
    return JsonResponse({  # Devuelve un valor desde la función.
        'mensaje': 'API Practica PP',
        'versión': '1.0.0'
    })
