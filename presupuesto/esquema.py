from drf_spectacular.generators import SchemaGenerator


class GeneradorEsquema(SchemaGenerator):
    """Usa el mismo contrato en Swagger, exportaciones y check --deploy."""
    def __init__(self, *args, **kwargs):
        if not kwargs.get('urlconf'):
            kwargs['urlconf'] = 'presupuesto.esquema_urls'
        super().__init__(*args, **kwargs)
