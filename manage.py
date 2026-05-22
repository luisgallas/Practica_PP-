#!/usr/bin/env python
import os  # Importa un módulo de Python.
import sys  # Importa un módulo de Python.

if __name__ == '__main__':  # Bloque de ejecución principal cuando este archivo se ejecuta directamente.
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')  # Configura una variable de entorno si aún no existe.
    try:
        from django.core.management import execute_from_command_line  # Importa nombres concretos desde un módulo.
    except ImportError as exc:
        raise ImportError(  # Lanza una excepción si ocurre un error.
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)