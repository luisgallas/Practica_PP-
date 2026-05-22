import os  # Importa un módulo de Python.
import django  # Importa un módulo de Python.

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')  # Configura una variable de entorno si aún no existe.
django.setup()  # Inicializa Django para usar sus modelos y utilidades.

from django.contrib.auth import get_user_model  # Importa nombres concretos desde un módulo.
from presupuesto.models import Amenity, Propiedad, Disponibilidad, Reserva, Notificacion, Review  # Importa nombres concretos desde un módulo.

User = get_user_model()

# Crear superusuario
if not User.objects.filter(username='admin').exists():  # Consulta o crea objetos en la base de datos.
    admin_user = User.objects.create_superuser('admin', 'admin@test.com', 'admin123')  # Consulta o crea objetos en la base de datos.
    admin_user.rol = 'admin'
    admin_user.save()
    print("✅ Superusuario 'admin' creado")  # Imprime un mensaje en la consola.
else:
    admin_user = User.objects.get(username='admin')  # Consulta o crea objetos en la base de datos.
    print("✅ Superusuario 'admin' ya existe")  # Imprime un mensaje en la consola.

# Crear usuarios de prueba
anfitrion = User.objects.filter(username='anfitrion1').first()  # Consulta o crea objetos en la base de datos.
if not anfitrion:
    anfitrion = User.objects.create_user(  # Consulta o crea objetos en la base de datos.
        username='anfitrion1',
        email='anfitrion@test.com',
        password='test123',
        first_name='Juan',
        last_name='Pérez'
    )
    anfitrion.rol = 'anfitrion'
    anfitrion.save()
    print("✅ Usuario 'anfitrion1' creado")  # Imprime un mensaje en la consola.

huespedes = []
for i in range(1, 4):  # Inicia una estructura de bloque en Python.
    huesped = User.objects.filter(username=f'huesped{i}').first()  # Consulta o crea objetos en la base de datos.
    if not huesped:
        huesped = User.objects.create_user(  # Consulta o crea objetos en la base de datos.
            username=f'huesped{i}',
            email=f'huesped{i}@test.com',
            password='test123',
            first_name=f'Huésped{i}',
            last_name='Gallas'
        )
        huesped.rol = 'huesped'
        huesped.save()
        print(f"✅ Usuario 'huesped{i}' creado")  # Imprime un mensaje en la consola.
    huespedes.append(huesped)

# Crear amenities
amenities_data = [
    'WiFi', 'Aire Acondicionado', 'Piscina', 'Cocina Completa', 
    'TV Smart', 'Lavadora', 'Estacionamiento', 'Jardín'
]

amenities = []
for amenity_name in amenities_data:
    amenity, _ = Amenity.objects.get_or_create(nombre=amenity_name)  # Consulta o crea objetos en la base de datos.
    amenities.append(amenity)
    
print(f"✅ {len(amenities)} Amenities creadas")  # Imprime un mensaje en la consola.

# Crear propiedades
if Propiedad.objects.count() == 0:  # Consulta o crea objetos en la base de datos.
    prop1 = Propiedad.objects.create(  # Consulta o crea objetos en la base de datos.
        id_anfitrion=anfitrion,
        titulo='Casa cerca del centro',
        descripcion='Hermosa casa con vistas al centro de la ciudad',
        ubicacion='Calle Principal 123',
        precio_noche=150.00,
        precio_fin_semana=200.00,
        tarifa_limpieza=50.00,
        estado='disponible'
    )
    prop1.amenities.set(amenities[:4])
    print("✅ Propiedad 1 creada")  # Imprime un mensaje en la consola.

    prop2 = Propiedad.objects.create(  # Consulta o crea objetos en la base de datos.
        id_anfitrion=anfitrion,
        titulo='Departamento moderno',
        descripcion='Depto moderno en zona residencial',
        ubicacion='Avenida Independencia 456',
        precio_noche=100.00,
        precio_fin_semana=150.00,
        tarifa_limpieza=30.00,
        estado='disponible'
    )
    prop2.amenities.set(amenities[4:])
    print("✅ Propiedad 2 creada")  # Imprime un mensaje en la consola.

    prop3 = Propiedad.objects.create(  # Consulta o crea objetos en la base de datos.
        id_anfitrion=anfitrion,
        titulo='Cabaña en la montaña',
        descripcion='Cabaña tranquila rodeada de naturaleza',
        ubicacion='Camino Rural 789',
        precio_noche=80.00,
        precio_fin_semana=120.00,
        tarifa_limpieza=40.00,
        estado='disponible'
    )
    prop3.amenities.set(amenities[2:6])
    print("✅ Propiedad 3 creada")  # Imprime un mensaje en la consola.

print("\n" + "="*50)  # Imprime un mensaje en la consola.
print("✨ DATOS DE PRUEBA CARGADOS EXITOSAMENTE")  # Imprime un mensaje en la consola.
print("="*50)  # Imprime un mensaje en la consola.
print(f"Usuarios: {User.objects.count()}")  # Imprime un mensaje en la consola.
print(f"Propiedades: {Propiedad.objects.count()}")  # Imprime un mensaje en la consola.
print(f"Amenities: {Amenity.objects.count()}")  # Imprime un mensaje en la consola.
print("\n📝 Credenciales para admin:")  # Imprime un mensaje en la consola.
print("   Username: admin")  # Imprime un mensaje en la consola.
print("   Password: admin123")  # Imprime un mensaje en la consola.
