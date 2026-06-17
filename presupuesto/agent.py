import re
import unicodedata
from datetime import date, datetime, timedelta

from django.utils import timezone

from .models import Propiedad, Reserva, Review, Usuario
from .serializers import ReservaSerializer, ReviewSerializer
from .services import create_reservation, get_available_properties, host_reservations, find_property_by_text


SYSTEM_PROMPT = """
Sos el asistente de reservas de GuairaDevs Booking. Ayudas a huespedes a consultar
propiedades, amenities, resenas, disponibilidad y reservas; ayudas a anfitriones a revisar
sus reservas; y ayudas a administradores a supervisar reservas globales. No respondes temas fuera de la plataforma. No buscas online: solo usas
la informacion disponible en la API/backend del proyecto. Si falta un dato, lo pedis.
Antes de crear, confirmar, cancelar o modificar una reserva, siempre pedis confirmacion
explicita y mostras el resumen de la accion.
""".strip()


MONTHS = {
    "enero": 1,
    "febrero": 2,
    "marzo": 3,
    "abril": 4,
    "mayo": 5,
    "junio": 6,
    "julio": 7,
    "agosto": 8,
    "septiembre": 9,
    "setiembre": 9,
    "octubre": 10,
    "noviembre": 11,
    "diciembre": 12,
}


OUT_OF_SCOPE_REPLY = (
    "Puedo ayudarte solo con propiedades, amenities, disponibilidad, reservas y resenas "
    "del sistema de booking."
)


def normalize(text):
    text = text.lower().strip()
    return "".join(
        char for char in unicodedata.normalize("NFD", text)
        if unicodedata.category(char) != "Mn"
    )


def parse_guests(text):
    match = re.search(r"(\d+)\s*(persona|personas|huesped|huespedes)", normalize(text))
    return int(match.group(1)) if match else 1


def infer_year(month_number, today=None):
    today = today or timezone.localdate()
    year = today.year
    if month_number < today.month:
        year += 1
    return year


def parse_iso_date(value):
    return datetime.strptime(value, "%Y-%m-%d").date()


def parse_slash_date(value):
    return datetime.strptime(value, "%d/%m/%Y").date()


def parse_date_range(text):
    normalized = normalize(text)

    iso_range = re.search(r"(\d{4}-\d{2}-\d{2})\s*(?:al|hasta|-)\s*(\d{4}-\d{2}-\d{2})", normalized)
    if iso_range:
        return parse_iso_date(iso_range.group(1)), parse_iso_date(iso_range.group(2))

    slash_range = re.search(r"(\d{1,2}/\d{1,2}/\d{4})\s*(?:al|hasta|-)\s*(\d{1,2}/\d{1,2}/\d{4})", normalized)
    if slash_range:
        return parse_slash_date(slash_range.group(1)), parse_slash_date(slash_range.group(2))

    single_iso = re.search(r"(\d{4}-\d{2}-\d{2})", normalized)
    if single_iso:
        start = parse_iso_date(single_iso.group(1))
        return start, start + timedelta(days=1)

    single_slash = re.search(r"(\d{1,2}/\d{1,2}/\d{4})", normalized)
    if single_slash:
        start = parse_slash_date(single_slash.group(1))
        return start, start + timedelta(days=1)

    month_names = "|".join(MONTHS.keys())
    repeated_month_range = re.search(
        rf"(?:desde\s+el\s+|desde\s+|del\s+)?(\d{{1,2}})\s*de\s*({month_names})\s*(?:al|hasta|-)\s*(?:el\s+)?(\d{{1,2}})\s*de\s*({month_names})(?:\s*(?:del|de)\s*(\d{{4}}))?",
        normalized,
    )
    if repeated_month_range:
        start_day = int(repeated_month_range.group(1))
        start_month = MONTHS[repeated_month_range.group(2)]
        end_day = int(repeated_month_range.group(3))
        end_month = MONTHS[repeated_month_range.group(4)]
        year = int(repeated_month_range.group(5)) if repeated_month_range.group(5) else infer_year(start_month)
        end_year = year + 1 if end_month < start_month else year
        return date(year, start_month, start_day), date(end_year, end_month, end_day)

    range_match = re.search(
        rf"(?:desde\s+el\s+|desde\s+|del\s+)?(\d{{1,2}})\s*(?:al|-|hasta)\s*(?:el\s+)?(\d{{1,2}})\s*de\s*({month_names})",
        normalized,
    )
    if range_match:
        start_day = int(range_match.group(1))
        end_day = int(range_match.group(2))
        month_number = MONTHS[range_match.group(3)]
        explicit_year = re.search(r"(?:del|de)\s*(\d{4})", normalized[range_match.end():])
        year = int(explicit_year.group(1)) if explicit_year else infer_year(month_number)
        return date(year, month_number, start_day), date(year, month_number, end_day)

    single_match = re.search(rf"(?:para\s+el|el|del|desde\s+el)?\s*(\d{{1,2}})\s*de\s*({month_names})", normalized)
    if single_match:
        day = int(single_match.group(1))
        month_number = MONTHS[single_match.group(2)]
        year = infer_year(month_number)
        start = date(year, month_number, day)
        return start, start + timedelta(days=1)

    return None, None


