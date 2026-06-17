import unicodedata

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


class Usuario(AbstractUser):
    ROL_CHOICES = [
        ("admin", "Admin"),
        ("anfitrion", "Anfitrion"),
        ("huesped", "Huesped"),
    ]

    rol = models.CharField(max_length=20, choices=ROL_CHOICES, default="huesped")
    telefono = models.CharField(max_length=20, blank=True, null=True)
    fecha_registro = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.username


class Amenity(models.Model):
    nombre = models.CharField(max_length=100, unique=True)

    class Meta:
        verbose_name = "Amenity"
        verbose_name_plural = "Amenities"

    def save(self, *args, **kwargs):
        if self.nombre:
            self.nombre = normalize_amenity_name(self.nombre)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.nombre


def normalize_amenity_name(name):
    normalized = unicodedata.normalize("NFD", name.strip().upper())
    return "".join(char for char in normalized if unicodedata.category(char) != "Mn")


class Propiedad(models.Model):
    ESTADO_CHOICES = [
        ("disponible", "Disponible"),
        ("pausada", "Pausada"),
        ("inactiva", "Inactiva"),
    ]

    titulo = models.CharField(max_length=200)
    descripcion = models.TextField()
    calle = models.CharField(max_length=255, blank=True, default="")
    ubicacion = models.CharField(max_length=255, help_text="Ciudad donde se encuentra la propiedad.")
    precio_noche = models.DecimalField("Precio noche (Gs.)", max_digits=12, decimal_places=0)
    precio_fin_semana = models.DecimalField("Precio fin de semana (Gs.)", max_digits=12, decimal_places=0)
    tarifa_limpieza = models.DecimalField("Tarifa limpieza (Gs.)", max_digits=12, decimal_places=0)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default="disponible")
    id_anfitrion = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        related_name="propiedades",
        limit_choices_to={"rol": "anfitrion"},
    )
    amenities = models.ManyToManyField(
        Amenity,
        related_name="propiedades",
        blank=True,
    )

    class Meta:
        verbose_name = "Propiedad"
        verbose_name_plural = "Propiedades"

    def __str__(self):
        return self.titulo


class Reserva(models.Model):
    ESTADO_CHOICES = [
        ("pendiente", "Pendiente"),
        ("confirmada", "Confirmada"),
        ("cancelada", "Cancelada"),
        ("rechazada", "Rechazada"),
    ]

    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    cantidad_huespedes = models.IntegerField()
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default="pendiente")
    precio_total = models.DecimalField("Precio total (Gs.)", max_digits=12, decimal_places=0)
    id_huesped = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        related_name="reservas",
        limit_choices_to={"rol": "huesped"},
    )
    id_propiedad = models.ForeignKey(
        Propiedad,
        on_delete=models.CASCADE,
        related_name="reservas",
    )

    class Meta:
        verbose_name = "Reserva"
        verbose_name_plural = "Reservas"

    def __str__(self):
        return f"{self.id_propiedad} ({self.fecha_inicio} - {self.fecha_fin})"


class Disponibilidad(models.Model):
    ESTADO_CHOICES = [
        ("disponible", "Disponible"),
        ("bloqueada", "Bloqueada"),
        ("reservada", "Reservada"),
    ]

    fecha = models.DateField()
    fecha_inicio_reserva = models.DateField(blank=True, null=True)
    fecha_publicacion = models.DateTimeField(default=timezone.now)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default="disponible")
    id_propiedad = models.ForeignKey(
        Propiedad,
        on_delete=models.CASCADE,
        related_name="disponibilidades",
    )
    id_reserva = models.ForeignKey(
        Reserva,
        on_delete=models.SET_NULL,
        related_name="disponibilidades",
        blank=True,
        null=True,
    )

    class Meta:
        verbose_name = "Disponibilidad"
        verbose_name_plural = "Disponibilidades"
        unique_together = ("fecha", "id_propiedad")

    def __str__(self):
        return f"{self.fecha} - {self.get_estado_display()}"


class AgenteIAConfig(models.Model):
    nombre = models.CharField(max_length=100, default="Agente IA de Booking")
    descripcion = models.TextField(
        default=(
            "Asistente para huespedes y anfitriones. Consulta propiedades, amenities, "
            "resenas, disponibilidad y reservas usando datos reales del backend."
        )
    )
    system_prompt = models.TextField()
    endpoint_chat = models.CharField(max_length=150, default="/api/agent/chat/")
    endpoint_disponibilidad = models.CharField(max_length=150, default="/api/availability/")
    endpoint_reservas = models.CharField(max_length=150, default="/api/reservations/")
    endpoint_propiedades = models.CharField(max_length=150, default="/api/properties/")
    requiere_confirmacion_reserva = models.BooleanField(default=True)
    activo = models.BooleanField(default=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Agente IA"
        verbose_name_plural = "Agente IA"

    def __str__(self):
        return self.nombre


class PreguntarIA(AgenteIAConfig):
    class Meta:
        proxy = True
        verbose_name = "Preguntar a la IA"
        verbose_name_plural = "Preguntar a la IA"


class Notificacion(models.Model):
    mensaje = models.TextField()
    estado = models.CharField(max_length=20, default="pendiente")
    fecha = models.DateTimeField(default=timezone.now)
    id_usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    id_reserva = models.ForeignKey(Reserva, on_delete=models.CASCADE, blank=True, null=True)

    class Meta:
        verbose_name = "Notificacion"
        verbose_name_plural = "Notificaciones"


class Review(models.Model):
    calificacion = models.IntegerField()
    comentario = models.TextField()
    fecha = models.DateTimeField(default=timezone.now)
    id_usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    id_propiedad = models.ForeignKey(Propiedad, on_delete=models.CASCADE)
    id_reserva = models.OneToOneField(Reserva, on_delete=models.CASCADE)

    class Meta:
        verbose_name = "Reseña"
        verbose_name_plural = "Reseñas"
