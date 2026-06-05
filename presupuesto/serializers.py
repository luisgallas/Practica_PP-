from rest_framework import serializers

from presupuesto.models import Propiedad


class PropiedadSerializer(serializers.ModelSerializer):
    anfitrion = serializers.CharField(source='id_anfitrion.username', read_only=True)
    amenities = serializers.StringRelatedField(many=True, read_only=True)

    class Meta:
        model = Propiedad
        fields = [
            'id',
            'titulo',
            'descripcion',
            'ubicacion',
            'precio_noche',
            'precio_fin_semana',
            'tarifa_limpieza',
            'estado',
            'id_anfitrion',
            'anfitrion',
            'amenities',
        ]
