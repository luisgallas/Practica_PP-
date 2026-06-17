import json

from django import forms
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.shortcuts import render
from django.utils.html import format_html

from . import agent
from .models import AgenteIAConfig, Amenity, Disponibilidad, Notificacion, PreguntarIA, Propiedad, Reserva, Review, Usuario
from .services import sync_reservation_availability


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


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ("Datos de booking", {"fields": ("rol", "telefono", "fecha_registro")}),
    )
    list_display = ("username", "email", "rol", "is_staff", "is_active")


admin.site.register(Amenity)
admin.site.register(Notificacion)


@admin.action(description="Eliminar seleccionado")
def eliminar_propiedades_seleccionadas(modeladmin, request, queryset):
    total = queryset.count()
    queryset.delete()
    modeladmin.message_user(request, f"Se eliminaron {total} propiedad(es) seleccionada(s).")


@admin.register(Propiedad)
class PropiedadAdmin(admin.ModelAdmin):
    change_list_template = "admin/presupuesto/propiedad/change_list.html"
    list_display = ("titulo", "ubicacion", "calle", "estado", "precio_noche_guaranies")
    search_fields = ("titulo", "ubicacion", "calle", "descripcion")
    list_filter = ("estado", "ubicacion", "amenities")
    actions = [eliminar_propiedades_seleccionadas]
    actions_on_top = True
    actions_on_bottom = True

    @admin.display(description="Precio noche")
    def precio_noche_guaranies(self, obj):
        return f"Gs. {int(obj.precio_noche):,}".replace(",", ".")


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
class AgenteIAConfigAdmin(admin.ModelAdmin):
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
        return not AgenteIAConfig.objects.exists()

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
class PreguntarIAAdmin(admin.ModelAdmin):
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


@admin.register(Reserva)
class ReservaAdmin(admin.ModelAdmin):
    list_display = ("id", "id_propiedad", "id_huesped", "fecha_inicio", "fecha_fin", "estado", "precio_total")
    list_filter = ("estado", "fecha_inicio", "id_propiedad")
    search_fields = ("id_propiedad__titulo", "id_huesped__username")
    inlines = [DisponibilidadReservaInline]

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        sync_reservation_availability(obj)


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("id", "id_propiedad", "id_usuario", "calificacion", "fecha")
    list_filter = ("calificacion", "fecha", "id_propiedad")
    search_fields = ("comentario", "id_propiedad__titulo", "id_usuario__username")
    readonly_fields = ("calificacion", "comentario", "fecha", "id_usuario", "id_propiedad", "id_reserva")
    fields = ("calificacion", "comentario", "fecha", "id_usuario", "id_propiedad", "id_reserva")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
