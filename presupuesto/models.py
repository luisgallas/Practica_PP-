from django.db import models  # Importa nombres concretos desde un módulo.
from django.contrib.auth.models import AbstractUser  # Importa nombres concretos desde un módulo.


class Usuario(AbstractUser):  # Define una clase Python.
    """Modelo de Usuario - extiende AbstractUser de Django"""
    ROL_CHOICES = [
        ('anfitrion', 'Anfitrión'),
        ('huesped', 'Huésped'),
        ('admin', 'Administrador'),
    ]
    
    rol = models.CharField(max_length=20, choices=ROL_CHOICES, default='huesped')  # Define un campo de texto corto en el modelo.
    telefono = models.CharField(max_length=20, blank=True, null=True)  # Define un campo de texto corto en el modelo.
    fecha_registro = models.DateTimeField(auto_now_add=True)  # Define un campo que almacena fecha y hora.
    
    groups = models.ManyToManyField(  # Define una relación de muchos a muchos entre modelos.
        'auth.Group',
        blank=True,
        help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.',
        related_name='usuario_groups',
        verbose_name='groups',  # Define el nombre legible del modelo en singular/plural.
    )
    user_permissions = models.ManyToManyField(  # Define una relación de muchos a muchos entre modelos.
        'auth.Permission',
        blank=True,
        help_text='Specific permissions for this user.',
        related_name='usuario_permissions',
        verbose_name='user permissions',  # Define el nombre legible del modelo en singular/plural.
    )
    
    class Meta:  # Define una clase Python.
        verbose_name = 'Usuario'  # Define el nombre legible del modelo en singular/plural.
        verbose_name_plural = 'Usuarios'  # Define el nombre legible del modelo en singular/plural.
        ordering = ['-fecha_registro']  # Define el orden por defecto de los registros.
    
    def __str__(self):  # Define una función / método.
        return f"{self.get_full_name() or self.username} ({self.get_rol_display()})"  # Devuelve un valor desde la función.


class Amenity(models.Model):  # Define una clase Python.
    """Modelo de Amenidades (comodidades)"""
    nombre = models.CharField(max_length=100, unique=True)  # Define un campo de texto corto en el modelo.
    
    class Meta:  # Define una clase Python.
        verbose_name = 'Amenity'  # Define el nombre legible del modelo en singular/plural.
        verbose_name_plural = 'Amenities'  # Define el nombre legible del modelo en singular/plural.
        ordering = ['nombre']  # Define el orden por defecto de los registros.
    
    def __str__(self):  # Define una función / método.
        return self.nombre  # Devuelve un valor desde la función.


class Propiedad(models.Model):  # Define una clase Python.
    """Modelo de Propiedad"""
    ESTADO_CHOICES = [
        ('disponible', 'Disponible'),
        ('ocupada', 'Ocupada'),
        ('mantenimiento', 'Mantenimiento'),
        ('retirada', 'Retirada'),
    ]
    
    id_anfitrion = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='propiedades')  # Define una relación de clave foránea entre modelos.
    titulo = models.CharField(max_length=200)  # Define un campo de texto corto en el modelo.
    descripcion = models.TextField()  # Define un campo de texto largo en el modelo.
    ubicacion = models.CharField(max_length=255)  # Define un campo de texto corto en el modelo.
    precio_noche = models.DecimalField(max_digits=10, decimal_places=2)  # Define un campo numérico decimal para precios u importes.
    precio_fin_semana = models.DecimalField(max_digits=10, decimal_places=2)  # Define un campo numérico decimal para precios u importes.
    tarifa_limpieza = models.DecimalField(max_digits=10, decimal_places=2, default=0)  # Define un campo numérico decimal para precios u importes.
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='disponible')  # Define un campo de texto corto en el modelo.
    amenities = models.ManyToManyField(Amenity, through='PropiedadAmenity')  # Define una relación de muchos a muchos entre modelos.
    
    class Meta:  # Define una clase Python.
        verbose_name = 'Propiedad'  # Define el nombre legible del modelo en singular/plural.
        verbose_name_plural = 'Propiedades'  # Define el nombre legible del modelo en singular/plural.
        ordering = ['-id']  # Define el orden por defecto de los registros.
    
    def __str__(self):  # Define una función / método.
        return f"{self.titulo} - {self.ubicacion}"  # Devuelve un valor desde la función.


class PropiedadAmenity(models.Model):  # Define una clase Python.
    """Modelo de relación entre Propiedad y Amenity"""
    id_propiedad = models.ForeignKey(Propiedad, on_delete=models.CASCADE)  # Define una relación de clave foránea entre modelos.
    id_amenity = models.ForeignKey(Amenity, on_delete=models.CASCADE)  # Define una relación de clave foránea entre modelos.
    
    class Meta:  # Define una clase Python.
        verbose_name = 'Propiedad Amenity'  # Define el nombre legible del modelo en singular/plural.
        verbose_name_plural = 'Propiedades Amenities'  # Define el nombre legible del modelo en singular/plural.
        unique_together = ('id_propiedad', 'id_amenity')
    
    def __str__(self):  # Define una función / método.
        return f"{self.id_propiedad.titulo} - {self.id_amenity.nombre}"  # Devuelve un valor desde la función.


