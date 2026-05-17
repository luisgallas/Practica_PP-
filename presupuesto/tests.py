from django.test import TestCase
from presupuesto.models import Usuario, Propiedad, Amenity, Reserva, Notificacion, Review


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
            descripcion='Descripción de prueba',
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