def extract_property_text(text):
    normalized_text = normalize(text)
    for propiedad in Propiedad.objects.all():
        if normalize(propiedad.titulo) in normalized_text:
            return propiedad.titulo

    match = re.search(
        r"(?:en|de|tiene)\s+(?:la|el)?\s*([^,.?]+?)(?:\s+para\s+la\s+fecha|\s+para\s+el|\s+del|\s+desde|\s+hasta|,|\?|\.|$)",
        text,
        re.IGNORECASE,
    )
    if match:
        return match.group(1).strip(" ?.!")

    match = re.search(r"(quinta\s+[\w\s]+?)(?:\s+para\s+la\s+fecha|\s+para\s+el|\s+del|\s+desde|\s+hasta|,|\?|\.|$)", text, re.IGNORECASE)
    if match:
        return match.group(1).strip(" ?.!")
    return text.strip(" ?.!")


def wants_to_create_reservation(normalized):
    patterns = [
        r"\breservar\b",
        r"\breservame\b",
        r"\breservarme\b",
        r"\breserva\s+esta\b",
        r"\bhacer(?:me)?\s+una\s+reserva\b",
        r"\bcrear\s+una\s+reserva\b",
        r"\bquiero\s+una\s+reserva\b",
    ]
    return any(re.search(pattern, normalized) for pattern in patterns)


def property_payload(propiedad):
    amenities = [amenity.nombre for amenity in propiedad.amenities.all()]
    accepts_pets = any("mascota" in normalize(name) for name in amenities)
    return {
        "id": propiedad.id,
        "titulo": propiedad.titulo,
        "descripcion": propiedad.descripcion,
        "calle": propiedad.calle,
        "ubicacion": propiedad.ubicacion,
        "precio_noche": str(propiedad.precio_noche),
        "precio_fin_semana": str(propiedad.precio_fin_semana),
        "tarifa_limpieza": str(propiedad.tarifa_limpieza),
        "estado": propiedad.estado,
        "amenities": amenities,
        "acepta_mascotas": accepts_pets,
    }


def handle_confirmation(payload):
    action = payload.get("pending_action") or {}
    if action.get("type") != "create_reservation":
        return {
            "reply": "No tengo una accion pendiente para confirmar.",
            "intent": "confirmation_without_action",
        }

    data = action["data"]
    try:
        reserva = create_reservation(
            data["property_id"],
            data["guest_id"],
            parse_iso_date(data["start_date"]),
            parse_iso_date(data["end_date"]),
            data["guests"],
        )
    except Exception as exc:
        return {
            "reply": f"No pude crear la reserva: {exc}",
            "intent": "create_reservation_error",
            "error": str(exc),
        }

    return {
        "reply": (
            f"Listo, cree la reserva #{reserva.id} en estado pendiente para "
            f"{reserva.id_propiedad.titulo}, del {reserva.fecha_inicio} al {reserva.fecha_fin}."
        ),
        "intent": "create_reservation_confirmed",
        "data": ReservaSerializer(reserva).data,
    }


