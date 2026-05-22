from django.test import TestCase  # Importa nombres concretos desde un módulo.
from presupuesto.models import Usuario, Propiedad, Amenity, Reserva, Notificacion, Review  # Importa nombres concretos desde un módulo.


class UsuarioModelTest(TestCase):  # Define una clase Python.
    def setUp(self):  # Define una función / método.
        self.usuario = Usuario.objects.create_user(  # Consulta o crea objetos en la base de datos.
            username='testuser',
            email='test@example.com',
            password='testpass123',
            rol='huesped'
        )
    
    def test_usuario_creation(self):  # Define una función / método.
        self.assertEqual(self.usuario.username, 'testuser')  # Realiza una comparación en un caso de prueba.
        self.assertEqual(self.usuario.rol, 'huesped')  # Realiza una comparación en un caso de prueba.
    
    def test_usuario_str(self):  # Define una función / método.
        self.assertIn('testuser', str(self.usuario))  # Realiza una comparación en un caso de prueba.


class PropiedadModelTest(TestCase):  # Define una clase Python.
    def setUp(self):  # Define una función / método.
        self.usuario = Usuario.objects.create_user(  # Consulta o crea objetos en la base de datos.
            username='anfitrion',
            password='testpass123',
            rol='anfitrion'
        )
        self.propiedad = Propiedad.objects.create(  # Consulta o crea objetos en la base de datos.
            id_anfitrion=self.usuario,
            titulo='Casa de prueba',
            descripcion='Descripción de prueba',
            ubicacion='Buenos Aires',
            precio_noche=100,
            precio_fin_semana=150,
            tarifa_limpieza=30,
        )
    
    def test_propiedad_creation(self):  # Define una función / método.
        self.assertEqual(self.propiedad.titulo, 'Casa de prueba')  # Realiza una comparación en un caso de prueba.
        self.assertEqual(self.propiedad.estado, 'disponible')  # Realiza una comparación en un caso de prueba.
    
    def test_propiedad_str(self):  # Define una función / método.
        self.assertIn('Casa de prueba', str(self.propiedad))  # Realiza una comparación en un caso de prueba.
