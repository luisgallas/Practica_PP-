from django.apps import AppConfig  # Importa nombres concretos desde un módulo.


class PresupuestoConfig(AppConfig):  # Define una clase Python.
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'presupuesto'
    verbose_name = 'Presupuesto'  # Define el nombre legible del modelo en singular/plural.
