from django.apps import AppConfig  # Importa nombres concretos desde un módulo.


class PresupuestoConfig(AppConfig):  # Define una clase Python.
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'presupuesto'
    verbose_name = 'Reservas'  # Define el nombre legible de la app en el admin.
