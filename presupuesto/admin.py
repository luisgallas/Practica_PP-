from django.contrib import admin  # Importa el módulo de administración de Django.
from .models import Usuario, Propiedad, PropiedadAmenity, Disponibilidad, Reserva, Notificacion, Review, Amenity  # Importa los modelos de la app presupuesto.


@admin.register(Usuario)  # Registra el modelo Usuario en el panel de administración de Django.
class UsuarioAdmin(admin.ModelAdmin):  # Define la configuración de admin para el modelo Usuario.
    list_display = ('username', 'get_full_name', 'email', 'telefono', 'rol', 'fecha_registro')  # Campos que se muestran en la lista de usuarios.
    list_filter = ('rol', 'fecha_registro')  # Filtros disponibles en la barra lateral para el listado.
    search_fields = ('username', 'email', 'first_name', 'last_name', 'telefono')  # Campos que se pueden buscar.
    fieldsets = (  # Organiza los campos del formulario de admin en secciones.
        ('Información Personal', {'fields': ('username', 'email', 'first_name', 'last_name', 'telefono')}),  # Grupo de campos personales.
        ('Roles y Permisos', {'fields': ('rol', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),  # Grupo de roles y permisos.
        ('Fechas', {'fields': ('last_login', 'date_joined', 'fecha_registro')}),  # Grupo de campos de tiempo.
    )
    readonly_fields = ('fecha_registro', 'last_login', 'date_joined')  # Campos que no pueden editarse desde el admin.


@admin.register(Amenity)  # Registra el modelo Amenity en el admin.
class AmenityAdmin(admin.ModelAdmin):  # Define la configuración de admin para Amenity.
    list_display = ('nombre', 'id')  # Muestra el nombre y el id en la lista.
    search_fields = ('nombre',)  # Permite buscar amenities por nombre.
    ordering = ('nombre',)  # Ordena la lista de amenities por nombre.


@admin.register(Propiedad)  # Registra el modelo Propiedad en el admin.
class PropiedadAdmin(admin.ModelAdmin):  # Define la configuración de admin para Propiedad.
    list_display = ('titulo', 'id_anfitrion', 'ubicacion', 'precio_noche', 'estado')  # Campos visibles en la lista de propiedades.
    list_filter = ('estado', 'id_anfitrion')  # Filtros para estado y anfitrión.
    search_fields = ('titulo', 'descripcion', 'ubicacion')  # Campos que se pueden buscar.
    fieldsets = (  # Organiza los campos del formulario de admin en secciones.
        ('Información Básica', {'fields': ('titulo', 'descripcion', 'ubicacion', 'id_anfitrion')}),  # Grupo básico de campos.
        ('Precios', {'fields': ('precio_noche', 'precio_fin_semana', 'tarifa_limpieza')}),  # Grupo de precios.
        ('Estado', {'fields': ('estado',)}),  # Grupo de estado de la propiedad.
    )


@admin.register(PropiedadAmenity)  # Registra el modelo PropiedadAmenity en el admin.
class PropiedadAmenityAdmin(admin.ModelAdmin):  # Define la configuración de admin para PropiedadAmenity.
    list_display = ('id_propiedad', 'id_amenity')  # Campos mostrados en la lista.
    list_filter = ('id_propiedad', 'id_amenity')  # Filtros para las relaciones entre propiedad y amenity.
    search_fields = ('id_propiedad__titulo', 'id_amenity__nombre')  # Permite buscar por título de propiedad y nombre de amenity.


@admin.register(Disponibilidad)  # Registra el modelo Disponibilidad en el admin.
class DisponibilidadAdmin(admin.ModelAdmin):  # Define la configuración de admin para Disponibilidad.
    list_display = ('id_propiedad', 'fecha', 'estado')  # Muestra propiedad, fecha y estado.
    list_filter = ('estado', 'fecha', 'id_propiedad')  # Filtros para estado, fecha y propiedad.
    search_fields = ('id_propiedad__titulo',)  # Permite buscar disponibilidades por título de propiedad.
    date_hierarchy = 'fecha'  # Activa navegación por fecha en el admin.


@admin.register(Reserva)  # Registra el modelo Reserva en el admin.
class ReservaAdmin(admin.ModelAdmin):  # Define la configuración de admin para Reserva.
    list_display = ('id', 'id_propiedad', 'id_huesped', 'fecha_inicio', 'fecha_fin', 'estado', 'precio_total')  # Campos mostrados en la lista de reservas.
    list_filter = ('estado', 'fecha_inicio', 'id_propiedad')  # Filtros para estado, fecha de inicio y propiedad.
    search_fields = ('id_huesped__username', 'id_propiedad__titulo')  # Permite buscar reservas por usuario o propiedad.
    fieldsets = (  # Organiza los campos del formulario de admin en secciones.
        ('Información de Reserva', {'fields': ('id_propiedad', 'id_huesped', 'estado')}),  # Grupo de información principal.
        ('Fechas', {'fields': ('fecha_inicio', 'fecha_fin')}),  # Grupo de fechas.
        ('Huéspedes y Precios', {'fields': ('cantidad_huespedes', 'precio_total')}),  # Grupo de cantidad y precio.
    )
    readonly_fields = ('precio_total',)  # Precio total no editable desde el admin.
    date_hierarchy = 'fecha_inicio'  # Navegación por fecha de inicio.


@admin.register(Notificacion)  # Registra el modelo Notificacion en el admin.
class NotificacionAdmin(admin.ModelAdmin):  # Define la configuración de admin para Notificacion.
    list_display = ('id_usuario', 'id_reserva', 'estado', 'fecha')  # Muestra usuario, reserva, estado y fecha.
    list_filter = ('estado', 'fecha')  # Filtros por estado y fecha.
    search_fields = ('id_usuario__username', 'mensaje')  # Permite buscar notificaciones por usuario o mensaje.
    readonly_fields = ('fecha',)  # Fecha de creación no editable.


@admin.register(Review)  # Registra el modelo Review en el admin.
class ReviewAdmin(admin.ModelAdmin):  # Define la configuración de admin para Review.
    list_display = ('id_propiedad', 'id_usuario', 'calificacion', 'fecha')  # Muestra propiedad, usuario, calificación y fecha.
    list_filter = ('calificacion', 'fecha')  # Filtros para calificación y fecha.
    search_fields = ('id_usuario__username', 'id_propiedad__titulo', 'comentario')  # Permite buscar reseñas por usuario, propiedad o comentario.
    readonly_fields = ('fecha',)  # Fecha no se puede editar.
