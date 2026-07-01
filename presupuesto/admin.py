import json

from django import forms
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.shortcuts import render
from django.utils import timezone
from django.utils.html import format_html

from . import agent
from .models import AgenteIAConfig, Amenity, Disponibilidad, HistorialPropiedadVisitada, Notificacion, PreguntarIA, Propiedad, PropiedadFoto, Reserva, Review, Usuario
from .services import (
    BLOCKING_AVAILABILITY_STATES,
    BLOCKING_RESERVATION_STATES,
    calculate_price,
    sync_reservation_availability,
    update_reservation_status,
)


ADMIN_MODEL_ORDER = {
    "Preguntar a la IA": 0,
    "Amenities": 1,
    "Notificaciones": 2,
    "Propiedades": 3,
    "Reservas": 4,
    "Reseñas": 5,
    "Usuarios": 6,
    "Agente IA": 7,
}


original_get_app_list = admin.site.get_app_list


def ordered_get_app_list(request, app_label=None):
    app_list = original_get_app_list(request, app_label)
    for app in app_list:
        if app["app_label"] == "presupuesto":
            app["models"].sort(
                key=lambda model: ADMIN_MODEL_ORDER.get(model["name"], 99)
            )
    return app_list


admin.site.get_app_list = ordered_get_app_list


def is_admin_role(user):
    return user.is_superuser or getattr(user, "rol", None) == "admin"


class RoleAdminMixin:
    allowed_roles = ("admin",)
    add_roles = ("admin",)
    change_roles = ("admin",)
    delete_roles = ("admin",)

    def role_allowed(self, request, roles=None):
        roles = roles or self.allowed_roles
        return request.user.is_active and (is_admin_role(request.user) or request.user.rol in roles)

    def has_module_permission(self, request):
        return self.role_allowed(request)

    def has_view_permission(self, request, obj=None):
        return self.role_allowed(request)

    def has_add_permission(self, request):
        return self.role_allowed(request, self.add_roles)

    def has_change_permission(self, request, obj=None):
        return self.role_allowed(request, self.change_roles)

    def has_delete_permission(self, request, obj=None):
        return self.role_allowed(request, self.delete_roles)

    def get_model_perms(self, request):
        return {
            "view": self.has_view_permission(request),
            "add": self.has_add_permission(request),
            "change": self.has_change_permission(request),
            "delete": self.has_delete_permission(request),
        }


@admin.register(Usuario)
class UsuarioAdmin(RoleAdminMixin, UserAdmin):
    allowed_roles = ("admin",)
    fieldsets = UserAdmin.fieldsets + (
        ("Datos de booking", {"fields": ("rol", "telefono", "fecha_registro")}),
    )
    list_display = ("username", "email", "rol", "is_staff", "is_active")


@admin.register(Amenity)
class AmenityAdmin(RoleAdminMixin, admin.ModelAdmin):
    allowed_roles = ("admin", "anfitrion")
    add_roles = ("admin", "anfitrion")
    change_roles = ("admin", "anfitrion")
    delete_roles = ("admin",)
    search_fields = ("nombre",)


@admin.register(Notificacion)
class NotificacionAdmin(RoleAdminMixin, admin.ModelAdmin):
    allowed_roles = ("admin", "anfitrion", "huesped")
    add_roles = ("admin",)
    change_roles = ("admin",)
    delete_roles = ("admin",)
    list_display = ("id_usuario", "mensaje", "estado", "fecha")
    readonly_fields = ("mensaje", "estado", "fecha", "id_usuario", "id_reserva")

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        if is_admin_role(request.user):
            return queryset
        return queryset.filter(id_usuario=request.user)


@admin.register(HistorialPropiedadVisitada)
class HistorialPropiedadVisitadaAdmin(RoleAdminMixin, admin.ModelAdmin):
    allowed_roles = ("admin", "huesped")
    add_roles = ("admin",)
    change_roles = ("admin",)
    delete_roles = ("admin",)
    list_display = ("id_usuario", "id_propiedad", "fecha_visita", "cantidad_visitas")
    readonly_fields = ("id_usuario", "id_propiedad", "fecha_visita", "cantidad_visitas")

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        if is_admin_role(request.user):
            return queryset
        return queryset.filter(id_usuario=request.user)


