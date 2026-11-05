"""API versionada: consultas acotadas y autorización por objeto en el servidor."""
from django.core.exceptions import ValidationError as ErrorDjango
from django.db import transaction
from django.db.models import Avg, Count, Exists, OuterRef, Q, Sum
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import permissions, serializers, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.pagination import PageNumberPagination
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle
from drf_spectacular.utils import extend_schema, OpenApiParameter

from .api_serializadores import (AlojamientoSerializer, CrearReservaSerializer, FechasSerializer,
    ReservaWebSerializer, ResenaSerializer, EstadoReservaSerializer, CancelacionSerializer, CotizacionSerializer, PanelSerializer)
from .imagenes import preparar_imagen
from .models import Amenity, Disponibilidad, Favorito, Notificacion, Propiedad, PropiedadFoto, Reserva, Review, Usuario
from .serializers import AmenitySerializer, NotificacionSerializer, PropiedadFotoSerializer, UsuarioSerializer
from .services import (BLOCKING_RESERVATION_STATES, calculate_price, cancel_reservation, create_reservation,
    has_guest_capacity, is_property_available, record_property_visit, update_reservation_status)


class PaginacionWeb(PageNumberPagination):
    page_size = 12
    page_size_query_param = 'tamano'
    max_page_size = 48


def alojamientos_consulta():
    return Propiedad.objects.select_related('id_anfitrion').prefetch_related('amenities', 'fotos').annotate(
        puntuacion=Avg('review__calificacion'), cantidad_resenas=Count('review', distinct=True)).order_by('-id')


def exigir_gestion(usuario, propiedad):
    if not usuario.is_authenticated or not (usuario.rol == 'admin' or (usuario.rol == 'anfitrion' and propiedad.id_anfitrion_id == usuario.id)):
        raise PermissionDenied('No tenés permiso para gestionar este alojamiento.')


class LimiteFotos(UserRateThrottle):
    scope = 'fotos'


class CargaFotosSerializer(serializers.Serializer):
    fotos = serializers.ListField(child=serializers.FileField(), min_length=1, max_length=5)


