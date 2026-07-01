from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path
from rest_framework.response import Response
from rest_framework.views import APIView

from presupuesto.views import home


class HealthView(APIView):
    def get(self, request):
        return Response({"status": "ok", "service": "booking-api"})


urlpatterns = [
    path("", home, name="home"),
    path("admin/", admin.site.urls),
    path("api/health/", HealthView.as_view(), name="health"),
    path("api/salud/", HealthView.as_view(), name="salud"),
    path("api/", include("presupuesto.urls")),
    path("API/", include("presupuesto.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