def handle_availability(message):
    start_date, end_date = parse_date_range(message)
    if not start_date or not end_date:
        return {
            "reply": "Para consultar disponibilidad necesito fecha de entrada y salida.",
            "intent": "availability_missing_dates",
        }
    if end_date <= start_date:
        return {
            "reply": "La fecha de salida debe ser posterior a la fecha de entrada.",
            "intent": "availability_invalid_dates",
        }

    guests = parse_guests(message)
    available = get_available_properties(start_date, end_date, guests=guests)
    if not available:
        return {
            "reply": f"No encontre propiedades disponibles del {start_date} al {end_date}.",
            "intent": "availability",
            "data": [],
        }

    names = ", ".join(f"{item['titulo']} (id {item['id']})" for item in available[:5])
    return {
        "reply": (
            f"Si, encontre {len(available)} propiedad(es) disponibles del {start_date} "
            f"al {end_date} para {guests} persona(s): {names}."
        ),
        "intent": "availability",
        "data": available,
    }


def handle_property_info(message):
    property_text = extract_property_text(message)
    propiedad = find_property_by_text(property_text)
    if not propiedad:
        return {
            "reply": "No encontre esa propiedad en el sistema. Proba con el nombre exacto.",
            "intent": "property_not_found",
        }

    payload = property_payload(propiedad)
    amenities = ", ".join(payload["amenities"]) if payload["amenities"] else "sin amenities cargados"
    pets = "si" if payload["acepta_mascotas"] else "no figura como permitido"
    return {
        "reply": f"{propiedad.titulo} tiene: {amenities}. Mascotas: {pets}.",
        "intent": "property_info",
        "data": payload,
    }


def handle_property_reviews(message):
    property_text = extract_property_text(message)
    propiedad = find_property_by_text(property_text)
    if not propiedad:
        return {
            "reply": "No encontre esa propiedad para consultar sus resenas. Proba con el nombre exacto.",
            "intent": "reviews_property_not_found",
        }

    reviews = (
        Review.objects.filter(id_propiedad=propiedad)
        .select_related("id_usuario", "id_propiedad", "id_reserva")
        .order_by("-fecha")
    )
    count = reviews.count()
    if count == 0:
        return {
            "reply": f"{propiedad.titulo} todavia no tiene resenas cargadas.",
            "intent": "property_reviews",
            "data": {"count": 0, "reviews": []},
        }

    average = sum(review.calificacion for review in reviews) / count
    comments = "; ".join(
        f"{review.calificacion}/5: {review.comentario}" for review in reviews[:3]
    )
    return {
        "reply": (
            f"{propiedad.titulo} tiene {count} resena(s), promedio {average:.1f}/5. "
            f"Ultimos comentarios: {comments}"
        ),
        "intent": "property_reviews",
        "data": {
            "count": count,
            "average": round(average, 2),
            "reviews": ReviewSerializer(reviews[:10], many=True).data,
        },
    }


def handle_create_reservation(message, user_id):
    start_date, end_date = parse_date_range(message)
    if not start_date or not end_date:
        return {
            "reply": "Para preparar la reserva necesito fecha de entrada y salida.",
            "intent": "reservation_missing_dates",
        }

    property_text = extract_property_text(message)
    propiedad = find_property_by_text(property_text)
    if not propiedad:
        return {
            "reply": "No encontre la propiedad para reservar. Decime el nombre exacto.",
            "intent": "reservation_property_not_found",
        }

    guest_id = user_id or Usuario.objects.filter(rol="huesped").values_list("id", flat=True).first()
    if not guest_id:
        return {
            "reply": "No hay un usuario huesped disponible para asociar la reserva.",
            "intent": "reservation_missing_guest",
        }

    guests = parse_guests(message)
    available = get_available_properties(start_date, end_date, guests=guests, property_id=propiedad.id)
    if not available:
        return {
            "reply": f"{propiedad.titulo} no esta disponible del {start_date} al {end_date}.",
            "intent": "reservation_unavailable",
        }

    pending_action = {
        "type": "create_reservation",
        "data": {
            "property_id": propiedad.id,
            "guest_id": int(guest_id),
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "guests": guests,
        },
    }
    return {
        "reply": (
            f"Puedo crear una reserva pendiente para {propiedad.titulo}, del {start_date} "
            f"al {end_date}, para {guests} persona(s). Total estimado: "
            f"{available[0]['precio_total']}. Confirmas que la cree?"
        ),
        "intent": "create_reservation_needs_confirmation",
        "pending_action": pending_action,
    }


