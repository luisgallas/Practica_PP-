from django.db import models
from django.contrib.auth.models import AbstractUser


class Usuario(AbstractUser):
    """Modelo de Usuario - extiende AbstractUser de Django"""
    ROL_CHOICES = [
        ('anfitrion', 'Anfitrión'),
        ('huesped', 'Huésped'),
        ('admin', 'Administrador'),
    ]
    
    rol = models.CharField(max_length=20, choices=ROL_CHOICES, default='huesped')
    telefono = models.CharField(max_length=20, blank=True, null=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'
        ordering = ['-fecha_registro']
    
    def __str__(self):
        return f"{self.get_full_name()} ({self.get_rol_display()})"


class Amenity(models.Model):
    """Modelo de Amenidades (comodidades)"""
    nombre = models.CharField(max_length=100, unique=True)
    
    class Meta:
        verbose_name = 'Amenity'
        verbose_name_plural = 'Amenities'
        ordering = ['nombre']
    
    def __str__(self):
        return self.nombre


class Propiedad(models.Model):
    """Modelo de Propiedad"""
    ESTADO_CHOICES = [
        ('disponible', 'Disponible'),
        ('ocupada', 'Ocupada'),
        ('mantenimiento', 'Mantenimiento'),
        ('retirada', 'Retirada'),
    ]
    
    id_anfitrion = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='propiedades')
    titulo = models.CharField(max_length=200)
    descripcion = models.TextField()
    ubicacion = models.CharField(max_length=255)
    precio_noche = models.DecimalField(max_digits=10, decimal_places=2)
    precio_fin_semana = models.DecimalField(max_digits=10, decimal_places=2)
    tarifa_limpieza = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='disponible')
    amenities = models.ManyToManyField(Amenity, through='PropiedadAmenity')
    
    class Meta:
        verbose_name = 'Propiedad'
        verbose_name_plural = 'Propiedades'
        ordering = ['-id']
    
    def __str__(self):
        return f"{self.titulo} - {self.ubicacion}"


class PropiedadAmenity(models.Model):
    """Modelo de relación entre Propiedad y Amenity"""
    id_propiedad = models.ForeignKey(Propiedad, on_delete=models.CASCADE)
    id_amenity = models.ForeignKey(Amenity, on_delete=models.CASCADE)
    
    class Meta:
        verbose_name = 'Propiedad Amenity'
        verbose_name_plural = 'Propiedades Amenities'
        unique_together = ('id_propiedad', 'id_amenity')
    
    def __str__(self):
        return f"{self.id_propiedad.titulo} - {self.id_amenity.nombre}"


class Disponibilidad(models.Model):
    """Modelo de Disponibilidad de Propiedad"""
    ESTADO_CHOICES = [
        ('disponible', 'Disponible'),
        ('ocupada', 'Ocupada'),
        ('bloqueada', 'Bloqueada'),
    ]
    
    id_propiedad = models.ForeignKey(Propiedad, on_delete=models.CASCADE, related_name='disponibilidades')
    fecha = models.DateField()
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='disponible')
    
    class Meta:
        verbose_name = 'Disponibilidad'
        verbose_name_plural = 'Disponibilidades'
        unique_together = ('id_propiedad', 'fecha')
        ordering = ['fecha']
    
    def __str__(self):
        return f"{self.id_propiedad.titulo} - {self.fecha} ({self.get_estado_display()})"


class Reserva(models.Model):
    """Modelo de Reserva"""
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('confirmada', 'Confirmada'),
        ('cancelada', 'Cancelada'),
        ('completada', 'Completada'),
    ]
    
    id_propiedad = models.ForeignKey(Propiedad, on_delete=models.CASCADE, related_name='reservas')
    id_huesped = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='reservas')
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    cantidad_huespedes = models.IntegerField()
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='pendiente')
    precio_total = models.DecimalField(max_digits=12, decimal_places=2)
    
    class Meta:
        verbose_name = 'Reserva'
        verbose_name_plural = 'Reservas'
        ordering = ['-fecha_inicio']
    
    def __str__(self):
        return f"Reserva #{self.id} - {self.id_propiedad.titulo} ({self.get_estado_display()})"


class Notificacion(models.Model):
    """Modelo de Notificación"""
    ESTADO_CHOICES = [
        ('no_leida', 'No Leída'),
        ('leida', 'Leída'),
        ('archivada', 'Archivada'),
    ]
    
    id_usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='notificaciones')
    id_reserva = models.ForeignKey(Reserva, on_delete=models.CASCADE, null=True, blank=True, related_name='notificaciones')
    mensaje = models.TextField()
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='no_leida')
    fecha = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Notificación'
        verbose_name_plural = 'Notificaciones'
        ordering = ['-fecha']
    
    def __str__(self):
        return f"Notificación para {self.id_usuario.get_full_name()} - {self.get_estado_display()}"


class Review(models.Model):
    """Modelo de Reseña/Review"""
    CALIFICACION_CHOICES = [
        (1, '⭐ Muy Malo'),
        (2, '⭐⭐ Malo'),
        (3, '⭐⭐⭐ Regular'),
        (4, '⭐⭐⭐⭐ Bueno'),
        (5, '⭐⭐⭐⭐⭐ Excelente'),
    ]
    
    id_reserva = models.OneToOneField(Reserva, on_delete=models.CASCADE, related_name='review')
    id_propiedad = models.ForeignKey(Propiedad, on_delete=models.CASCADE, related_name='reviews')
    id_usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='reviews')
    calificacion = models.IntegerField(choices=CALIFICACION_CHOICES)
    comentario = models.TextField()
    fecha = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Review'
        verbose_name_plural = 'Reviews'
        ordering = ['-fecha']
        unique_together = ('id_reserva', 'id_propiedad')
    
    def __str__(self):
        return f"Review {self.get_calificacion_display()} - {self.id_propiedad.titulo}"
