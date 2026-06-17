from datetime import datetime

from django.http import HttpResponse, JsonResponse
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from presupuesto import agent
from presupuesto.models import Amenity, Propiedad
from presupuesto.serializers import AmenitySerializer, PropiedadSerializer, ReservaSerializer
from presupuesto.services import create_reservation, get_available_properties, host_reservations


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
    queryset = Propiedad.objects.select_related('id_anfitrion').prefetch_related('amenities')
    serializer_class = PropiedadSerializer


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

        results = get_available_properties(
            start_date=start_date,
            end_date=end_date,
            guests=guests,
            property_id=property_id,
        )
        return Response({"count": len(results), "results": results})


class ReservationListCreateAPIView(APIView):
    """Lista reservas o crea una reserva usando las reglas del backend."""

    def get(self, request):
        reservations = host_reservations(
            host_id=request.query_params.get("host_id"),
            status=request.query_params.get("status"),
            month=request.query_params.get("month"),
        )
        serializer = ReservaSerializer(reservations, many=True)
        return Response({"count": reservations.count(), "results": serializer.data})

    def post(self, request):
        try:
            reserva = create_reservation(
                propiedad_id=request.data.get("id_propiedad"),
                huesped_id=request.data.get("id_huesped"),
                start_date=parse_query_date(request.data.get("fecha_inicio"), "fecha_inicio"),
                end_date=parse_query_date(request.data.get("fecha_fin"), "fecha_fin"),
                guests=int(request.data.get("cantidad_huespedes") or 1),
            )
        except Exception as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(ReservaSerializer(reserva).data, status=status.HTTP_201_CREATED)


class AgentChatAPIView(APIView):
    """Endpoint conversacional del agente IA."""

    def post(self, request):
        return Response(agent.chat(request.data))


class AgentSystemPromptAPIView(APIView):
    """Expone el prompt de sistema para documentar o configurar Dify/Botpress."""

    def get(self, request):
        return Response({"system_prompt": agent.SYSTEM_PROMPT})