def handle_host_summary(message, user_id):
    normalized = normalize(message)
    today = timezone.localdate()
    month = f"{today.year}-{today.month:02d}" if "mes" in normalized else None
    scope = "anfitrion"

    if user_id:
        user = Usuario.objects.filter(id=user_id).first()
        if user and user.rol == "admin":
            user_id = None
            scope = "admin"
        elif user and user.rol != "anfitrion":
            return {
                "reply": (
                    f"Estas preguntando como {user.username}, que tiene rol {user.get_rol_display()}. "
                    "Para consultar reservas, elegi un usuario Admin para ver todo el sistema "
                    "o un usuario Anfitrion para ver sus reservas."
                ),
                "intent": "host_wrong_role",
                "data": {"user_id": user.id, "rol": user.rol},
            }

    status = None
    if "pendiente" in normalized:
        status = "pendiente"
    elif "confirmada" in normalized:
        status = "confirmada"

    reservations = host_reservations(host_id=user_id, status=status, month=month)
    count = reservations.count()

    if "cuantas" in normalized or "cuantos" in normalized or "cantidad" in normalized:
        period = " este mes" if month else ""
        owner = "en todo el sistema" if scope == "admin" else ""
        return {
            "reply": f"Tenes {count} reserva(s){period} {owner}.".replace("  ", " ").strip(),
            "intent": "reservation_count",
            "data": {"count": count, "month": month, "status": status, "scope": scope},
        }

    serialized = ReservaSerializer(reservations[:10], many=True).data
    if status == "pendiente" and count == 0:
        reply = "No tenes reservas pendientes de confirmar."
    else:
        scope_text = " en todo el sistema" if scope == "admin" else ""
        reply = f"Encontre {count} reserva(s){scope_text}" + (f" en estado {status}" if status else "") + "."
    return {"reply": reply, "intent": "reservations", "data": serialized}


def chat(payload):
    message = (payload.get("message") or "").strip()
    if not message:
        return {"reply": "Decime que necesitas consultar sobre reservas o propiedades.", "intent": "empty"}

    if payload.get("confirm") is True or normalize(message) in {"si", "confirmo", "confirmar", "dale"}:
        return handle_confirmation(payload)

    normalized = normalize(message)
    user_id = payload.get("user_id")

    if any(word in normalized for word in ["clima", "noticia", "internet", "online", "google"]):
        return {"reply": OUT_OF_SCOPE_REPLY, "intent": "out_of_scope"}

    if wants_to_create_reservation(normalized):
        return handle_create_reservation(message, user_id)

    if any(word in normalized for word in ["disponible", "disponibilidad", "hay propiedades"]):
        return handle_availability(message)

    if any(word in normalized for word in ["review", "reviews", "resena", "resenas", "calificacion", "estrellas"]):
        return handle_property_reviews(message)

    if any(word in normalized for word in ["amenities", "amenity", "mascota", "propiedad", "quinta"]):
        return handle_property_info(message)

    if any(word in normalized for word in ["anfitrion", "pendiente", "confirmar", "cuantas reservas", "cuantos reservas", "reservas tuve"]):
        return handle_host_summary(message, user_id)

    return {"reply": OUT_OF_SCOPE_REPLY, "intent": "fallback"}
