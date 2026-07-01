from datetime import timedelta
from decimal import Decimal, ROUND_HALF_UP

from django.db.models import Q
from django.utils import timezone

from .models import Disponibilidad, HistorialPropiedadVisitada, Notificacion, Propiedad, Reserva, Usuario


BLOCKING_RESERVATION_STATES = ["pendiente", "confirmada", "activa"]
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


def has_guest_capacity(propiedad, guests):
    return int(guests or 1) <= propiedad.capacidad_maxima_huespedes


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


def create_notification(user, message, reserva=None):
    return Notificacion.objects.create(
        id_usuario=user,
        id_reserva=reserva,
        mensaje=message,
    )


def notify_reservation_change(reserva, message):
    create_notification(reserva.id_huesped, message, reserva)
    create_notification(reserva.id_propiedad.id_anfitrion, message, reserva)


def get_available_properties(start_date, end_date, guests=None, property_id=None):
    queryset = Propiedad.objects.filter(estado="disponible").prefetch_related("amenities")
    if property_id:
        queryset = queryset.filter(id=property_id)

    available = []
    guests = int(guests or 1)
    for propiedad in queryset:
        if is_property_available(propiedad, start_date, end_date) and has_guest_capacity(propiedad, guests):
            available.append(
                {
                    "id": propiedad.id,
                    "titulo": propiedad.titulo,
                    "calle": propiedad.calle,
                    "ubicacion": propiedad.ubicacion,
                    "tipo_alojamiento": propiedad.tipo_alojamiento,
                    "capacidad_maxima_huespedes": propiedad.capacidad_maxima_huespedes,
                    "precio_total": str(calculate_price(propiedad, start_date, end_date)),
                    "amenities": [amenity.nombre for amenity in propiedad.amenities.all()],
                    "reglas_casa": {
                        "permite_mascotas": propiedad.permite_mascotas,
                        "permite_fumar": propiedad.permite_fumar,
                        "permite_fiestas": propiedad.permite_fiestas,
                    },
                    "politica_cancelacion": propiedad.politica_cancelacion,
                }
            )
    return available


def create_reservation(propiedad_id, huesped_id, start_date, end_date, guests):
    propiedad = Propiedad.objects.get(id=propiedad_id)
    huesped = Usuario.objects.get(id=huesped_id, rol="huesped")
    guests = int(guests or 1)

    if start_date < timezone.localdate():
        raise ValueError("No se puede reservar con fecha de entrada pasada.")

    if end_date <= start_date:
        raise ValueError("La fecha de salida debe ser posterior a la fecha de entrada.")

    if guests < 1:
        raise ValueError("La reserva debe tener al menos un huesped.")

    if not has_guest_capacity(propiedad, guests):
        raise ValueError(
            "La cantidad de huespedes supera la capacidad maxima de la propiedad."
        )

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
    notify_reservation_change(
        reserva,
        f"Reserva #{reserva.id} creada en estado pendiente para {propiedad.titulo}.",
    )
    return reserva


def calculate_refund(reserva, today=None):
    today = today or timezone.localdate()
    days_before = (reserva.fecha_inicio - today).days
    policy = reserva.id_propiedad.politica_cancelacion

    if policy == "flexible":
        percent = Decimal("1.00") if days_before >= 1 else Decimal("0.50")
    elif policy == "moderada":
        if days_before >= 5:
            percent = Decimal("1.00")
        elif days_before >= 1:
            percent = Decimal("0.50")
        else:
            percent = Decimal("0.00")
    else:
        percent = Decimal("0.50") if days_before >= 7 else Decimal("0.00")

    return (reserva.precio_total * percent).quantize(Decimal("1"), rounding=ROUND_HALF_UP)


def cancel_reservation(reserva, cancelled_by=None, reason=""):
    if reserva.estado in ["cancelada", "completada"]:
        raise ValueError("La reserva no se puede cancelar en su estado actual.")

    reserva.estado = "cancelada"
    reserva.fecha_cancelacion = timezone.now()
    reserva.cancelada_por = cancelled_by
    reserva.motivo_cancelacion = reason or "Cancelacion solicitada desde el sistema."
    reserva.monto_reembolso = calculate_refund(reserva)
    reserva.save()
    sync_reservation_availability(reserva)
    notify_reservation_change(
        reserva,
        (
            f"Reserva #{reserva.id} cancelada. Reembolso simulado: "
            f"Gs. {int(reserva.monto_reembolso):,}."
        ).replace(",", "."),
    )
    return reserva


def update_reservation_status(reserva, new_status):
    if new_status not in dict(Reserva.ESTADO_CHOICES):
        raise ValueError("Estado de reserva invalido.")
    if reserva.estado == "cancelada":
        raise ValueError("No se puede cambiar una reserva cancelada.")

    reserva.estado = new_status
    reserva.save()
    sync_reservation_availability(reserva)
    notify_reservation_change(reserva, f"Reserva #{reserva.id} cambio a estado {reserva.get_estado_display()}.")
    return reserva


def record_property_visit(user, propiedad):
    if not user.is_authenticated or user.rol != "huesped":
        return None
    history, created = HistorialPropiedadVisitada.objects.get_or_create(
        id_usuario=user,
        id_propiedad=propiedad,
    )
    if not created:
        history.cantidad_visitas += 1
        history.fecha_visita = timezone.now()
        history.save(update_fields=["cantidad_visitas", "fecha_visita"])
    return history


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