class PropiedadFotoInline(admin.TabularInline):
    model = PropiedadFoto
    fields = ("foto", "descripcion", "es_portada", "fecha_publicacion")
    readonly_fields = ("fecha_publicacion",)
    extra = 1


@admin.action(description="Eliminar seleccionado")
def eliminar_propiedades_seleccionadas(modeladmin, request, queryset):
    total = queryset.count()
    queryset.delete()
    modeladmin.message_user(request, f"Se eliminaron {total} propiedad(es) seleccionada(s).")


@admin.register(Propiedad)
class PropiedadAdmin(RoleAdminMixin, admin.ModelAdmin):
    allowed_roles = ("admin", "anfitrion", "huesped")
    add_roles = ("admin", "anfitrion")
    change_roles = ("admin", "anfitrion")
    delete_roles = ("admin", "anfitrion")
    change_list_template = "admin/presupuesto/propiedad/change_list.html"
    list_display = (
        "titulo",
        "ubicacion",
        "tipo_alojamiento",
        "capacidad_maxima_huespedes",
        "estado",
        "precio_noche_guaranies",
    )
    search_fields = ("titulo", "ubicacion", "calle", "descripcion")
    list_filter = ("estado", "tipo_alojamiento", "politica_cancelacion", "ubicacion", "amenities", "permite_mascotas", "permite_fumar", "permite_fiestas")
    inlines = [PropiedadFotoInline]
    actions = [eliminar_propiedades_seleccionadas]
    actions_on_top = True
    actions_on_bottom = True

    @admin.display(description="Precio noche")
    def precio_noche_guaranies(self, obj):
        return f"Gs. {int(obj.precio_noche):,}".replace(",", ".")

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        if is_admin_role(request.user):
            return queryset
        if request.user.rol == "huesped":
            return queryset.filter(estado="disponible")
        return queryset.filter(id_anfitrion=request.user)

    def get_readonly_fields(self, request, obj=None):
        if request.user.rol == "huesped":
            return [field.name for field in self.model._meta.fields] + ["amenities"]
        return super().get_readonly_fields(request, obj)

    def get_exclude(self, request, obj=None):
        if getattr(request.user, "rol", None) == "anfitrion":
            return ("id_anfitrion",)
        return super().get_exclude(request, obj)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "id_anfitrion" and not is_admin_role(request.user):
            kwargs["queryset"] = Usuario.objects.filter(id=request.user.id)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def save_model(self, request, obj, form, change):
        if request.user.rol == "anfitrion":
            obj.id_anfitrion = request.user
        super().save_model(request, obj, form, change)


class UsuarioContextChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return f"{obj.username} - {obj.get_rol_display()}"


class AgenteIATestForm(forms.Form):
    usuario = UsuarioContextChoiceField(
        queryset=Usuario.objects.none(),
        required=False,
        label="Preguntar como",
        help_text="Admin ve datos globales, anfitrion ve sus reservas, huesped puede reservar.",
    )
    message = forms.CharField(
        label="Pregunta para la IA",
        widget=forms.Textarea(attrs={"rows": 4, "style": "width: 80%;"}),
    )
    confirm = forms.BooleanField(
        required=False,
        label="Confirmar accion pendiente",
        help_text="Usar solo cuando la IA ya pidio confirmacion para crear una reserva.",
    )
    pending_action = forms.CharField(required=False, widget=forms.HiddenInput)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["usuario"].queryset = Usuario.objects.filter(
            rol__in=["admin", "anfitrion", "huesped"]
        ).order_by("rol", "username")


