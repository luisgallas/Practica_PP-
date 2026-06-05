from django.test import TestCase

from presupuesto.models import Propiedad, Usuario


class UsuarioModelTest(TestCase):
    def setUp(self):
        self.usuario = Usuario.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            rol='huesped'
        )

    def test_usuario_creation(self):
        self.assertEqual(self.usuario.username, 'testuser')
        self.assertEqual(self.usuario.rol, 'huesped')

    def test_usuario_str(self):
        self.assertIn('testuser', str(self.usuario))


class PropiedadModelTest(TestCase):
    def setUp(self):
        self.usuario = Usuario.objects.create_user(
            username='anfitrion',
            password='testpass123',
            rol='anfitrion'
        )
        self.propiedad = Propiedad.objects.create(
            id_anfitrion=self.usuario,
            titulo='Casa de prueba',
            descripcion='Descripcion de prueba',
            ubicacion='Buenos Aires',
            precio_noche=100,
            precio_fin_semana=150,
            tarifa_limpieza=30,
        )

    def test_propiedad_creation(self):
        self.assertEqual(self.propiedad.titulo, 'Casa de prueba')
        self.assertEqual(self.propiedad.estado, 'disponible')

    def test_propiedad_str(self):
        self.assertIn('Casa de prueba', str(self.propiedad))


class PropiedadAPITest(TestCase):
    def setUp(self):
        self.usuario = Usuario.objects.create_user(
            username='api-anfitrion',
            password='testpass123',
            rol='anfitrion'
        )
        self.propiedad = Propiedad.objects.create(
            id_anfitrion=self.usuario,
            titulo='Departamento API',
            descripcion='Disponible para pruebas de API',
            ubicacion='Asuncion',
            precio_noche=120,
            precio_fin_semana=180,
            tarifa_limpieza=35,
        )

    def test_propiedad_list_endpoint(self):
        response = self.client.get('/api/propiedades/')

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['titulo'], 'Departamento API')

    def test_propiedad_detail_endpoint(self):
        response = self.client.get(f'/api/propiedades/{self.propiedad.id}/')

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['id'], self.propiedad.id)
        self.assertEqual(data['anfitrion'], 'api-anfitrion')
