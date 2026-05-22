from django.contrib import admin  # Importa nombres concretos desde un módulo.
from django.urls import path, include  # Importa nombres concretos desde un módulo.
from presupuesto.views import home  # Importa nombres concretos desde un módulo.

urlpatterns = [  # Define la lista de rutas URL del proyecto o aplicación.
    path('', home, name='home'),  # Define una ruta URL y la vista asociada.
    path('admin/', admin.site.urls),  # Define una ruta URL y la vista asociada.
    path('api/', include('presupuesto.urls')),  # Define una ruta URL y la vista asociada.
]