class Disponibilidad(models.Model):  # Define una clase Python.
    """Modelo de Disponibilidad de Propiedad"""
    ESTADO_CHOICES = [
        ('disponible', 'Disponible'),
        ('ocupada', 'Ocupada'),
        ('bloqueada', 'Bloqueada'),
    ]
    
    id_propiedad = models.ForeignKey(Propiedad, on_delete=models.CASCADE, related_name='disponibilidades')  # Define una relación de clave foránea entre modelos.
    fecha = models.DateField()  # Define un campo que almacena una fecha.
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='disponible')  # Define un campo de texto corto en el modelo.
    
    class Meta:  # Define una clase Python.
        verbose_name = 'Disponibilidad'  # Define el nombre legible del modelo en singular/plural.
        verbose_name_plural = 'Disponibilidades'  # Define el nombre legible del modelo en singular/plural.
        unique_together = ('id_propiedad', 'fecha')
        ordering = ['fecha']  # Define el orden por defecto de los registros.
    
    def __str__(self):  # Define una función / método.
        return f"{self.id_propiedad.titulo} - {self.fecha} ({self.get_estado_display()})"  # Devuelve un valor desde la función.


class Reserva(models.Model):  # Define una clase Python.
    """Modelo de Reserva"""
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('confirmada', 'Confirmada'),
        ('cancelada', 'Cancelada'),
        ('completada', 'Completada'),
    ]
    
    id_propiedad = models.ForeignKey(Propiedad, on_delete=models.CASCADE, related_name='reservas')  # Define una relación de clave foránea entre modelos.
    id_huesped = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='reservas')  # Define una relación de clave foránea entre modelos.
    fecha_inicio = models.DateField()  # Define un campo que almacena una fecha.
    fecha_fin = models.DateField()  # Define un campo que almacena una fecha.
    cantidad_huespedes = models.IntegerField()  # Define un campo entero.
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='pendiente')  # Define un campo de texto corto en el modelo.
    precio_total = models.DecimalField(max_digits=12, decimal_places=2)  # Define un campo numérico decimal para precios u importes.
    
    class Meta:  # Define una clase Python.
        verbose_name = 'Reserva'  # Define el nombre legible del modelo en singular/plural.
        verbose_name_plural = 'Reservas'  # Define el nombre legible del modelo en singular/plural.
        ordering = ['-fecha_inicio']  # Define el orden por defecto de los registros.
    
    def __str__(self):  # Define una función / método.
        return f"Reserva #{self.id} - {self.id_propiedad.titulo} ({self.get_estado_display()})"


class Notificacion(models.Model):  # Define una clase Python.
    """Modelo de Notificación"""
    ESTADO_CHOICES = [
        ('no_leida', 'No Leída'),
        ('leida', 'Leída'),
        ('archivada', 'Archivada'),
    ]
    
    id_usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='notificaciones')  # Define una relación de clave foránea entre modelos.
    id_reserva = models.ForeignKey(Reserva, on_delete=models.CASCADE, null=True, blank=True, related_name='notificaciones')  # Define una relación de clave foránea entre modelos.
    mensaje = models.TextField()  # Define un campo de texto largo en el modelo.
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='no_leida')  # Define un campo de texto corto en el modelo.
    fecha = models.DateTimeField(auto_now_add=True)  # Define un campo que almacena fecha y hora.
    
    class Meta:  # Define una clase Python.
        verbose_name = 'Notificación'  # Define el nombre legible del modelo en singular/plural.
        verbose_name_plural = 'Notificaciones'  # Define el nombre legible del modelo en singular/plural.
        ordering = ['-fecha']  # Define el orden por defecto de los registros.
    
    def __str__(self):  # Define una función / método.
        return f"Notificación para {self.id_usuario.get_full_name()} - {self.get_estado_display()}"  # Devuelve un valor desde la función.


class Review(models.Model):  # Define una clase Python.
    """Modelo de Reseña/Review"""
    CALIFICACION_CHOICES = [
        (1, '⭐ Muy Malo'),
        (2, '⭐⭐ Malo'),
        (3, '⭐⭐⭐ Regular'),
        (4, '⭐⭐⭐⭐ Bueno'),
        (5, '⭐⭐⭐⭐⭐ Excelente'),
    ]
    
    id_reserva = models.OneToOneField(Reserva, on_delete=models.CASCADE, related_name='review')  # Define una relación uno a uno entre modelos.
    id_propiedad = models.ForeignKey(Propiedad, on_delete=models.CASCADE, related_name='reviews')  # Define una relación de clave foránea entre modelos.
    id_usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='reviews')  # Define una relación de clave foránea entre modelos.
    calificacion = models.IntegerField(choices=CALIFICACION_CHOICES)  # Define un campo entero.
    comentario = models.TextField()  # Define un campo de texto largo en el modelo.
    fecha = models.DateTimeField(auto_now_add=True)  # Define un campo que almacena fecha y hora.
    
    class Meta:  # Define una clase Python.
        verbose_name = 'Review'  # Define el nombre legible del modelo en singular/plural.
        verbose_name_plural = 'Reviews'  # Define el nombre legible del modelo en singular/plural.
        ordering = ['-fecha']  # Define el orden por defecto de los registros.
        unique_together = ('id_reserva', 'id_propiedad')
    
    def __str__(self):  # Define una función / método.
        return f"Review {self.get_calificacion_display()} - {self.id_propiedad.titulo}"  # Devuelve un valor desde la función.
