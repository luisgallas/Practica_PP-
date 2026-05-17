from django.contrib import admin
from .models import Usuario, Propiedad, PropiedadAmenity, Disponibilidad, Reserva, Notificacion, Review, Amenity


@admin.register(Usuario)
class UsuarioAdmin(admin.ModelAdmin):
    list_display = ('username', 'get_full_name', 'email', 'rol', 'fecha_registro')
    list_filter = ('rol', 'fecha_registro')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    fieldsets = (
        ('Información Personal', {'fields': ('username', 'email', 'first_name', 'last_name', 'telefono')}),
        ('Roles y Permisos', {'fields': ('rol', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Fechas', {'fields': ('last_login', 'date_joined', 'fecha_registro')}),
    )
    readonly_fields = ('fecha_registro', 'last_login', 'date_joined')


@admin.register(Amenity)
class AmenityAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'id')
    search_fields = ('nombre',)
    ordering = ('nombre',)


@admin.register(Propiedad)
class PropiedadAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'id_anfitrion', 'ubicacion', 'precio_noche', 'estado')
    list_filter = ('estado', 'id_anfitrion')
    search_fields = ('titulo', 'descripcion', 'ubicacion')
    fieldsets = (
        ('Información Básica', {'fields': ('titulo', 'descripcion', 'ubicacion', 'id_anfitrion')}),
        ('Precios', {'fields': ('precio_noche', 'precio_fin_semana', 'tarifa_limpieza')}),
        ('Estado', {'fields': ('estado',)}),
    )


@admin.register(PropiedadAmenity)
class PropiedadAmenityAdmin(admin.ModelAdmin):
    list_display = ('id_propiedad', 'id_amenity')
    list_filter = ('id_propiedad', 'id_amenity')
    search_fields = ('id_propiedad__titulo', 'id_amenity__nombre')


@admin.register(Disponibilidad)
class DisponibilidadAdmin(admin.ModelAdmin):
    list_display = ('id_propiedad', 'fecha', 'estado')
    list_filter = ('estado', 'fecha', 'id_propiedad')
    search_fields = ('id_propiedad__titulo',)
    date_hierarchy = 'fecha'


@admin.register(Reserva)
class ReservaAdmin(admin.ModelAdmin):
    list_display = ('id', 'id_propiedad', 'id_huesped', 'fecha_inicio', 'fecha_fin', 'estado', 'precio_total')
    list_filter = ('estado', 'fecha_inicio', 'id_propiedad')
    search_fields = ('id_huesped__username', 'id_propiedad__titulo')
    fieldsets = (
        ('Información de Reserva', {'fields': ('id_propiedad', 'id_huesped', 'estado')}),
        ('Fechas', {'fields': ('fecha_inicio', 'fecha_fin')}),
        ('Huéspedes y Precios', {'fields': ('cantidad_huespedes', 'precio_total')}),
    )
    readonly_fields = ('precio_total',)
    date_hierarchy = 'fecha_inicio'


@admin.register(Notificacion)
class NotificacionAdmin(admin.ModelAdmin):
    list_display = ('id_usuario', 'id_reserva', 'estado', 'fecha')
    list_filter = ('estado', 'fecha')
    search_fields = ('id_usuario__username', 'mensaje')
    readonly_fields = ('fecha',)


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('id_propiedad', 'id_usuario', 'calificacion', 'fecha')
    list_filter = ('calificacion', 'fecha')
    search_fields = ('id_usuario__username', 'id_propiedad__titulo', 'comentario')
    readonly_fields = ('fecha',)
