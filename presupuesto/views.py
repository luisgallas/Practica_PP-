from datetime import datetime

from django.contrib.auth import authenticate
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from presupuesto import agent
from presupuesto.authentication import create_jwt_for_user
from presupuesto.models import Amenity, HistorialPropiedadVisitada, Notificacion, Propiedad, Reserva
from presupuesto.permissions import can_cancel_reservation, can_manage_reservation
from presupuesto.serializers import (
    AmenitySerializer,
    HistorialPropiedadVisitadaSerializer,
    NotificacionSerializer,
    PropiedadSerializer,
    ReservaSerializer,
    UsuarioSerializer,
)
from presupuesto.services import (
    cancel_reservation,
    create_reservation,
    get_available_properties,
    host_reservations,
    record_property_visit,
    update_reservation_status,
)


def home(request):
    """Pagina principal del backend."""
    propiedades_count = Propiedad.objects.count()
    html = f"""
    <!doctype html>
    <html lang="es">
    <head>
        <meta charset="utf-8">
        <title>Practica PP - Booking</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; line-height: 1.5; }}
            code {{ background: #f2f2f2; padding: 2px 6px; border-radius: 4px; }}
            li {{ margin: 8px 0; }}
        </style>
    </head>
    <body>
        <h1>Practica PP - Booking con agente IA</h1>
        <p>Backend Django funcionando. Propiedades cargadas: <strong>{propiedades_count}</strong>.</p>
        <h2>Endpoints principales</h2>
        <ul>
            <li><a href="/api/health/">/api/health/</a> - salud del backend</li>
            <li><a href="/api/properties/">/api/properties/</a> - propiedades</li>
            <li><a href="/api/availability/?start_date=2026-07-20&end_date=2026-07-25&guests=2">/api/availability/</a> - disponibilidad</li>
            <li><a href="/api/agent/system-prompt/">/api/agent/system-prompt/</a> - system prompt</li>
            <li><code>POST /api/agent/chat/</code> - chat del agente</li>
        </ul>
        <p>Para probar el chat con POST, usa <code>docs/demo_requests.http</code> o <code>scripts/demo_agent.ps1</code>.</p>
    </body>
    </html>
    """
    return HttpResponse(html)


def api_info(request):
    """Endpoint basico de informacion."""
    return JsonResponse({
        'mensaje': 'API Practica PP',
        'version': '1.0.0',
    })


class PropiedadListAPIView(generics.ListAPIView): #hereda de ListAPIView para listar objetos
    """Lista todas las propiedades."""
    queryset = Propiedad.objects.select_related('id_anfitrion').prefetch_related('amenities') #optimiza consultas a la base de datos
    serializer_class = PropiedadSerializer #especifica el serializer a usar para convertir objetos a JSON


class PropiedadDetailAPIView(generics.RetrieveAPIView):
    """Muestra el detalle de una propiedad."""
    queryset = Propiedad.objects.select_related('id_anfitrion').prefetch_related('amenities', 'fotos')
    serializer_class = PropiedadSerializer

    def get_object(self):
        propiedad = super().get_object()
        record_property_visit(self.request.user, propiedad)
        return propiedad


class AmenityListAPIView(generics.ListAPIView):
    """Lista amenities cargados en el sistema."""
    queryset = Amenity.objects.order_by("nombre")
    serializer_class = AmenitySerializer


def parse_query_date(value, field_name):
    if not value:
        raise ValueError(f"El parametro {field_name} es obligatorio.")
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError as exc:
        raise ValueError(f"El parametro {field_name} debe tener formato YYYY-MM-DD.") from exc