@admin.register(AgenteIAConfig)
class AgenteIAConfigAdmin(RoleAdminMixin, admin.ModelAdmin):
    allowed_roles = ("admin",)
    list_display = (
        "nombre",
        "que_hace_resumen",
        "endpoint_chat",
        "requiere_confirmacion_reserva",
        "activo",
    )
    readonly_fields = (
        "nombre",
        "descripcion",
        "que_hace",
        "system_prompt",
        "conexion_backend",
        "endpoint_chat",
        "endpoint_disponibilidad",
        "endpoint_reservas",
        "endpoint_propiedades",
        "requiere_confirmacion_reserva",
        "activo",
        "fecha_actualizacion",
    )
    fieldsets = (
        ("Que hace la IA", {"fields": ("nombre", "descripcion", "que_hace")}),
        ("Rol claro del agente", {"fields": ("system_prompt",)}),
        (
            "Conexion real con el backend",
            {
                "fields": (
                    "conexion_backend",
                    "endpoint_chat",
                    "endpoint_disponibilidad",
                    "endpoint_reservas",
                    "endpoint_propiedades",
                )
            },
        ),
        ("Reglas", {"fields": ("requiere_confirmacion_reserva", "activo", "fecha_actualizacion")}),
    )

    def has_add_permission(self, request):
        return is_admin_role(request.user) and not AgenteIAConfig.objects.exists()

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    @admin.display(description="Que hace")
    def que_hace_resumen(self, obj):
        return "Responde a administradores, anfitriones y huespedes usando datos reales del backend"

    @admin.display(description="Que puede hacer la IA")
    def que_hace(self, obj):
        return format_html(
            "<ul>"
            "<li>Consultar propiedades disponibles por fecha y cantidad de personas.</li>"
            "<li>Responder que amenities tiene una propiedad y si acepta mascotas.</li>"
            "<li>Preparar una reserva y pedir confirmacion antes de crearla.</li>"
            "<li>Permitir al administrador consultar reservas globales del sistema.</li>"
            "<li>Ayudar al anfitrion a revisar reservas del mes o pendientes.</li>"
            "<li>Consultar resenas reales de una propiedad.</li>"
            "</ul>"
        )

    @admin.display(description="Como se conecta")
    def conexion_backend(self, obj):
        return format_html(
            "<p>El agente conversa por <strong>{}</strong> y desde ahi consulta servicios reales del backend.</p>"
            "<ul>"
            "<li><strong>{}</strong>: disponibilidad y precio estimado.</li>"
            "<li><strong>{}</strong>: listar o crear reservas.</li>"
            "<li><strong>{}</strong>: propiedades y amenities.</li>"
            "</ul>",
            obj.endpoint_chat,
            obj.endpoint_disponibilidad,
            obj.endpoint_reservas,
            obj.endpoint_propiedades,
        )


@admin.register(PreguntarIA)
class PreguntarIAAdmin(RoleAdminMixin, admin.ModelAdmin):
    allowed_roles = ("admin", "anfitrion", "huesped")
    add_roles = ()
    change_roles = ()
    delete_roles = ()

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def changelist_view(self, request, extra_context=None):
        result = None
        result_json = None
        pending_action_json = ""

        initial = {
            "message": "Hay reservas pendientes de confirmar?",
            "usuario": Usuario.objects.filter(rol="anfitrion").values_list("id", flat=True).first(),
        }

        if request.method == "POST":
            form = AgenteIATestForm(request.POST)
            if form.is_valid():
                selected_user = form.cleaned_data["usuario"]
                payload = {"message": form.cleaned_data["message"]}

                if selected_user:
                    payload["user_id"] = selected_user.id
                if form.cleaned_data["confirm"]:
                    payload["confirm"] = True

                raw_pending_action = form.cleaned_data.get("pending_action")
                if raw_pending_action:
                    try:
                        payload["pending_action"] = json.loads(raw_pending_action)
                    except json.JSONDecodeError:
                        payload["pending_action"] = {}

                result = agent.chat(payload)
                result_json = json.dumps(result, ensure_ascii=False, indent=2, default=str)

                if result.get("pending_action"):
                    pending_action_json = json.dumps(result["pending_action"], ensure_ascii=False)
                    form = AgenteIATestForm(
                        initial={
                            "usuario": selected_user.id if selected_user else None,
                            "message": "confirmo",
                            "pending_action": pending_action_json,
                        }
                    )
                elif result.get("intent") == "create_reservation_confirmed":
                    form = AgenteIATestForm(
                        initial={
                            "usuario": selected_user.id if selected_user else None,
                            "message": "",
                        }
                    )
        else:
            form = AgenteIATestForm(initial=initial)

        context = {
            **self.admin_site.each_context(request),
            "title": "Preguntar a la IA",
            "form": form,
            "result": result,
            "result_json": result_json,
            "pending_action_json": pending_action_json,
        }
        return render(request, "admin/presupuesto/agenteia_test.html", context)


