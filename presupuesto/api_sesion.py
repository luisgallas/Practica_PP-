"""Access token en memoria del cliente y renovación revocable en cookie HttpOnly."""
from django.conf import settings
from django.contrib.auth import authenticate
from django.middleware.csrf import get_token, rotate_token
from django.db import transaction
from rest_framework import serializers
from rest_framework.authentication import SessionAuthentication
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework_simplejwt.tokens import RefreshToken, TokenError
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken
from .api_serializadores import IngresoSerializer, RegistroSerializer
from .serializers import UsuarioSerializer

NOMBRE_COOKIE = 'hospeda_renovacion'
RUTA_COOKIE = '/api/v1/auth/'


class LimiteIngreso(AnonRateThrottle):
    scope = 'ingreso'


def guardar_cookie(respuesta, token):
    respuesta.set_cookie(NOMBRE_COOKIE, str(token), max_age=86400, httponly=True,
                         secure=not settings.DEBUG, samesite=settings.REFRESH_COOKIE_SAMESITE, path=RUTA_COOKIE)
    respuesta['Cache-Control'] = 'no-store'
    return respuesta


class VistaSesion(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []
    throttle_classes = [LimiteIngreso]
    serializer_class = IngresoSerializer

    def proteger(self, request):
        SessionAuthentication().enforce_csrf(request)


class CsrfVista(VistaSesion):
    throttle_classes = [AnonRateThrottle]

    @extend_schema(responses=inline_serializer('TokenCsrf', {'csrfToken': serializers.CharField()}))
    def get(self, request):
        respuesta = Response({'csrfToken': get_token(request)})
        respuesta['Cache-Control'] = 'no-store'
        return respuesta


class IngresoVista(VistaSesion):
    @extend_schema(request=IngresoSerializer, responses=inline_serializer('SesionIniciada', {'access': serializers.CharField(), 'usuario': UsuarioSerializer(), 'csrfToken': serializers.CharField()}))
    def post(self, request):
        self.proteger(request)
        datos = IngresoSerializer(data=request.data)
        datos.is_valid(raise_exception=True)
        usuario = authenticate(request, **datos.validated_data)
        if usuario is None:
            raise AuthenticationFailed('Usuario o contraseña incorrectos.')
        rotate_token(request)
        token = RefreshToken.for_user(usuario)
        return guardar_cookie(Response({'access': str(token.access_token), 'usuario': UsuarioSerializer(usuario).data,
                                        'csrfToken': get_token(request)}), token)


class RegistroVista(VistaSesion):
    serializer_class = RegistroSerializer

    @extend_schema(request=RegistroSerializer, responses={201: UsuarioSerializer})
    def post(self, request):
        self.proteger(request)
        datos = RegistroSerializer(data=request.data)
        datos.is_valid(raise_exception=True)
        usuario = datos.save()
        return Response(UsuarioSerializer(usuario).data, status=201)


class RenovacionVista(VistaSesion):
    throttle_classes = [AnonRateThrottle]

    @extend_schema(request=None, responses=inline_serializer('AccesoRenovado', {'access': serializers.CharField()}))
    def post(self, request):
        self.proteger(request)
        valor = request.COOKIES.get(NOMBRE_COOKIE)
        if not valor:
            raise AuthenticationFailed('Iniciá sesión para continuar.')
        try:
            # Impide reutilizar simultáneamente la misma renovación en PostgreSQL.
            with transaction.atomic():
                token = RefreshToken(valor)
                OutstandingToken.objects.select_for_update().get(jti=token['jti'])
                datos = TokenRefreshSerializer(data={'refresh': valor})
                datos.is_valid(raise_exception=True)
                resultado = datos.validated_data
        except (TokenError, OutstandingToken.DoesNotExist) as error:
            raise AuthenticationFailed('La sesión venció. Iniciá sesión nuevamente.') from error
        return guardar_cookie(Response({'access': resultado['access']}), resultado['refresh'])


class SalidaVista(VistaSesion):
    throttle_classes = [AnonRateThrottle]

    @extend_schema(request=None, responses={204: None})
    def post(self, request):
        self.proteger(request)
        try:
            RefreshToken(request.COOKIES.get(NOMBRE_COOKIE, '')).blacklist()
        except TokenError:
            pass
        respuesta = Response(status=204)
        respuesta.delete_cookie(NOMBRE_COOKIE, path=RUTA_COOKIE, samesite=settings.REFRESH_COOKIE_SAMESITE)
        respuesta['Cache-Control'] = 'no-store'
        return respuesta