class AvailabilityAPIView(APIView):
    """Consulta disponibilidad real de propiedades para un rango de fechas."""

    def get(self, request):
        try:
            start_date = parse_query_date(request.query_params.get("start_date"), "start_date")
            end_date = parse_query_date(request.query_params.get("end_date"), "end_date")
            guests = int(request.query_params.get("guests") or 1)
            property_id = request.query_params.get("property_id")
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        if end_date <= start_date:
            return Response(
                {"detail": "end_date debe ser posterior a start_date."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if start_date < timezone.localdate():
            return Response(
                {"detail": "start_date no puede ser una fecha pasada."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        results = get_available_properties(
            start_date=start_date,
            end_date=end_date,
            guests=guests,
            property_id=property_id,
        )
        return Response({"count": len(results), "results": results})


class ReservationListCreateAPIView(APIView):
    """Lista reservas o crea una reserva usando las reglas del backend."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        if request.user.rol == "anfitrion":
            reservations = host_reservations(
                host_id=request.user.id,
                status=request.query_params.get("status"),
                month=request.query_params.get("month"),
            )
        elif request.user.rol == "huesped":
            reservations = Reserva.objects.filter(id_huesped=request.user).select_related(
                "id_propiedad", "id_huesped", "id_propiedad__id_anfitrion"
            ).order_by("-fecha_inicio")
        else:
            reservations = host_reservations(
                host_id=request.query_params.get("host_id"),
                status=request.query_params.get("status"),
                month=request.query_params.get("month"),
            )
        serializer = ReservaSerializer(reservations, many=True)
        return Response({"count": reservations.count(), "results": serializer.data})

    def post(self, request):
        if request.user.rol not in ["huesped", "admin"]:
            return Response(
                {"detail": "Solo un huesped o admin puede crear reservas."},
                status=status.HTTP_403_FORBIDDEN,
            )

        guest_id = request.data.get("id_huesped") if request.user.rol == "admin" else request.user.id
        try:
            reserva = create_reservation(
                propiedad_id=request.data.get("id_propiedad"),
                huesped_id=guest_id,
                start_date=parse_query_date(request.data.get("fecha_inicio"), "fecha_inicio"),
                end_date=parse_query_date(request.data.get("fecha_fin"), "fecha_fin"),
                guests=int(request.data.get("cantidad_huespedes") or 1),
            )
        except Exception as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(ReservaSerializer(reserva).data, status=status.HTTP_201_CREATED)


class ReservationStatusAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        reserva = Reserva.objects.select_related("id_propiedad__id_anfitrion", "id_huesped").get(pk=pk)
        if not can_manage_reservation(request.user, reserva):
            return Response({"detail": "No tenes permiso para cambiar esta reserva."}, status=status.HTTP_403_FORBIDDEN)

        try:
            reserva = update_reservation_status(reserva, request.data.get("estado"))
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(ReservaSerializer(reserva).data)


class ReservationCancelAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        reserva = Reserva.objects.select_related("id_propiedad__id_anfitrion", "id_huesped").get(pk=pk)
        if not can_cancel_reservation(request.user, reserva):
            return Response({"detail": "No tenes permiso para cancelar esta reserva."}, status=status.HTTP_403_FORBIDDEN)

        try:
            reserva = cancel_reservation(
                reserva,
                cancelled_by=request.user,
                reason=request.data.get("motivo", ""),
            )
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(ReservaSerializer(reserva).data)


class AuthLoginAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        username = request.data.get("username")
        password = request.data.get("password")
        user = authenticate(request, username=username, password=password)
        if not user:
            return Response({"detail": "Credenciales invalidas."}, status=status.HTTP_400_BAD_REQUEST)
        return Response({
            "access": create_jwt_for_user(user),
            "token_type": "Bearer",
            "expires_in": 3600,
            "user": UsuarioSerializer(user).data,
        })


class MeAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return Response(UsuarioSerializer(request.user).data)


class NotificationListAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        notifications = Notificacion.objects.filter(id_usuario=request.user).order_by("-fecha")
        return Response({
            "count": notifications.count(),
            "results": NotificacionSerializer(notifications, many=True).data,
        })


class GuestHistoryAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        if request.user.rol != "huesped":
            return Response({"detail": "Solo huespedes pueden ver este historial."}, status=status.HTTP_403_FORBIDDEN)
        history = HistorialPropiedadVisitada.objects.filter(id_usuario=request.user).select_related(
            "id_propiedad", "id_propiedad__id_anfitrion"
        )
        return Response({
            "count": history.count(),
            "results": HistorialPropiedadVisitadaSerializer(history, many=True, context={"request": request}).data,
        })


class HostDashboardAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        if request.user.rol != "anfitrion":
            return Response({"detail": "Solo anfitriones pueden ver este panel."}, status=status.HTTP_403_FORBIDDEN)
        reservations = Reserva.objects.filter(id_propiedad__id_anfitrion=request.user)
        month = datetime.today().month
        year = datetime.today().year
        reservations_month = reservations.filter(fecha_inicio__year=year, fecha_inicio__month=month)
        nights_reserved = sum((r.fecha_fin - r.fecha_inicio).days for r in reservations.filter(estado__in=["confirmada", "activa", "completada"]))
        total_properties = Propiedad.objects.filter(id_anfitrion=request.user).count()
        occupancy_rate = 0 if total_properties == 0 else round((nights_reserved / (total_properties * 30)) * 100, 2)
        return Response({
            "propiedades": total_properties,
            "reservas_pendientes": reservations.filter(estado="pendiente").count(),
            "reservas_mes": reservations_month.count(),
            "ingresos_simulados": reservations.filter(estado__in=["confirmada", "activa", "completada"]).aggregate(total=Sum("precio_total"))["total"] or 0,
            "tasa_ocupacion_estimada": occupancy_rate,
            "reviews_recibidas": Review.objects.filter(id_propiedad__id_anfitrion=request.user).count(),
        })


class AgentChatAPIView(APIView):
    """Endpoint conversacional del agente IA."""

    def post(self, request):
        return Response(agent.chat(request.data))


class AgentSystemPromptAPIView(APIView):
    """Expone el prompt de sistema para documentar o configurar Dify/Botpress."""

    def get(self, request):
        return Response({"system_prompt": agent.SYSTEM_PROMPT})