class DisponibilidadReservaInline(admin.TabularInline):
    model = Disponibilidad
    verbose_name = "Fecha reservada"
    verbose_name_plural = "Fechas reservadas por esta reserva"
    fields = ("fecha", "estado", "inicio_de_reserva", "publicada_el")
    readonly_fields = ("fecha", "estado", "inicio_de_reserva", "publicada_el")
    extra = 0
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False

    @admin.display(description="Inicio de reserva")
    def inicio_de_reserva(self, obj):
        return obj.fecha_inicio_reserva

    @admin.display(description="Publicada el")
    def publicada_el(self, obj):
        return obj.fecha_publicacion


def guaranies(value):
    return f"Gs. {int(value):,}".replace(",", ".")


def property_amenities(propiedad):
    amenities = [amenity.nombre for amenity in propiedad.amenities.all()]
    return ", ".join(amenities) if amenities else "Sin amenities cargados"


def property_rules(propiedad):
    return (
        f"Mascotas: {'si' if propiedad.permite_mascotas else 'no'}; "
        f"Fumar: {'si' if propiedad.permite_fumar else 'no'}; "
        f"Fiestas: {'si' if propiedad.permite_fiestas else 'no'}"
    )


class ReservaAdminForm(forms.ModelForm):
    class Meta:
        model = Reserva
        fields = "__all__"

    def clean(self):
        cleaned_data = super().clean()
        propiedad = cleaned_data.get("id_propiedad")
        start_date = cleaned_data.get("fecha_inicio")
        end_date = cleaned_data.get("fecha_fin")
        guests = cleaned_data.get("cantidad_huespedes") or 1

        if not propiedad or not start_date or not end_date:
            return cleaned_data

        if start_date < timezone.localdate():
            raise forms.ValidationError("No se puede reservar con fecha de entrada pasada.")

        if guests > propiedad.capacidad_maxima_huespedes:
            raise forms.ValidationError(
                "La cantidad de huespedes supera la capacidad maxima de la propiedad."
            )

        overlapping_reservations = Reserva.objects.filter(
            id_propiedad=propiedad,
            estado__in=BLOCKING_RESERVATION_STATES,
            fecha_inicio__lt=end_date,
            fecha_fin__gt=start_date,
        )
        blocked_availability = Disponibilidad.objects.filter(
            id_propiedad=propiedad,
            estado__in=BLOCKING_AVAILABILITY_STATES,
            fecha__gte=start_date,
            fecha__lt=end_date,
        )

        if self.instance.pk:
            overlapping_reservations = overlapping_reservations.exclude(pk=self.instance.pk)
            blocked_availability = blocked_availability.filter(
                Q(id_reserva__isnull=True) | ~Q(id_reserva=self.instance)
            )

        if overlapping_reservations.exists() or blocked_availability.exists():
            raise forms.ValidationError("La propiedad no esta disponible para esas fechas.")

        return cleaned_data


