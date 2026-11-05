"""Pruebas de integración del contrato, aislamiento de usuarios y archivos."""
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from io import BytesIO
from tempfile import TemporaryDirectory
from threading import Barrier
from unittest import skipUnless

from django.conf import settings
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import connection, close_old_connections
from django.test import TestCase, TransactionTestCase, override_settings
from django.test.utils import CaptureQueriesContext
from django.utils import timezone
from PIL import Image
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken

from .models import Favorito, Propiedad, PropiedadFoto, Reserva, Review, Usuario
from .services import create_reservation


def imagen(nombre='foto.png', tamano=(32, 24)):
    salida = BytesIO()
    Image.new('RGB', tamano, '#0b5cad').save(salida, 'PNG')
    return SimpleUploadedFile(nombre, salida.getvalue(), content_type='image/png')


@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class ApiFrontendTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.anfitrion = Usuario.objects.create_user(username='anfitrion', password='UnaClaveLarga2026!', rol='anfitrion', email='privado@example.com', telefono='0981111111')
        cls.otro = Usuario.objects.create_user(username='otro', password='UnaClaveLarga2026!', rol='anfitrion')
        cls.huesped = Usuario.objects.create_user(username='huesped', password='UnaClaveLarga2026!', rol='huesped')
        cls.administrador = Usuario.objects.create_user(username='administrador', password='UnaClaveLarga2026!', rol='admin')
        cls.propiedad = Propiedad.objects.create(titulo='Casa de prueba', descripcion='Casa con patio y espacio para descansar.', ubicacion='Villarrica', precio_noche=200000, precio_fin_semana=250000, tarifa_limpieza=50000, capacidad_maxima_huespedes=4, id_anfitrion=cls.anfitrion)

    def setUp(self):
        cache.clear()
        self.cliente = APIClient()
        self.carpeta = TemporaryDirectory()
        self.addCleanup(self.carpeta.cleanup)
        configuracion = override_settings(MEDIA_ROOT=self.carpeta.name)
        configuracion.enable()
        self.addCleanup(configuracion.disable)
        self.desde = timezone.localdate() + timedelta(days=15)
        self.hasta = self.desde + timedelta(days=2)
        self.ruta = f'/api/v1/alojamientos/{self.propiedad.pk}/'

    def ingresar(self, usuario=None):
        self.cliente.force_authenticate(usuario or self.anfitrion)

    def reservar(self, **cambios):
        datos = {'alojamiento': self.propiedad.pk, 'desde': self.desde.isoformat(), 'hasta': self.hasta.isoformat(), 'huespedes': 2}
        datos.update(cambios)
        return self.cliente.post('/api/v1/reservas/', datos, format='json')

    def test_catalogo_paginado_oculta_datos_privados_y_pausados(self):
        Propiedad.objects.create(titulo='Pausada', descripcion='Privada', ubicacion='Asunción', precio_noche=1, precio_fin_semana=1, tarifa_limpieza=0, estado='pausada', id_anfitrion=self.otro)
        respuesta = self.cliente.get('/api/v1/alojamientos/')
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.data['count'], 1)
        self.assertNotIn('email', respuesta.data['results'][0]['anfitrion'])
        self.assertNotIn('telefono', respuesta.data['results'][0]['anfitrion'])
        self.assertEqual(self.cliente.get('/api/v1/alojamientos/?mios=1').status_code, 403)

    def test_filtros_validados_y_pagina_acotada(self):
        self.assertEqual(self.cliente.get('/api/v1/alojamientos/?precio_max=abc').status_code, 400)
        self.assertEqual(self.cliente.get('/api/v1/alojamientos/?ciudad=noexiste').data['count'], 0)
        self.assertEqual(self.cliente.get('/api/v1/alojamientos/?huespedes=8').data['count'], 0)
        self.assertEqual(self.cliente.get('/api/v1/alojamientos/?desde=2000-01-01&hasta=2000-01-02').status_code, 400)

    def test_listado_no_aumenta_consultas_por_alojamiento(self):
        with CaptureQueriesContext(connection) as consultas:
            self.cliente.get('/api/v1/alojamientos/')
        base = len(consultas)
        for indice in range(8):
            Propiedad.objects.create(titulo=f'Casa {indice}', descripcion='Espacio', ubicacion='Villarrica', precio_noche=10, precio_fin_semana=10, tarifa_limpieza=0, id_anfitrion=self.anfitrion)
        with CaptureQueriesContext(connection) as consultas:
            self.cliente.get('/api/v1/alojamientos/')
        self.assertLessEqual(len(consultas), base)

    def test_anfitrion_solo_edita_sus_alojamientos(self):
        self.ingresar(self.otro)
        respuesta = self.cliente.patch(self.ruta, {'titulo': 'Modificada'}, format='json')
        self.assertEqual(respuesta.status_code, 403)
        self.assertEqual(self.cliente.get('/api/v1/alojamientos/?mios=1').data['count'], 0)
        self.ingresar()
        self.assertEqual(self.cliente.patch(self.ruta, {'titulo': 'Casa actualizada'}, format='json').status_code, 200)
        self.propiedad.refresh_from_db()
        self.assertEqual(self.propiedad.titulo, 'Casa actualizada')

    def test_huesped_no_publica_y_no_se_puede_cambiar_propietario(self):
        self.ingresar(self.huesped)
        self.assertEqual(self.cliente.patch(self.ruta, {'estado': 'pausada'}, format='json').status_code, 403)
        self.ingresar()
        self.cliente.patch(self.ruta, {'id_anfitrion': self.otro.pk, 'anfitrion': self.otro.pk}, format='json')
        self.propiedad.refresh_from_db()
        self.assertEqual(self.propiedad.id_anfitrion_id, self.anfitrion.pk)

    def test_cinco_fotos_recodificadas_y_sexta_rechazada(self):
        self.ingresar()
        respuesta = self.cliente.post(self.ruta + 'fotos/', {'fotos': [imagen(f'{i}.png') for i in range(5)]}, format='multipart')
        self.assertEqual(respuesta.status_code, 201, respuesta.data)
        self.assertEqual(self.propiedad.fotos.count(), 5)
        self.assertEqual(self.propiedad.fotos.filter(es_portada=True).count(), 1)
        foto = self.propiedad.fotos.first()
        self.assertTrue(foto.foto.name.endswith('.webp'))
        with foto.foto.open('rb') as archivo:
            with Image.open(archivo) as contenido:
                self.assertEqual(contenido.format, 'WEBP')
                self.assertFalse(contenido.getexif())
        self.assertEqual(self.cliente.post(self.ruta + 'fotos/', {'fotos': [imagen()]}, format='multipart').status_code, 400)
        self.assertEqual(self.propiedad.fotos.count(), 5)

    def test_lote_invalido_no_publica_archivos_parciales(self):
        self.ingresar()
        falso = SimpleUploadedFile('casa.jpg', b'<script>alert(1)</script>', content_type='image/jpeg')
        respuesta = self.cliente.post(self.ruta + 'fotos/', {'fotos': [imagen(), falso]}, format='multipart')
        self.assertEqual(respuesta.status_code, 400)
        self.assertFalse(self.propiedad.fotos.exists())

    def test_rechaza_tamano_svg_y_dimensiones(self):
        self.ingresar()
        archivos = [SimpleUploadedFile('grande.jpg', b'x' * (5 * 1024 * 1024 + 1), content_type='image/jpeg'),
                    SimpleUploadedFile('vector.svg', b'<svg xmlns="http://www.w3.org/2000/svg"/>', content_type='image/svg+xml'),
                    imagen(tamano=(5000, 4001))]
        for archivo in archivos:
            with self.subTest(archivo=archivo.name):
                self.assertEqual(self.cliente.post(self.ruta + 'fotos/', {'fotos': [archivo]}, format='multipart').status_code, 400)
        self.assertFalse(self.propiedad.fotos.exists())

    def test_fotos_no_permiten_acceso_ajeno_y_portada_es_unica(self):
        self.ingresar(self.otro)
        self.assertEqual(self.cliente.post(self.ruta + 'fotos/', {'fotos': [imagen()]}, format='multipart').status_code, 403)
        self.ingresar()
        self.cliente.post(self.ruta + 'fotos/', {'fotos': [imagen(), imagen()]}, format='multipart')
        segunda = self.propiedad.fotos.order_by('id').last()
        self.assertEqual(self.cliente.patch(self.ruta + f'fotos/{segunda.pk}/portada/', {}, format='json').status_code, 200)
        self.assertEqual(self.propiedad.fotos.filter(es_portada=True).get().pk, segunda.pk)
        with self.captureOnCommitCallbacks(execute=True):
            self.assertEqual(self.cliente.delete(self.ruta + f'fotos/{segunda.pk}/').status_code, 204)
        self.assertEqual(self.propiedad.fotos.filter(es_portada=True).count(), 1)

    def test_reserva_aislada_con_total_del_servidor_y_solapamiento(self):
        self.ingresar(self.huesped)
        respuesta = self.reservar(precio_total=1, estado='confirmada', id_huesped=self.otro.pk)
        self.assertEqual(respuesta.status_code, 201, respuesta.data)
        reserva = Reserva.objects.get(pk=respuesta.data['id'])
        self.assertEqual(reserva.id_huesped_id, self.huesped.pk)
        self.assertEqual(reserva.estado, 'pendiente')
        self.assertGreater(reserva.precio_total, 1)
        self.assertEqual(self.reservar().status_code, 400)
        self.assertEqual(reserva.disponibilidades.count(), 2)
        self.ingresar(self.otro)
        self.assertEqual(self.cliente.get('/api/v1/reservas/').data['count'], 0)
        self.assertEqual(self.cliente.post(f'/api/v1/reservas/{reserva.pk}/estado/', {'estado': 'confirmada'}, format='json').status_code, 404)

    def test_reserva_invalida_o_fuera_de_capacidad(self):
        self.ingresar(self.huesped)
        for cambios in [{'huespedes': 5}, {'huespedes': 0}, {'desde': '2000-01-01'}, {'hasta': self.desde.isoformat()}, {'hasta': (self.desde + timedelta(days=366)).isoformat()}]:
            with self.subTest(cambios=cambios):
                self.assertEqual(self.reservar(**cambios).status_code, 400)
        self.assertFalse(Reserva.objects.exists())

    def test_confirmacion_cancelacion_y_transiciones(self):
        self.ingresar(self.huesped)
        identificador = self.reservar().data['id']
        self.assertEqual(self.cliente.post(f'/api/v1/reservas/{identificador}/estado/', {'estado': 'confirmada'}, format='json').status_code, 403)
        self.ingresar()
        self.assertEqual(self.cliente.post(f'/api/v1/reservas/{identificador}/estado/', {'estado': 'completada'}, format='json').status_code, 400)
        self.assertEqual(self.cliente.post(f'/api/v1/reservas/{identificador}/estado/', {'estado': 'confirmada'}, format='json').status_code, 200)
        self.ingresar(self.huesped)
        self.assertEqual(self.cliente.post(f'/api/v1/reservas/{identificador}/cancelar/', {'motivo': 'Cambio de planes'}, format='json').status_code, 200)
        self.assertEqual(self.reservar().status_code, 201)

    def test_resenas_solo_para_estadias_propias_completadas_y_sin_duplicados(self):
        reserva = Reserva.objects.create(id_propiedad=self.propiedad, id_huesped=self.huesped, fecha_inicio=timezone.localdate()-timedelta(days=4), fecha_fin=timezone.localdate()-timedelta(days=2), cantidad_huespedes=1, precio_total=1, estado='confirmada')
        self.ingresar(self.huesped)
        datos = {'id_reserva': reserva.pk, 'calificacion': 5, 'comentario': 'Una estadía muy agradable.'}
        self.assertEqual(self.cliente.post(self.ruta + 'resenas/', datos, format='json').status_code, 404)
        reserva.estado = 'completada'; reserva.save()
        self.assertEqual(self.cliente.post(self.ruta + 'resenas/', datos, format='json').status_code, 201)
        self.assertEqual(self.cliente.post(self.ruta + 'resenas/', datos, format='json').status_code, 400)
        self.assertEqual(Review.objects.count(), 1)

    def test_favoritos_persistentes_sin_duplicados(self):
        self.ingresar(self.huesped)
        for _ in range(2):
            self.assertEqual(self.cliente.post(self.ruta + 'favorito/').status_code, 204)
        self.assertEqual(Favorito.objects.count(), 1)
        self.assertTrue(self.cliente.get(self.ruta + 'favorito/').data['guardado'])
        self.assertEqual(self.cliente.get('/api/v1/cuenta/favoritos/').data['count'], 1)
        self.assertEqual(self.cliente.delete(self.ruta + 'favorito/').status_code, 204)
        self.assertFalse(Favorito.objects.exists())

    def test_administracion_restringida_por_rol(self):
        self.ingresar(self.huesped)
        self.assertEqual(self.cliente.get('/api/v1/cuenta/panel/').status_code, 403)
        self.assertEqual(self.cliente.get('/api/v1/cuenta/usuarios/').status_code, 403)
        self.ingresar(self.administrador)
        self.assertEqual(self.cliente.get('/api/v1/cuenta/usuarios/').data['count'], 4)
        self.assertEqual(self.cliente.get('/api/v1/cuenta/panel/').data['alojamientos'], 1)

    def test_chat_exige_identidad_y_confirmacion_firmada(self):
        self.assertEqual(self.cliente.post('/api/v1/asistente/', {'message': 'Cuantas reservas hay', 'user_id': self.administrador.pk}, format='json').status_code, 401)
        self.ingresar(self.huesped)
        respuesta = self.cliente.post('/api/v1/asistente/', {'message': 'Cuantas reservas hay', 'user_id': self.administrador.pk}, format='json')
        self.assertEqual(respuesta.data['intent'], 'host_wrong_role')
        respuesta = self.cliente.post('/api/v1/asistente/', {'message': 'confirmo', 'confirm': True, 'pending_action': {'type': 'create_reservation', 'data': {'guest_id': self.huesped.pk}}}, format='json')
        self.assertEqual(respuesta.status_code, 400)
        self.assertFalse(Reserva.objects.exists())

    def test_login_csrf_rotacion_revocacion_y_cookie_httponly(self):
        cliente = APIClient(enforce_csrf_checks=True)
        credenciales = {'username': self.huesped.username, 'password': 'UnaClaveLarga2026!'}
        self.assertEqual(cliente.post('/api/v1/auth/ingresar/', credenciales, format='json').status_code, 403)
        csrf = cliente.get('/api/v1/auth/csrf/').data['csrfToken']
        respuesta = cliente.post('/api/v1/auth/ingresar/', credenciales, format='json', HTTP_X_CSRFTOKEN=csrf)
        self.assertEqual(respuesta.status_code, 200, respuesta.data)
        self.assertTrue(respuesta.cookies['hospeda_renovacion']['httponly'])
        self.assertEqual(AccessToken(respuesta.data['access'])['user_id'], str(self.huesped.pk))
        anterior = respuesta.cookies['hospeda_renovacion'].value
        csrf = respuesta.data['csrfToken']
        self.assertEqual(cliente.post('/api/v1/auth/renovar/', {}, format='json').status_code, 403)
        respuesta = cliente.post('/api/v1/auth/renovar/', {}, format='json', HTTP_X_CSRFTOKEN=csrf)
        self.assertEqual(respuesta.status_code, 200, respuesta.data)
        actual = respuesta.cookies['hospeda_renovacion'].value
        self.assertNotEqual(actual, anterior)
        cliente.cookies['hospeda_renovacion'] = anterior
        self.assertIn(cliente.post('/api/v1/auth/renovar/', {}, format='json', HTTP_X_CSRFTOKEN=csrf).status_code, [401, 403])
        cliente.cookies['hospeda_renovacion'] = actual
        self.assertEqual(cliente.post('/api/v1/auth/salir/', {}, format='json', HTTP_X_CSRFTOKEN=csrf).status_code, 204)
        cliente.cookies['hospeda_renovacion'] = actual
        self.assertIn(cliente.post('/api/v1/auth/renovar/', {}, format='json', HTTP_X_CSRFTOKEN=csrf).status_code, [401, 403])

    def test_registro_no_admite_admin_y_valida_contrasena(self):
        datos = {'username': 'nueva', 'email': 'nueva@example.com', 'password': 'UnaClaveLarga2026!', 'rol': 'admin'}
        self.assertEqual(self.cliente.post('/api/v1/auth/registro/', datos, format='json').status_code, 400)
        datos.update(rol='anfitrion', password='123')
        self.assertEqual(self.cliente.post('/api/v1/auth/registro/', datos, format='json').status_code, 400)
        datos['password'] = 'UnaClaveLarga2026!'
        respuesta = self.cliente.post('/api/v1/auth/registro/', datos, format='json')
        self.assertEqual(respuesta.status_code, 201, respuesta.data)
        self.assertFalse(Usuario.objects.get(username='nueva').is_superuser)

    def test_login_limita_intentos_incorrectos(self):
        for _ in range(10):
            self.cliente.post('/api/v1/auth/ingresar/', {'username': 'nadie', 'password': 'incorrecta'}, format='json')
        respuesta = self.cliente.post('/api/v1/auth/ingresar/', {'username': 'nadie', 'password': 'incorrecta'}, format='json')
        self.assertEqual(respuesta.status_code, 429)

    def test_chat_admin_no_permite_suplantar_otro_rol(self):
        self.cliente.force_login(self.huesped)
        respuesta = self.cliente.post('/admin/presupuesto/preguntaria/', {'usuario': self.administrador.pk, 'message': 'Cuantas reservas hay en total?'})
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.context['result']['intent'], 'host_wrong_role')


