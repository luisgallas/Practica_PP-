from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path
from rest_framework.response import Response
from rest_framework.views import APIView

from presupuesto.views import home #devuelve una pagina html con el mensaje de bienvenida al proyecto


class HealthView(APIView): #APIVeew viene de Djnado Rest framword  que responde cuando alguine hace una peticion
    def get(self, request):
        return Response({"status": "ok", "service": "booking-api"})


urlpatterns = [
    path('api/v1/', include('presupuesto.api_urls')),
    path("", home, name="home"),
    path("admin/", admin.site.urls), #activa el panel de administracion de Django
    path("api/health/", HealthView.as_view(), name="health"), #ruta para verificar el estado del servicio
    path("api/salud/", HealthView.as_view(), name="salud"), #
    path("api/", include("presupuesto.urls")), #esto conecta las rutas de la app presupuesto  
    path("API/", include("presupuesto.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