class AlojamientoViewSet(viewsets.ModelViewSet):
    serializer_class = AlojamientoSerializer
    pagination_class = PaginacionWeb
    http_method_names = ['get', 'post', 'patch', 'delete', 'head', 'options']

    def get_permissions(self):
        return [permissions.AllowAny()] if self.action in ['list', 'retrieve', 'disponibilidad', 'resenas'] and self.request.method == 'GET' else [permissions.IsAuthenticated()]

    def get_queryset(self):
        consulta = alojamientos_consulta()
        usuario = self.request.user
        propia = self.request.query_params.get('mios') == '1'
        if propia:
            if not usuario.is_authenticated or usuario.rol not in ['anfitrion', 'admin']:
                raise PermissionDenied('Esta vista es exclusiva de anfitriones y administradores.')
            if usuario.rol == 'anfitrion':
                consulta = consulta.filter(id_anfitrion=usuario)
        elif self.action == 'list' or not usuario.is_authenticated or usuario.rol == 'huesped':
            consulta = consulta.filter(estado='disponible')
        elif usuario.rol == 'anfitrion':
            consulta = consulta.filter(Q(estado='disponible') | Q(id_anfitrion=usuario))
        if self.action != 'list':
            return consulta
        parametros = self.request.query_params
        if parametros.get('ciudad'):
            consulta = consulta.filter(ubicacion__icontains=parametros['ciudad'][:255])
        if parametros.get('tipo'):
            consulta = consulta.filter(tipo_alojamiento=parametros['tipo'])
        for nombre, filtro in [('precio_max', 'precio_noche__lte'), ('huespedes', 'capacidad_maxima_huespedes__gte'), ('puntaje', 'puntuacion__gte')]:
            if parametros.get(nombre):
                valor = serializers.IntegerField(min_value=0, max_value=999999999999).run_validation(parametros[nombre])
                consulta = consulta.filter(**{filtro: valor})
        for servicio in parametros.getlist('servicio')[:20]:
            identificador = serializers.IntegerField(min_value=1).run_validation(servicio)
            consulta = consulta.filter(amenities__id=identificador)
        if parametros.get('desde') or parametros.get('hasta'):
            fechas = FechasSerializer(data=parametros)
            fechas.is_valid(raise_exception=True)
            desde, hasta = fechas.validated_data['desde'], fechas.validated_data['hasta']
            ocupadas = Reserva.objects.filter(id_propiedad=OuterRef('pk'), estado__in=BLOCKING_RESERVATION_STATES, fecha_inicio__lt=hasta, fecha_fin__gt=desde)
            bloqueadas = Disponibilidad.objects.filter(id_propiedad=OuterRef('pk'), estado__in=['bloqueada', 'reservada'], fecha__gte=desde, fecha__lt=hasta)
            consulta = consulta.filter(~Exists(ocupadas), ~Exists(bloqueadas))
        orden = {'precio': 'precio_noche', '-precio': '-precio_noche', 'puntaje': '-puntuacion'}.get(parametros.get('orden'), '-id')
        return consulta.order_by(orden, '-id').distinct()

    @extend_schema(parameters=[OpenApiParameter(nombre, str) for nombre in ['ciudad', 'tipo', 'precio_max', 'huespedes', 'puntaje', 'servicio', 'desde', 'hasta', 'orden', 'mios']])
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        propiedad = self.get_object()
        record_property_visit(request.user, propiedad)
        return Response(self.get_serializer(propiedad).data)

    def perform_create(self, serializer):
        if self.request.user.rol != 'anfitrion':
            raise PermissionDenied('Solo un anfitrión puede publicar alojamientos.')
        serializer.save(id_anfitrion=self.request.user)

    def perform_update(self, serializer):
        exigir_gestion(self.request.user, serializer.instance)
        serializer.save()

    def perform_destroy(self, instance):
        exigir_gestion(self.request.user, instance)
        raise ValidationError('Pausá o desactivá el alojamiento para conservar el historial de reservas.')

    @extend_schema(responses=CotizacionSerializer, parameters=[OpenApiParameter('desde', str, required=True), OpenApiParameter('hasta', str, required=True), OpenApiParameter('huespedes', int)])
    @action(detail=True, methods=['get'])
    def disponibilidad(self, request, pk=None):
        propiedad = self.get_object()
        fechas = FechasSerializer(data=request.query_params)
        fechas.is_valid(raise_exception=True)
        datos = fechas.validated_data
        disponible = is_property_available(propiedad, datos['desde'], datos['hasta']) and has_guest_capacity(propiedad, datos['huespedes'])
        return Response({'disponible': disponible, 'noches': (datos['hasta'] - datos['desde']).days,
                         'total': str(calculate_price(propiedad, datos['desde'], datos['hasta'])),
                         'limpieza': str(propiedad.tarifa_limpieza)})

    @extend_schema(request=CargaFotosSerializer, responses=PropiedadFotoSerializer(many=True))
    @action(detail=True, methods=['post'], parser_classes=[MultiPartParser], throttle_classes=[LimiteFotos])
    def fotos(self, request, pk=None):
        propiedad = self.get_object()
        exigir_gestion(request.user, propiedad)
        datos = CargaFotosSerializer(data={'fotos': request.FILES.getlist('fotos')})
        datos.is_valid(raise_exception=True)
        creadas = []
        try:
            preparadas = [preparar_imagen(archivo) for archivo in datos.validated_data['fotos']]
            with transaction.atomic():
                Propiedad.objects.select_for_update().get(pk=propiedad.pk)
                existentes = PropiedadFoto.objects.filter(propiedad=propiedad).count()
                if existentes + len(preparadas) > 5:
                    raise ValidationError('El alojamiento admite hasta 5 fotos en total.')
                for indice, archivo in enumerate(preparadas):
                    foto = PropiedadFoto(propiedad=propiedad, foto=archivo, es_portada=existentes == 0 and indice == 0)
                    foto.save()
                    creadas.append(foto)
        except Exception as error:
            for foto in creadas:
                foto.foto.delete(save=False)
            if isinstance(error, ErrorDjango):
                raise ValidationError(error.messages)
            raise
        return Response(PropiedadFotoSerializer(creadas, many=True, context={'request': request}).data, status=201)

    @action(detail=True, methods=['delete'], url_path=r'fotos/(?P<foto_id>\d+)')
    def eliminar_foto(self, request, pk=None, foto_id=None):
        propiedad = self.get_object()
        exigir_gestion(request.user, propiedad)
        with transaction.atomic():
            Propiedad.objects.select_for_update().get(pk=propiedad.pk)
            foto = get_object_or_404(PropiedadFoto, pk=foto_id, propiedad=propiedad)
            archivo = foto.foto
            foto.delete()
            transaction.on_commit(lambda: archivo.delete(save=False))
            restantes = PropiedadFoto.objects.filter(propiedad=propiedad)
            primera = restantes.first()
            if primera and not restantes.filter(es_portada=True).exists():
                primera.es_portada = True
                primera.save(update_fields=['es_portada'])
        return Response(status=204)

    @action(detail=True, methods=['patch'], url_path=r'fotos/(?P<foto_id>\d+)/portada')
    def portada(self, request, pk=None, foto_id=None):
        propiedad = self.get_object()
        exigir_gestion(request.user, propiedad)
        foto = get_object_or_404(PropiedadFoto, pk=foto_id, propiedad=propiedad)
        foto.es_portada = True
        foto.save(update_fields=['es_portada'])
        return Response(PropiedadFotoSerializer(foto, context={'request': request}).data)

    @extend_schema(methods=['GET'], responses=ResenaSerializer(many=True))
    @extend_schema(methods=['POST'], request=ResenaSerializer, responses=ResenaSerializer)
    @action(detail=True, methods=['get', 'post'])
    def resenas(self, request, pk=None):
        propiedad = self.get_object()
        if request.method == 'GET':
            consulta = Review.objects.filter(id_propiedad=propiedad).select_related('id_usuario').order_by('-fecha')
            pagina = self.paginate_queryset(consulta)
            return self.get_paginated_response(ResenaSerializer(pagina, many=True).data)
        if request.user.rol != 'huesped':
            raise PermissionDenied('Solo huéspedes pueden publicar reseñas.')
        datos = ResenaSerializer(data=request.data)
        datos.is_valid(raise_exception=True)
        with transaction.atomic():
            reserva = get_object_or_404(Reserva.objects.select_for_update(), pk=datos.validated_data['id_reserva'].pk,
                id_huesped=request.user, id_propiedad=propiedad, estado='completada', fecha_fin__lte=timezone.localdate())
            if Review.objects.filter(id_reserva=reserva).exists():
                raise ValidationError('Ya publicaste una reseña de esta estadía.')
            datos.save(id_usuario=request.user, id_propiedad=propiedad)
        return Response(datos.data, status=201)

    @extend_schema(request=None, responses={200: {'type': 'object', 'properties': {'guardado': {'type': 'boolean'}}}, 204: None})
    @action(detail=True, methods=['get', 'post', 'delete'])
    def favorito(self, request, pk=None):
        propiedad = self.get_object()
        if request.user.rol != 'huesped':
            raise PermissionDenied('Los favoritos están disponibles para huéspedes.')
        if request.method == 'GET':
            return Response({'guardado': Favorito.objects.filter(usuario=request.user, propiedad=propiedad).exists()})
        if request.method == 'POST':
            Favorito.objects.get_or_create(usuario=request.user, propiedad=propiedad)
        else:
            Favorito.objects.filter(usuario=request.user, propiedad=propiedad).delete()
        return Response(status=204)


class ReservaViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Reserva.objects.none()
    serializer_class = ReservaWebSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = PaginacionWeb

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Reserva.objects.none()
        usuario = self.request.user
        consulta = Reserva.objects.select_related('id_propiedad__id_anfitrion', 'id_huesped').prefetch_related('id_propiedad__fotos', 'id_propiedad__amenities').annotate(tiene_resena=Exists(Review.objects.filter(id_reserva=OuterRef('pk'))))
        if usuario.rol == 'huesped':
            consulta = consulta.filter(id_huesped=usuario)
        elif usuario.rol == 'anfitrion':
            consulta = consulta.filter(id_propiedad__id_anfitrion=usuario)
        elif usuario.rol != 'admin':
            return consulta.none()
        if self.request.query_params.get('estado'):
            consulta = consulta.filter(estado=self.request.query_params['estado'])
        return consulta.order_by('-id')

    @extend_schema(request=CrearReservaSerializer, responses=ReservaWebSerializer)
    def create(self, request):
        if request.user.rol != 'huesped':
            raise PermissionDenied('Ingresá como huésped para reservar.')
        datos = CrearReservaSerializer(data=request.data)
        datos.is_valid(raise_exception=True)
        valores = datos.validated_data
        try:
            reserva = create_reservation(valores['alojamiento'].pk, request.user.pk, valores['desde'], valores['hasta'], valores['huespedes'])
        except ValueError as error:
            raise ValidationError(str(error))
        return Response(self.get_serializer(reserva).data, status=201)

    @extend_schema(request=EstadoReservaSerializer)
    @action(detail=True, methods=['post'])
    def estado(self, request, pk=None):
        reserva = self.get_object()
        exigir_gestion(request.user, reserva.id_propiedad)
        datos = EstadoReservaSerializer(data=request.data)
        datos.is_valid(raise_exception=True)
        try:
            reserva = update_reservation_status(reserva, datos.validated_data['estado'])
        except ValueError as error:
            raise ValidationError(str(error))
        return Response(self.get_serializer(reserva).data)

    @extend_schema(request=CancelacionSerializer)
    @action(detail=True, methods=['post'])
    def cancelar(self, request, pk=None):
        reserva = self.get_object()
        datos = CancelacionSerializer(data=request.data)
        datos.is_valid(raise_exception=True)
        try:
            reserva = cancel_reservation(reserva, request.user, datos.validated_data.get('motivo', ''))
        except ValueError as error:
            raise ValidationError(str(error))
        return Response(self.get_serializer(reserva).data)


class ServicioViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Amenity.objects.order_by('nombre')
    serializer_class = AmenitySerializer
    pagination_class = PaginacionWeb


class NotificacionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Notificacion.objects.none()
    serializer_class = NotificacionSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = PaginacionWeb

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Notificacion.objects.none()
        return Notificacion.objects.filter(id_usuario=self.request.user).order_by('-fecha')

    @action(detail=True, methods=['post'])
    def leer(self, request, pk=None):
        aviso = self.get_object()
        aviso.estado = 'leida'
        aviso.save(update_fields=['estado'])
        return Response(self.get_serializer(aviso).data)


class CuentaViewSet(viewsets.GenericViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UsuarioSerializer
    pagination_class = PaginacionWeb

    @action(detail=False, methods=['get'])
    def perfil(self, request):
        return Response(UsuarioSerializer(request.user).data)

    @extend_schema(responses=AlojamientoSerializer(many=True))
    @action(detail=False, methods=['get'])
    def favoritos(self, request):
        pagina = self.paginate_queryset(alojamientos_consulta().filter(favoritos__usuario=request.user, estado='disponible'))
        return self.get_paginated_response(AlojamientoSerializer(pagina, many=True, context={'request': request}).data)

    @extend_schema(responses=PanelSerializer)
    @action(detail=False, methods=['get'])
    def panel(self, request):
        usuario = request.user
        if usuario.rol not in ['admin', 'anfitrion']:
            raise PermissionDenied('Este panel es para anfitriones y administradores.')
        propiedades = Propiedad.objects.all()
        reservas = Reserva.objects.all()
        if usuario.rol == 'anfitrion':
            propiedades = propiedades.filter(id_anfitrion=usuario)
            reservas = reservas.filter(id_propiedad__id_anfitrion=usuario)
        datos = {'alojamientos': propiedades.count(), 'reservas': reservas.count(), 'pendientes': reservas.filter(estado='pendiente').count(),
                 'ingresos_simulados': reservas.filter(estado__in=['confirmada', 'activa', 'completada']).aggregate(total=Sum('precio_total'))['total'] or 0}
        if usuario.rol == 'admin':
            datos['usuarios'] = Usuario.objects.count()
        return Response(datos)

    @extend_schema(responses=UsuarioSerializer(many=True))
    @action(detail=False, methods=['get'])
    def usuarios(self, request):
        if request.user.rol != 'admin':
            raise PermissionDenied('Solo administradores pueden consultar usuarios.')
        pagina = self.paginate_queryset(Usuario.objects.order_by('-id'))
        return self.get_paginated_response(UsuarioSerializer(pagina, many=True).data)
