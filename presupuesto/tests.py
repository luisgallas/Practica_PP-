from datetime import date

from django.test import TestCase
from rest_framework.test import APIClient

from .models import Amenity, Disponibilidad, Propiedad, Reserva, Review, Usuario


class AgentApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin_user = Usuario.objects.create_user(username="admin_user", password="x", rol="admin")
        self.host = Usuario.objects.create_user(username="host", password="x", rol="anfitrion")
        self.guest = Usuario.objects.create_user(username="guest", password="x", rol="huesped")
        self.property = Propiedad.objects.create(
            titulo="Quinta XS",
            descripcion="Quinta para descanso",
            calle="Ruta 8 km 4",
            ubicacion="Villarrica",
            precio_noche=100,
            precio_fin_semana=150,
            tarifa_limpieza=30,
            estado="disponible",
            id_anfitrion=self.host,
        )
        wifi = Amenity.objects.create(nombre="WiFi")
        self.property.amenities.add(wifi)

    def test_availability_endpoint_returns_real_property(self):
        response = self.client.get(
            "/api/availability/",
            {"start_date": "2026-07-20", "end_date": "2026-07-25", "guests": 2},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["titulo"], "Quinta XS")

    def test_agent_requires_confirmation_before_creating_reservation(self):
        response = self.client.post(
            "/api/agent/chat/",
            {
                "message": "Quiero reservar esta propiedad para el 15 de agosto en la Quinta XS",
                "user_id": self.guest.id,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["intent"], "create_reservation_needs_confirmation")
        self.assertEqual(Reserva.objects.count(), 0)

        confirmation = self.client.post(
            "/api/agent/chat/",
            {
                "message": "confirmo",
                "confirm": True,
                "pending_action": response.data["pending_action"],
            },
            format="json",
        )

        self.assertEqual(confirmation.status_code, 200)
        self.assertEqual(confirmation.data["intent"], "create_reservation_confirmed")
        self.assertEqual(Reserva.objects.count(), 1)
        disponibilidad = Disponibilidad.objects.get(
            id_propiedad=self.property,
            fecha=date(2026, 8, 15),
        )
        reserva = Reserva.objects.get()
        self.assertEqual(disponibilidad.estado, "reservada")
        self.assertEqual(disponibilidad.fecha_inicio_reserva, date(2026, 8, 15))
        self.assertEqual(disponibilidad.id_reserva, reserva)

    def test_agent_understands_natural_reservation_request_with_slash_dates(self):
        response = self.client.post(
            "/api/agent/chat/",
            {
                "message": (
                    "Podrias hacerme una reserva en Quinta XS para la fecha "
                    "18/06/2026 hasta 19/06/2026, con TV Smart y TELEFONO"
                ),
                "user_id": self.guest.id,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["intent"], "create_reservation_needs_confirmation")
        self.assertEqual(response.data["pending_action"]["data"]["start_date"], "2026-06-18")
        self.assertEqual(response.data["pending_action"]["data"]["end_date"], "2026-06-19")
        self.assertIn("Quinta XS", response.data["reply"])

    def test_agent_understands_written_date_range_with_repeated_month(self):
        response = self.client.post(
            "/api/agent/chat/",
            {
                "message": (
                    "Podrias reservarme una reserva en Quinta XS para el 7 de julio "
                    "al 9 de julio del 2026, con TV y aire acondicionado"
                ),
                "user_id": self.guest.id,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["intent"], "create_reservation_needs_confirmation")
        self.assertEqual(response.data["pending_action"]["data"]["start_date"], "2026-07-07")
        self.assertEqual(response.data["pending_action"]["data"]["end_date"], "2026-07-09")
        self.assertIn("del 2026-07-07 al 2026-07-09", response.data["reply"])

    def test_agent_understands_desde_hasta_date_range(self):
        response = self.client.post(
            "/api/agent/chat/",
            {
                "message": (
                    "Podrias reservarme Quinta XS desde el 10 hasta el 14 "
                    "de julio del 2026"
                ),
                "user_id": self.guest.id,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["intent"], "create_reservation_needs_confirmation")
        self.assertEqual(response.data["pending_action"]["data"]["start_date"], "2026-07-10")
        self.assertEqual(response.data["pending_action"]["data"]["end_date"], "2026-07-14")
        self.assertIn("del 2026-07-10 al 2026-07-14", response.data["reply"])

    def test_host_pending_summary(self):
        Reserva.objects.create(
            id_propiedad=self.property,
            id_huesped=self.guest,
            fecha_inicio=date(2026, 6, 16),
            fecha_fin=date(2026, 6, 18),
            cantidad_huespedes=2,
            estado="pendiente",
            precio_total=230,
        )

        response = self.client.post(
            "/api/agent/chat/",
            {"message": "Hay reservas pendientes de confirmar?", "user_id": self.host.id},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["intent"], "reservations")
        self.assertIn("1 reserva", response.data["reply"])

    def test_host_question_with_guest_user_explains_wrong_role(self):
        response = self.client.post(
            "/api/agent/chat/",
            {"message": "Cuantas reservas tengo en total?", "user_id": self.guest.id},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["intent"], "host_wrong_role")
        self.assertIn("rol Huesped", response.data["reply"])

    def test_admin_user_can_ask_global_reservation_count(self):
        Reserva.objects.create(
            id_propiedad=self.property,
            id_huesped=self.guest,
            fecha_inicio=date(2026, 6, 16),
            fecha_fin=date(2026, 6, 18),
            cantidad_huespedes=2,
            estado="pendiente",
            precio_total=230,
        )

        response = self.client.post(
            "/api/agent/chat/",
            {"message": "Cuantas reservas hay en total?", "user_id": self.admin_user.id},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["intent"], "reservation_count")
        self.assertEqual(response.data["data"]["scope"], "admin")
        self.assertIn("en todo el sistema", response.data["reply"])

    def test_agent_answers_property_reviews(self):
        reserva = Reserva.objects.create(
            id_propiedad=self.property,
            id_huesped=self.guest,
            fecha_inicio=date(2026, 7, 1),
            fecha_fin=date(2026, 7, 3),
            cantidad_huespedes=2,
            estado="confirmada",
            precio_total=230,
        )
        Review.objects.create(
            id_propiedad=self.property,
            id_usuario=self.guest,
            id_reserva=reserva,
            calificacion=5,
            comentario="Excelente quinta, muy comoda.",
        )

        response = self.client.post(
            "/api/agent/chat/",
            {"message": "Que resenas tiene la Quinta XS?"},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["intent"], "property_reviews")
        self.assertEqual(response.data["data"]["count"], 1)
        self.assertIn("5.0/5", response.data["reply"])
