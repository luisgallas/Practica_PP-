from django.urls import path  # Importa nombres concretos desde un módulo.
from presupuesto.views import api_info  # Importa nombres concretos desde un módulo.

urlpatterns = [  # Define la lista de rutas URL del proyecto o aplicación.
    path('', api_info, name='api_info'),  # Define una ruta URL y la vista asociada.
]