@admin.register(Reserva)
class ReservaAdmin(RoleAdminMixin, admin.ModelAdmin):
    form = ReservaAdminForm
    allowed_roles = ("admin", "anfitrion", "huesped")
    add_roles = ("admin", "huesped")
    change_roles = ("admin", "anfitrion", "huesped")
    delete_roles = ("admin",)
    list_display = ("id", "id_propiedad", "id_huesped", "fecha_inicio", "fecha_fin", "estado", "precio_total", "monto_reembolso")
    list_filter = ("estado", "fecha_inicio", "id_propiedad")
    search_fields = ("id_propiedad__titulo", "id_huesped__username")
    readonly_fields = ("fecha_cancelacion", "cancelada_por", "monto_reembolso", "detalle_propiedad", "ver_propiedades")
    inlines = [DisponibilidadReservaInline]
    actions = ["confirmar_reservas", "rechazar_reservas"]

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        if is_admin_role(request.user):
            return queryset
        if request.user.rol == "anfitrion":
            return queryset.filter(id_propiedad__id_anfitrion=request.user)
        if request.user.rol == "huesped":
            return queryset.filter(id_huesped=request.user)
        return queryset.none()

    def get_fields(self, request, obj=None):
        if request.user.rol == "huesped":
            if obj:
                return (
                    "fecha_inicio",
                    "fecha_fin",
                    "cantidad_huespedes",
                    "id_propiedad",
                    "detalle_propiedad",
                    "estado",
                    "precio_total",
                    "monto_reembolso",
                )
            return (
                "fecha_inicio",
                "fecha_fin",
                "cantidad_huespedes",
                "id_propiedad",
                "ver_propiedades",
            )
        if request.user.rol == "anfitrion":
            return ("estado",)
        return super().get_fields(request, obj)

    def get_readonly_fields(self, request, obj=None):
        if request.user.rol == "anfitrion":
            return ()
        if request.user.rol == "huesped":
            if obj and obj.estado == "pendiente":
                return ("detalle_propiedad", "estado", "precio_total", "monto_reembolso")
            if obj:
                return (
                    "fecha_inicio",
                    "fecha_fin",
                    "cantidad_huespedes",
                    "id_propiedad",
                    "detalle_propiedad",
                    "estado",
                    "precio_total",
                    "monto_reembolso",
                )
            return ("ver_propiedades",)
        return self.readonly_fields

    def has_change_permission(self, request, obj=None):
        if is_admin_role(request.user):
            return True
        if request.user.rol == "anfitrion" and obj is None:
            return True
        if request.user.rol == "anfitrion" and obj:
            return obj.id_propiedad.id_anfitrion_id == request.user.id
        if request.user.rol == "huesped" and obj is None:
            return True
        if request.user.rol == "huesped" and obj:
            return obj.id_huesped_id == request.user.id and obj.estado == "pendiente"
        return False

    def can_manage_reserva(self, request, reserva):
        if is_admin_role(request.user):
            return True
        return (
            request.user.rol == "anfitrion"
            and reserva.id_propiedad.id_anfitrion_id == request.user.id
        )

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "id_huesped" and request.user.rol == "huesped":
            kwargs["queryset"] = Usuario.objects.filter(id=request.user.id)
        if db_field.name == "id_propiedad" and request.user.rol == "huesped":
            kwargs["queryset"] = Propiedad.objects.filter(estado="disponible").order_by("titulo")
        if db_field.name == "id_propiedad" and request.user.rol == "anfitrion":
            kwargs["queryset"] = Propiedad.objects.filter(id_anfitrion=request.user)
        formfield = super().formfield_for_foreignkey(db_field, request, **kwargs)
        return formfield

    def save_model(self, request, obj, form, change):
        if request.user.rol == "huesped":
            if change:
                original = Reserva.objects.get(pk=obj.pk)
                if original.estado != "pendiente":
                    raise PermissionDenied("Solo podes modificar reservas pendientes.")
                obj.id_huesped = original.id_huesped
                obj.estado = original.estado
            else:
                obj.id_huesped = request.user
                obj.estado = "pendiente"
            obj.precio_total = calculate_price(obj.id_propiedad, obj.fecha_inicio, obj.fecha_fin)
        super().save_model(request, obj, form, change)
        sync_reservation_availability(obj)

    @admin.display(description="Detalle de la propiedad")
    def detalle_propiedad(self, obj):
        if not obj or not obj.id_propiedad_id:
            return "-"
        propiedad = obj.id_propiedad
        return self.property_detail_html(propiedad)

    @admin.display(description="Propiedades disponibles")
    def ver_propiedades(self, obj):
        return format_html(
            '<a class="button" href="/admin/presupuesto/propiedad/">Ver propiedades y detalles</a>'
        )

    def property_detail_html(self, propiedad):
        return format_html(
            "<strong>{}</strong><br>"
            "Descripcion: {}<br>"
            "Ubicacion: {} - {}<br>"
            "Tipo: {} | Estado: {} | Capacidad: {} huesped(es)<br>"
            "Precio noche: {} | Fin de semana: {} | Limpieza: {}<br>"
            "Amenities: {}<br>"
            "Reglas: {}<br>"
            "Politica de cancelacion: {}",
            propiedad.titulo,
            propiedad.descripcion,
            propiedad.ubicacion,
            propiedad.calle or "Sin calle cargada",
            propiedad.get_tipo_alojamiento_display(),
            propiedad.get_estado_display(),
            propiedad.capacidad_maxima_huespedes,
            guaranies(propiedad.precio_noche),
            guaranies(propiedad.precio_fin_semana),
            guaranies(propiedad.tarifa_limpieza),
            property_amenities(propiedad),
            property_rules(propiedad),
            propiedad.get_politica_cancelacion_display(),
        )

    @admin.action(description="Confirmar reservas seleccionadas")
    def confirmar_reservas(self, request, queryset):
        total = 0
        for reserva in queryset.select_related("id_propiedad__id_anfitrion", "id_huesped"):
            if (
                reserva.estado == "pendiente"
                and self.can_manage_reserva(request, reserva)
            ):
                update_reservation_status(reserva, "confirmada")
                total += 1
        self.message_user(request, f"Se confirmaron {total} reserva(s) pendiente(s).")

    @admin.action(description="Rechazar reservas seleccionadas")
    def rechazar_reservas(self, request, queryset):
        total = 0
        for reserva in queryset.select_related("id_propiedad__id_anfitrion", "id_huesped"):
            if (
                reserva.estado == "pendiente"
                and self.can_manage_reserva(request, reserva)
            ):
                update_reservation_status(reserva, "rechazada")
                total += 1
        self.message_user(request, f"Se rechazaron {total} reserva(s) pendiente(s).")


