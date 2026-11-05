"""Contrato de la interfaz Hospeda PY. Los datos privados nunca son públicos."""
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as ErrorDjango
from django.utils import timezone
from rest_framework import serializers

from .models import Amenity, Propiedad, Reserva, Review, Usuario
from .serializers import AmenitySerializer, PropiedadFotoSerializer


class UsuarioPublicoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Usuario
        fields = ['id', 'username', 'first_name']


class AlojamientoSerializer(serializers.ModelSerializer):
    anfitrion = UsuarioPublicoSerializer(source='id_anfitrion', read_only=True)
    amenities = AmenitySerializer(many=True, read_only=True)
    servicios = serializers.PrimaryKeyRelatedField(source='amenities', many=True, queryset=Amenity.objects.all(), write_only=True, required=False)
    fotos = PropiedadFotoSerializer(many=True, read_only=True)
    puntuacion = serializers.FloatField(read_only=True, allow_null=True)
    cantidad_resenas = serializers.IntegerField(read_only=True)

    class Meta:
        model = Propiedad
        fields = ['id', 'titulo', 'descripcion', 'calle', 'ubicacion', 'tipo_alojamiento', 'capacidad_maxima_huespedes', 'precio_noche', 'precio_fin_semana', 'tarifa_limpieza', 'estado', 'permite_mascotas', 'permite_fumar', 'permite_fiestas', 'politica_cancelacion', 'anfitrion', 'amenities', 'servicios', 'fotos', 'puntuacion', 'cantidad_resenas']
        extra_kwargs = {
            'capacidad_maxima_huespedes': {'min_value': 1, 'max_value': 100},
            'precio_noche': {'min_value': 1}, 'precio_fin_semana': {'min_value': 1},
            'tarifa_limpieza': {'min_value': 0}, 'descripcion': {'max_length': 10000},
        }


class RegistroSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, max_length=128)
    rol = serializers.ChoiceField(choices=['huesped', 'anfitrion'])
    email = serializers.EmailField(required=True)

    class Meta:
        model = Usuario
        fields = ['username', 'first_name', 'last_name', 'email', 'telefono', 'password', 'rol']

    def validate(self, datos):
        usuario = Usuario(**{clave: valor for clave, valor in datos.items() if clave != 'password'})
        try:
            validate_password(datos['password'], usuario)
        except ErrorDjango as error:
            raise serializers.ValidationError({'password': error.messages})
        return datos

    def create(self, validated_data):
        return Usuario.objects.create_user(**validated_data)


class FechasSerializer(serializers.Serializer):
    desde = serializers.DateField()
    hasta = serializers.DateField()
    huespedes = serializers.IntegerField(min_value=1, max_value=100, default=1)

    def validate(self, datos):
        if datos['desde'] < timezone.localdate():
            raise serializers.ValidationError('La entrada no puede ser una fecha pasada.')
        noches = (datos['hasta'] - datos['desde']).days
        if noches < 1 or noches > 365:
            raise serializers.ValidationError('Elegí una estadía de entre 1 y 365 noches.')
        return datos


class CrearReservaSerializer(FechasSerializer):
    alojamiento = serializers.PrimaryKeyRelatedField(queryset=Propiedad.objects.filter(estado='disponible'))


class ReservaWebSerializer(serializers.ModelSerializer):
    propiedad = AlojamientoSerializer(source='id_propiedad', read_only=True)
    huesped = UsuarioPublicoSerializer(source='id_huesped', read_only=True)
    tiene_resena = serializers.BooleanField(read_only=True)

    class Meta:
        model = Reserva
        fields = ['id', 'fecha_inicio', 'fecha_fin', 'cantidad_huespedes', 'estado', 'precio_total', 'propiedad', 'huesped', 'monto_reembolso', 'motivo_cancelacion', 'tiene_resena']


class ResenaSerializer(serializers.ModelSerializer):
    usuario = UsuarioPublicoSerializer(source='id_usuario', read_only=True)

    class Meta:
        model = Review
        fields = ['id', 'calificacion', 'comentario', 'fecha', 'usuario', 'id_reserva']
        read_only_fields = ['fecha']
        extra_kwargs = {'calificacion': {'min_value': 1, 'max_value': 5}, 'comentario': {'max_length': 2000}, 'id_reserva': {'validators': []}}


class IngresoSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    password = serializers.CharField(max_length=128, write_only=True)


class EstadoReservaSerializer(serializers.Serializer):
    estado = serializers.ChoiceField(choices=['confirmada', 'rechazada', 'activa', 'completada'])


class CancelacionSerializer(serializers.Serializer):
    motivo = serializers.CharField(max_length=255, required=False, allow_blank=True)


class ChatEntradaSerializer(serializers.Serializer):
    message = serializers.CharField(max_length=2000)
    confirm = serializers.BooleanField(required=False)
    accion_firmada = serializers.CharField(required=False)


class ChatSalidaSerializer(serializers.Serializer):
    reply = serializers.CharField()
    intent = serializers.CharField()
    accion_firmada = serializers.CharField(required=False)
    data = serializers.JSONField(required=False)
    pending_action = serializers.JSONField(required=False)


class CotizacionSerializer(serializers.Serializer):
    disponible = serializers.BooleanField()
    noches = serializers.IntegerField()
    total = serializers.CharField()
    limpieza = serializers.CharField()


class PanelSerializer(serializers.Serializer):
    alojamientos = serializers.IntegerField()
    reservas = serializers.IntegerField()
    pendientes = serializers.IntegerField()
    ingresos_simulados = serializers.DecimalField(max_digits=20, decimal_places=0)
    usuarios = serializers.IntegerField(required=False)
