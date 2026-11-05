from django.urls import include, path
from rest_framework.routers import DefaultRouter
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView
from .api_sesion import CsrfVista, IngresoVista, RegistroVista, RenovacionVista, SalidaVista
from .api_vistas import AlojamientoViewSet, ReservaViewSet, ServicioViewSet, NotificacionViewSet, CuentaViewSet
from .views import AgentChatAPIView

router = DefaultRouter()
router.register('alojamientos', AlojamientoViewSet, basename='alojamiento-web')
router.register('reservas', ReservaViewSet, basename='reserva-web')
router.register('servicios', ServicioViewSet, basename='servicio-web')
router.register('notificaciones', NotificacionViewSet, basename='notificacion-web')
router.register('cuenta', CuentaViewSet, basename='cuenta-web')

urlpatterns = [
    path('auth/csrf/', CsrfVista.as_view()), path('auth/ingresar/', IngresoVista.as_view()),
    path('auth/registro/', RegistroVista.as_view()), path('auth/renovar/', RenovacionVista.as_view()),
    path('auth/salir/', SalidaVista.as_view()), path('asistente/', AgentChatAPIView.as_view()),
    path('esquema/', SpectacularAPIView.as_view(), name='esquema-web'),
    path('documentacion/', SpectacularSwaggerView.as_view(url_name='esquema-web')),
    path('redoc/', SpectacularRedocView.as_view(url_name='esquema-web')),
    path('', include(router.urls)),
]
