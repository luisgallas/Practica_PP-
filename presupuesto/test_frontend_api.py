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

    def test_contacto_y_maps_se_guardan_y_aparecen_en_reserva(self):
        self.ingresar()
        datos = {'google_maps_url': 'https://maps.app.goo.gl/ejemplo', 'telefono_contacto': '+595 981 123456'}
        respuesta = self.cliente.patch(self.ruta, datos, format='json')
        self.assertEqual(respuesta.status_code, 200, respuesta.data)
        self.propiedad.refresh_from_db()
        self.assertEqual(self.propiedad.telefono_contacto, datos['telefono_contacto'])
        self.ingresar(self.huesped)
        detalle = self.cliente.get(self.ruta).data
        self.assertEqual(detalle['google_maps_url'], datos['google_maps_url'])
        self.assertNotIn('telefono', detalle['anfitrion'])
        reserva = self.reservar()
        self.assertEqual(reserva.status_code, 201, reserva.data)
        self.assertEqual(reserva.data['propiedad']['telefono_contacto'], datos['telefono_contacto'])
        self.ingresar(self.otro)
        self.assertEqual(self.cliente.patch(self.ruta, datos, format='json').status_code, 403)

    def test_valida_enlaces_maps_y_telefono_y_permite_borrarlos(self):
        self.ingresar()
        for enlace in ['https://example.com/maps', 'https://www.google.com.evil.test/maps', 'javascript:alert(1)', 'http://maps.google.com/', 'https://google.com/search?q=casa']:
            self.assertEqual(self.cliente.patch(self.ruta, {'google_maps_url': enlace}, format='json').status_code, 400)
        for telefono in ['abc123456', '+595<script>', '-------', '1234567890123456']:
            self.assertEqual(self.cliente.patch(self.ruta, {'telefono_contacto': telefono}, format='json').status_code, 400)
        for enlace in ['https://www.google.com/maps/place/Casa', 'https://goo.gl/maps/ejemplo', 'https://maps.app.goo.gl/ejemplo']:
            self.assertEqual(self.cliente.patch(self.ruta, {'google_maps_url': enlace}, format='json').status_code, 200)
        self.assertEqual(self.cliente.patch(self.ruta, {'google_maps_url': '', 'telefono_contacto': ''}, format='json').status_code, 200)

    def chat_guiado(self, mensaje, anterior=None, **extra):
        datos = {'message': mensaje}
        if anterior:
            datos['contexto_firmado'] = anterior.data['contexto_firmado']
            if anterior.data.get('accion_firmada'):
                datos['accion_firmada'] = anterior.data['accion_firmada']
        datos.update(extra)
        return self.cliente.post('/api/v1/asistente/', datos, format='json')

    def preparar_chat(self):
        self.ingresar(self.huesped)
        resultado = self.chat_guiado('Busco alojamiento en Villarrica')
        resultado = self.chat_guiado(f'{self.desde} al {self.hasta}', resultado)
        resultado = self.chat_guiado('2', resultado)
        self.assertEqual(resultado.data['opciones'][0]['id'], self.propiedad.pk)
        return self.chat_guiado('la primera', resultado)

    def test_chat_guiado_reserva_solo_tras_confirmar_y_no_duplica(self):
        resultado = self.preparar_chat()
        self.assertEqual(resultado.status_code, 200, resultado.data)
        self.assertIn('accion_firmada', resultado.data)
        self.assertIn('Cancelación:', resultado.data['reply'])
        self.assertFalse(Reserva.objects.exists())
        confirmada = self.chat_guiado('confirmo', resultado)
        self.assertEqual(confirmada.data['intent'], 'create_reservation_confirmed')
        reserva = Reserva.objects.get()
        self.assertEqual(reserva.id_huesped, self.huesped)
        self.assertEqual(reserva.cantidad_huespedes, 2)
        self.assertEqual(reserva.estado, 'pendiente')
        self.chat_guiado('confirmo', resultado)
        self.assertEqual(Reserva.objects.count(), 1)

    def test_chat_fechas_separadas_y_correcciones(self):
        self.ingresar(self.huesped)
        r = self.chat_guiado('Busco alojamiento en Villarrica')
        r = self.chat_guiado(str(self.desde), r)
        self.assertIn('salida', r.data['reply'])
        r = self.chat_guiado(str(self.hasta), r)
        self.assertIn('cuántos', r.data['reply'])
        r = self.chat_guiado('somos 2', r)
        r = self.chat_guiado('1', r)
        r = self.chat_guiado('somos 3 personas', r)
        self.assertIn('Huéspedes: 3', r.data['reply'])
        r = self.chat_guiado('descartar', r)
        self.assertNotIn('accion_firmada', r.data)
        self.assertFalse(Reserva.objects.exists())

    def test_chat_contexto_y_accion_no_se_pueden_suplantar(self):
        r = self.preparar_chat()
        self.ingresar(self.otro)
        self.assertEqual(self.chat_guiado('confirmo', r).status_code, 400)
        self.assertEqual(self.chat_guiado('revisar', r).status_code, 400)
        self.ingresar(self.huesped)
        self.assertEqual(self.chat_guiado('revisar', contexto_firmado=r.data['contexto_firmado'] + 'x').status_code, 400)
        self.assertFalse(Reserva.objects.exists())

    def test_chat_revalida_precio_y_disponibilidad(self):
        r = self.preparar_chat()
        self.propiedad.tarifa_limpieza += 100
        self.propiedad.save()
        self.assertEqual(self.chat_guiado('confirmo', r).status_code, 400)
        self.assertFalse(Reserva.objects.exists())
        actualizado = self.chat_guiado('revisar', r)
        create_reservation(self.propiedad.pk, self.huesped.pk, self.desde, self.hasta, 1)
        self.assertEqual(self.chat_guiado('confirmo', actualizado).data['intent'], 'create_reservation_error')
        self.assertEqual(Reserva.objects.count(), 1)

    def test_chat_consultas_por_ciudad_aisladas_por_rol(self):
        create_reservation(self.propiedad.pk, self.huesped.pk, self.desde, self.hasta, 1)
        for usuario, cantidad in [(self.anfitrion, 1), (self.otro, 0), (self.huesped, 1), (self.administrador, 1)]:
            self.ingresar(usuario)
            r = self.chat_guiado('en Villarrica cuantas reservas tengo')
            self.assertEqual(r.data['data']['count'], cantidad)
        r = self.chat_guiado('en Ciudad Inexistente cuantas reservas tengo')
        self.assertEqual(r.data['data']['count'], 0)
        self.ingresar(self.anfitrion)
        self.assertEqual(self.chat_guiado('Quiero reservar').status_code, 403)

    def test_chat_pide_anio_y_rechaza_fechas_invalidas(self):
        self.ingresar(self.huesped)
        r = self.chat_guiado('Busco alojamiento en Villarrica del 20 al 22 de diciembre')
        self.assertIn('año', r.data['reply'])
        r = self.chat_guiado(str(timezone.localdate().year + 1), r)
        self.assertIn('cuántos', r.data['reply'])
        r = self.chat_guiado('31/02/2099 al 03/03/2099', r)
        self.assertIn('no es válida', r.data['reply'])

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
        self.assertEqual(respuesta.data['data']['count'], 0)
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

    def test_registro_rechaza_admin_sin_codigo_y_valida_contrasena(self):
        datos = {'username': 'nueva', 'email': 'nueva@example.com', 'password': 'UnaClaveLarga2026!', 'rol': 'admin'}
        self.assertEqual(self.cliente.post('/api/v1/auth/registro/', datos, format='json').status_code, 400)
        datos.update(rol='anfitrion', password='123')
        self.assertEqual(self.cliente.post('/api/v1/auth/registro/', datos, format='json').status_code, 400)
        datos['password'] = 'UnaClaveLarga2026!'
        respuesta = self.cliente.post('/api/v1/auth/registro/', datos, format='json')
        self.assertEqual(respuesta.status_code, 201, respuesta.data)
        self.assertFalse(Usuario.objects.get(username='nueva').is_superuser)

    @override_settings(ADMIN_REGISTRATION_CODE='codigo-privado-de-prueba')
    def test_registro_admin_exige_codigo_y_permite_ingreso(self):
        datos = {'username': 'nuevoadmin', 'email': 'admin@example.com', 'password': 'UnaClaveLarga2026!', 'rol': 'admin'}
        for codigo in ['', 'incorrecto']:
            datos['codigo_admin'] = codigo
            self.assertEqual(self.cliente.post('/api/v1/auth/registro/', datos, format='json').status_code, 400)
        self.assertFalse(Usuario.objects.filter(username='nuevoadmin').exists())
        datos['codigo_admin'] = 'codigo-privado-de-prueba'
        respuesta = self.cliente.post('/api/v1/auth/registro/', datos, format='json')
        self.assertEqual(respuesta.status_code, 201, respuesta.data)
        self.assertEqual(respuesta.data['rol'], 'admin')
        self.assertNotIn('codigo_admin', respuesta.data)
        self.assertFalse(Usuario.objects.get(username='nuevoadmin').is_superuser)
        respuesta = self.cliente.post('/api/v1/auth/ingresar/', {'username': datos['username'], 'password': datos['password']}, format='json')
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.data['usuario']['rol'], 'admin')

    @override_settings(ADMIN_REGISTRATION_CODE='')
    def test_registro_admin_deshabilitado_sin_configuracion(self):
        datos = {'username': 'bloqueado', 'email': 'admin@example.com', 'password': 'UnaClaveLarga2026!', 'rol': 'admin', 'codigo_admin': 'cualquier-codigo'}
        self.assertEqual(self.cliente.post('/api/v1/auth/registro/', datos, format='json').status_code, 400)
        self.assertFalse(Usuario.objects.filter(username='bloqueado').exists())

    def test_admin_supervisa_sin_participar_como_huesped(self):
        self.ingresar(self.administrador)
        for ruta in ['/api/v1/cuenta/panel/', '/api/v1/cuenta/usuarios/', '/api/v1/alojamientos/?mios=1', '/api/v1/reservas/']:
            self.assertEqual(self.cliente.get(ruta).status_code, 200)
        self.assertEqual(self.reservar().status_code, 403)
        self.assertEqual(self.cliente.post(self.ruta + 'resenas/', {}, format='json').status_code, 403)
        self.assertEqual(self.cliente.post(self.ruta + 'favorito/').status_code, 403)
        self.assertFalse(Review.objects.exists())
        self.assertFalse(Favorito.objects.exists())

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
