from datetime import timedelta
from decimal import Decimal, ROUND_HALF_UP

from django.db.models import Q

from .models import Disponibilidad, Propiedad, Reserva, Usuario


BLOCKING_RESERVATION_STATES = ["pendiente", "confirmada"]
BLOCKING_AVAILABILITY_STATES = ["bloqueada", "reservada"]


def iter_stay_dates(start_date, end_date):
    current = start_date
    while current < end_date:
        yield current
        current += timedelta(days=1)


def calculate_price(propiedad, start_date, end_date):
    total = Decimal("0")
    for day in iter_stay_dates(start_date, end_date):
        if day.weekday() in (4, 5):
            total += propiedad.precio_fin_semana
        else:
            total += propiedad.precio_noche
    return (total + propiedad.tarifa_limpieza).quantize(Decimal("1"), rounding=ROUND_HALF_UP)


def reservation_overlaps(propiedad, start_date, end_date):
    return Reserva.objects.filter(
        id_propiedad=propiedad,
        estado__in=BLOCKING_RESERVATION_STATES,
        fecha_inicio__lt=end_date,
        fecha_fin__gt=start_date,
    )


def blocked_dates(propiedad, start_date, end_date):
    return Disponibilidad.objects.filter(
        id_propiedad=propiedad,
        fecha__gte=start_date,
        fecha__lt=end_date,
        estado__in=BLOCKING_AVAILABILITY_STATES,
    )


def is_property_available(propiedad, start_date, end_date):
    if propiedad.estado != "disponible":
        return False
    if reservation_overlaps(propiedad, start_date, end_date).exists():
        return False
    return not blocked_dates(propiedad, start_date, end_date).exists()


def release_reserved_dates(reserva):
    reserva.disponibilidades.update(
        estado="disponible",
        fecha_inicio_reserva=None,
        id_reserva=None,
    )


def mark_reserved_dates(reserva):
    reserva.disponibilidades.exclude(
        fecha__gte=reserva.fecha_inicio,
        fecha__lt=reserva.fecha_fin,
    ).update(
        estado="disponible",
        fecha_inicio_reserva=None,
        id_reserva=None,
    )

    for day in iter_stay_dates(reserva.fecha_inicio, reserva.fecha_fin):
        Disponibilidad.objects.update_or_create(
            id_propiedad=reserva.id_propiedad,
            fecha=day,
            defaults={
                "estado": "reservada",
                "fecha_inicio_reserva": reserva.fecha_inicio,
                "id_reserva": reserva,
            },
        )


def sync_reservation_availability(reserva):
    if reserva.estado in BLOCKING_RESERVATION_STATES:
        mark_reserved_dates(reserva)
    else:
        release_reserved_dates(reserva)


def get_available_properties(start_date, end_date, guests=None, property_id=None):
    queryset = Propiedad.objects.filter(estado="disponible").prefetch_related("amenities")
    if property_id:
        queryset = queryset.filter(id=property_id)

    available = []
    for propiedad in queryset:
        if is_property_available(propiedad, start_date, end_date):
            available.append(
                {
                    "id": propiedad.id,
                    "titulo": propiedad.titulo,
                    "calle": propiedad.calle,
                    "ubicacion": propiedad.ubicacion,
                    "precio_total": str(calculate_price(propiedad, start_date, end_date)),
                    "amenities": [amenity.nombre for amenity in propiedad.amenities.all()],
                    "nota_huespedes": (
                        "El sistema no registra capacidad maxima por propiedad; "
                        f"se informo la busqueda para {guests} huesped(es)."
                        if guests
                        else "El sistema no registra capacidad maxima por propiedad."
                    ),
                }
            )
    return available


def create_reservation(propiedad_id, huesped_id, start_date, end_date, guests):
    propiedad = Propiedad.objects.get(id=propiedad_id)
    huesped = Usuario.objects.get(id=huesped_id, rol="huesped")

    if not is_property_available(propiedad, start_date, end_date):
        raise ValueError("La propiedad no esta disponible para esas fechas.")

    reserva = Reserva.objects.create(
        id_propiedad=propiedad,
        id_huesped=huesped,
        fecha_inicio=start_date,
        fecha_fin=end_date,
        cantidad_huespedes=guests,
        estado="pendiente",
        precio_total=calculate_price(propiedad, start_date, end_date),
    )
    sync_reservation_availability(reserva)
    return reserva


def host_reservations(host_id=None, status=None, month=None):
    queryset = Reserva.objects.select_related("id_propiedad", "id_huesped", "id_propiedad__id_anfitrion")
    if host_id:
        queryset = queryset.filter(id_propiedad__id_anfitrion_id=host_id)
    if status:
        queryset = queryset.filter(estado=status)
    if month:
        year, month_number = month.split("-")
        queryset = queryset.filter(fecha_inicio__year=int(year), fecha_inicio__month=int(month_number))
    return queryset.order_by("-fecha_inicio")


def find_property_by_text(text):
    normalized = text.strip()
    if not normalized:
        return None
    return (
        Propiedad.objects.filter(
            Q(titulo__icontains=normalized)
            | Q(calle__icontains=normalized)
            | Q(ubicacion__icontains=normalized)
            | Q(descripcion__icontains=normalized)
        )
        .prefetch_related("amenities")
        .first()
    )
