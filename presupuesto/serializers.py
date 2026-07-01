from rest_framework import serializers

from .models import Amenity, Disponibilidad, HistorialPropiedadVisitada, Notificacion, Propiedad, PropiedadFoto, Reserva, Review, Usuario


class UsuarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Usuario
        fields = ["id", "username", "first_name", "last_name", "email", "rol", "telefono"]


class AmenitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Amenity
        fields = ["id", "nombre"]


class PropiedadFotoSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField()

    class Meta:
        model = PropiedadFoto
        fields = ["id", "foto", "url", "descripcion", "es_portada", "fecha_publicacion"]

    def get_url(self, obj):
        request = self.context.get("request")
        if not obj.foto:
            return ""
        if request:
            return request.build_absolute_uri(obj.foto.url)
        return obj.foto.url


class PropiedadSerializer(serializers.ModelSerializer):
    anfitrion = UsuarioSerializer(source="id_anfitrion", read_only=True)
    amenities = AmenitySerializer(many=True, read_only=True)
    fotos = PropiedadFotoSerializer(many=True, read_only=True)

    class Meta:
        model = Propiedad
        fields = [
            "id",
            "titulo",
            "descripcion",
            "calle",
            "ubicacion",
            "tipo_alojamiento",
            "capacidad_maxima_huespedes",
            "precio_noche",
            "precio_fin_semana",
            "tarifa_limpieza",
            "estado",
            "permite_mascotas",
            "permite_fumar",
            "permite_fiestas",
            "politica_cancelacion",
            "anfitrion",
            "amenities",
            "fotos",
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
            "fecha_cancelacion",
            "motivo_cancelacion",
            "monto_reembolso",
            "id_propiedad",
            "id_huesped",
            "propiedad",
            "huesped",
            "disponibilidades",
        ]
        read_only_fields = ["precio_total", "fecha_cancelacion", "motivo_cancelacion", "monto_reembolso"]

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


class NotificacionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notificacion
        fields = ["id", "mensaje", "estado", "fecha", "id_reserva"]


class HistorialPropiedadVisitadaSerializer(serializers.ModelSerializer):
    propiedad = PropiedadSerializer(source="id_propiedad", read_only=True)

    class Meta:
        model = HistorialPropiedadVisitada
        fields = ["id", "fecha_visita", "cantidad_visitas", "propiedad"]