@admin.register(Review)
class ReviewAdmin(RoleAdminMixin, admin.ModelAdmin):
    allowed_roles = ("admin", "anfitrion", "huesped")
    add_roles = ("huesped",)
    change_roles = ()
    delete_roles = ()
    list_display = ("id", "id_propiedad", "id_usuario", "calificacion", "fecha")
    list_filter = ("calificacion", "fecha", "id_propiedad")
    search_fields = ("comentario", "id_propiedad__titulo", "id_usuario__username")
    readonly_fields = ("fecha", "id_usuario", "id_propiedad")

    def has_add_permission(self, request):
        return request.user.is_active and getattr(request.user, "rol", None) == "huesped"

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def get_fields(self, request, obj=None):
        if request.user.rol == "huesped":
            return ("calificacion", "comentario", "id_reserva")
        return ("calificacion", "comentario", "fecha", "id_usuario", "id_propiedad", "id_reserva")

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        if is_admin_role(request.user):
            return queryset
        if request.user.rol == "anfitrion":
            return queryset.filter(id_propiedad__id_anfitrion=request.user)
        if request.user.rol == "huesped":
            return queryset.filter(id_usuario=request.user)
        return queryset.none()

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "id_reserva" and request.user.rol == "huesped":
            kwargs["queryset"] = Reserva.objects.filter(id_huesped=request.user)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def save_model(self, request, obj, form, change):
        if request.user.rol == "huesped":
            obj.id_usuario = request.user
            obj.id_propiedad = obj.id_reserva.id_propiedad
        super().save_model(request, obj, form, change)
