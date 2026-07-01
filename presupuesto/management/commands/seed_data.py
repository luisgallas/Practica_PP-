from datetime import date, timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand

from presupuesto.agent import SYSTEM_PROMPT
from presupuesto.models import AgenteIAConfig, Amenity, Disponibilidad, Propiedad, Reserva, Review, Usuario
from presupuesto.services import sync_reservation_availability


class Command(BaseCommand):
    help = "Carga datos de ejemplo para probar el booking y el agente."

    def handle(self, *args, **options):
        admin, _ = Usuario.objects.get_or_create(
            username="admin",
            defaults={
                "email": "admin@test.com",
                "rol": "admin",
                "is_staff": True,
                "is_superuser": True,
            },
        )
        admin.set_password("admin123")
        admin.save()

        host, _ = Usuario.objects.get_or_create(
            username="anfitrion1",
            defaults={
                "first_name": "Juan",
                "last_name": "Perez",
                "email": "anfitrion@test.com",
                "rol": "anfitrion",
                "is_staff": True,
            },
        )
        host.rol = "anfitrion"
        host.is_staff = True
        host.set_password("test123")
        host.save()

        guest, _ = Usuario.objects.get_or_create(
            username="huesped1",
            defaults={
                "first_name": "Huesped",
                "last_name": "Demo",
                "email": "huesped@test.com",
                "rol": "huesped",
                "is_staff": True,
            },
        )
        guest.rol = "huesped"
        guest.is_staff = True
        guest.set_password("test123")
        guest.save()

        AgenteIAConfig.objects.update_or_create(
            nombre="Agente IA de Booking",
            defaults={
                "descripcion": (
                    "Asistente para administradores, anfitriones y huespedes. Consulta propiedades, "
                    "amenities, resenas, disponibilidad y reservas usando datos reales del backend."
                ),
                "system_prompt": SYSTEM_PROMPT,
                "endpoint_chat": "/api/agent/chat/",
                "endpoint_disponibilidad": "/api/availability/",
                "endpoint_reservas": "/api/reservations/",
                "endpoint_propiedades": "/api/properties/",
                "requiere_confirmacion_reserva": True,
                "activo": True,
            },
        )

        amenity_names = [
            "WIFI",
            "PISCINA",
            "COCINA COMPLETA",
            "TV SMART",
            "LAVADORA",
            "ESTACIONAMIENTO",
            "JARDIN",
            "AIRE ACONDICIONADO",
        ]
        amenities = {name: Amenity.objects.get_or_create(nombre=name)[0] for name in amenity_names}

        property_specs = [
            ("Casa cerca del centro", "Hermosa casa con vistas al centro de la ciudad", "Calle Principal 123", "Villarrica", "casa_entera", 6, True, False, False, "flexible", 150, 200, 50, ["WIFI", "PISCINA", "COCINA COMPLETA"]),
            ("Departamento moderno", "Depto moderno en zona residencial", "Avenida Independencia 456", "Asuncion", "habitacion_privada", 2, False, False, False, "moderada", 100, 150, 30, ["TV SMART", "LAVADORA", "ESTACIONAMIENTO", "JARDIN"]),
            ("Cabana en la montana", "Cabana tranquila rodeada de naturaleza", "Camino Rural 789", "Caacupe", "casa_entera", 4, True, False, False, "estricta", 80, 120, 40, ["PISCINA", "COCINA COMPLETA", "TV SMART"]),
            ("Quinta Guaira", "Quinta de descanso para familias y grupos chicos", "Ruta 8 km 4", "Villarrica", "casa_entera", 8, False, False, True, "moderada", 50000, 80000, 30000, ["WIFI", "PISCINA", "ESTACIONAMIENTO"]),
        ]

        properties = []
        for (
            title,
            description,
            street,
            city,
            property_type,
            guest_capacity,
            allows_pets,
            allows_smoking,
            allows_parties,
            cancellation_policy,
            week_price,
            weekend_price,
            cleaning_fee,
            names,
        ) in property_specs:
            prop, _ = Propiedad.objects.update_or_create(
                titulo=title,
                defaults={
                    "descripcion": description,
                    "calle": street,
                    "ubicacion": city,
                    "tipo_alojamiento": property_type,
                    "capacidad_maxima_huespedes": guest_capacity,
                    "precio_noche": Decimal(str(week_price)),
                    "precio_fin_semana": Decimal(str(weekend_price)),
                    "tarifa_limpieza": Decimal(str(cleaning_fee)),
                    "estado": "disponible",
                    "permite_mascotas": allows_pets,
                    "permite_fumar": allows_smoking,
                    "permite_fiestas": allows_parties,
                    "politica_cancelacion": cancellation_policy,
                    "id_anfitrion": host,
                },
            )
            properties.append(prop)
            prop.amenities.set(amenities[name] for name in names)

        pending_reservation, _ = Reserva.objects.get_or_create(
            id_propiedad=properties[0],
            id_huesped=guest,
            fecha_inicio=date(2026, 6, 20),
            fecha_fin=date(2026, 6, 22),
            defaults={"cantidad_huespedes": 2, "estado": "pendiente", "precio_total": Decimal("400.00")},
        )
        sync_reservation_availability(pending_reservation)

        review_reservation, _ = Reserva.objects.get_or_create(
            id_propiedad=properties[3],
            id_huesped=guest,
            fecha_inicio=date(2026, 5, 10),
            fecha_fin=date(2026, 5, 12),
            defaults={"cantidad_huespedes": 2, "estado": "confirmada", "precio_total": Decimal("190000.00")},
        )
        sync_reservation_availability(review_reservation)
        Review.objects.update_or_create(
            id_reserva=review_reservation,
            defaults={
                "id_propiedad": properties[3],
                "id_usuario": guest,
                "calificacion": 5,
                "comentario": "Excelente quinta, muy comoda y limpia.",
            },
        )

        for prop in properties:
            for offset in range(0, 45):
                Disponibilidad.objects.get_or_create(
                    id_propiedad=prop,
                    fecha=date(2026, 7, 1) + timedelta(days=offset),
                    defaults={"estado": "disponible"},
                )

        for reserva in Reserva.objects.filter(estado__in=["pendiente", "confirmada"]).select_related("id_propiedad"):
            sync_reservation_availability(reserva)

        self.stdout.write(self.style.SUCCESS("Datos de ejemplo cargados correctamente."))