@skipUnless(connection.vendor == 'postgresql', 'La concurrencia real se verifica con PostgreSQL (CI).')
@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class ConcurrenciaReservasTests(TransactionTestCase):
    def test_solo_una_reserva_simultanea_ocupa_las_fechas(self):
        anfitrion = Usuario.objects.create_user(username='host', rol='anfitrion')
        huesped = Usuario.objects.create_user(username='guest', rol='huesped')
        propiedad = Propiedad.objects.create(titulo='Casa', descripcion='Casa', ubicacion='Villarrica', precio_noche=1, precio_fin_semana=1, tarifa_limpieza=0, id_anfitrion=anfitrion)
        barrera = Barrier(2)
        desde = timezone.localdate() + timedelta(days=5)
        def intento():
            close_old_connections()
            barrera.wait(timeout=10)
            try:
                create_reservation(propiedad.pk, huesped.pk, desde, desde + timedelta(days=1), 1)
                return 'creada'
            except ValueError:
                return 'ocupada'
            finally:
                close_old_connections()
        with ThreadPoolExecutor(max_workers=2) as ejecutor:
            resultados = list(ejecutor.map(lambda _: intento(), range(2)))
        self.assertCountEqual(resultados, ['creada', 'ocupada'])
        self.assertEqual(Reserva.objects.count(), 1)
