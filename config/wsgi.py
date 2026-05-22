import os  # Importa un módulo de Python.

from django.core.wsgi import get_wsgi_application  # Importa nombres concretos desde un módulo.

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')  # Configura una variable de entorno si aún no existe.

application = get_wsgi_application()  # Crea el objeto de aplicación WSGI/ASGI para el servidor web.
