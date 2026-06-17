from rest_framework import serializers

from .models import Amenity, Disponibilidad, Propiedad, Reserva, Review, Usuario


class UsuarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Usuario
        fields = ["id", "username", "first_name", "last_name", "email", "rol", "telefono"]


class AmenitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Amenity
        fields = ["id", "nombre"]


class PropiedadSerializer(serializers.ModelSerializer):
    anfitrion = UsuarioSerializer(source="id_anfitrion", read_only=True)
    amenities = AmenitySerializer(many=True, read_only=True)

    class Meta:
        model = Propiedad
        fields = [
            "id",
            "titulo",
            "descripcion",
            "calle",
            "ubicacion",
            "precio_noche",
            "precio_fin_semana",
            "tarifa_limpieza",
            "estado",
            "anfitrion",
            "amenities",
        ]


class ReservaSerializer(serializers.ModelSerializer):
    propiedad = PropiedadSerializer(source="id_propiedad", read_only=True)
    huesped = UsuarioSerializer(source="id_huesped", read_only=True)
    disponibilidades = serializers.SerializerMethodField()
    id_propiedad = serializers.PrimaryKeyRelatedField(
        queryset=Propiedad.objects.all(),
        write_only=True,
    )
    id_huesped = serializers.PrimaryKeyRelatedField(
        queryset=Usuario.objects.filter(rol="huesped"),
        write_only=True,
    )

    class Meta:
        model = Reserva
        fields = [
            "id",
            "fecha_inicio",
            "fecha_fin",
            "cantidad_huespedes",
            "estado",
            "precio_total",
            "id_propiedad",
            "id_huesped",
            "propiedad",
            "huesped",
            "disponibilidades",
        ]
        read_only_fields = ["precio_total"]

    def get_disponibilidades(self, obj):
        return [
            {
                "id": disponibilidad.id,
                "fecha": disponibilidad.fecha,
                "estado": disponibilidad.estado,
                "fecha_inicio_reserva": disponibilidad.fecha_inicio_reserva,
                "fecha_publicacion": disponibilidad.fecha_publicacion,
            }
            for disponibilidad in obj.disponibilidades.order_by("fecha")
        ]


class DisponibilidadSerializer(serializers.ModelSerializer):
    propiedad = PropiedadSerializer(source="id_propiedad", read_only=True)

    class Meta:
        model = Disponibilidad
        fields = ["id", "fecha", "fecha_inicio_reserva", "fecha_publicacion", "estado", "propiedad", "id_reserva"]


class ReviewSerializer(serializers.ModelSerializer):
    usuario = UsuarioSerializer(source="id_usuario", read_only=True)
    propiedad = PropiedadSerializer(source="id_propiedad", read_only=True)

    class Meta:
        model = Review
        fields = ["id", "calificacion", "comentario", "fecha", "usuario", "propiedad", "id_reserva"]
