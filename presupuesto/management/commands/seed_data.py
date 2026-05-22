from django.core.management.base import BaseCommand  # Importa nombres concretos desde un módulo.
from django.contrib.auth import get_user_model  # Importa nombres concretos desde un módulo.
from presupuesto.models import Propiedad, Amenity, Disponibilidad, Reserva, Notificacion, Review  # Importa nombres concretos desde un módulo.
from datetime import datetime, timedelta  # Importa nombres concretos desde un módulo.

User = get_user_model()


class Command(BaseCommand):  # Define una clase Python.
    help = 'Carga datos de prueba en la base de datos'  # Texto de ayuda para un comando custom de Django.

    def handle(self, *args, **options):  # Define una función / método.
        # Limpiar datos previos (opcional)
        self.stdout.write(self.style.WARNING('Creando datos de prueba...'))
        
        # Crear Usuarios
        users = []
        for i in range(5):  # Inicia una estructura de bloque en Python.
            username = f'usuario{i+1}'
            email = f'usuario{i+1}@example.com'
            user, created = User.objects.get_or_create(  # Consulta o crea objetos en la base de datos.
                username=username,
                defaults={  # Proporciona valores por defecto para la creación de un objeto.
                    'email': email,
                    'first_name': f'Usuario',
                    'last_name': f'{i+1}',
                    'rol': 'anfitrion' if i % 2 == 0 else 'huesped',
                    'telefono': f'555-000{i+1}',
                    'is_active': True,
                }
            )
            users.append(user)
            if created:
                user.set_password('password123')  # Establece la contraseña guardada y cifrada del usuario.
                user.save()
                self.stdout.write(self.style.SUCCESS(f'Usuario creado: {username}'))
        
        # Crear Amenities
        amenities_names = ['WiFi', 'Piscina', 'Estacionamiento', 'Aire acondicionado', 'TV']
        amenities = []
        for name in amenities_names:
            amenity, created = Amenity.objects.get_or_create(nombre=name)  # Consulta o crea objetos en la base de datos.
            amenities.append(amenity)
            if created:
                self.stdout.write(self.style.SUCCESS(f'Amenity creada: {name}'))
        
        # Crear Propiedades
        propiedades = []
        locations = ['Buenos Aires', 'Córdoba', 'Mendoza', 'Rosario', 'La Plata']
        for i in range(5):  # Inicia una estructura de bloque en Python.
            propiedad, created = Propiedad.objects.get_or_create(  # Consulta o crea objetos en la base de datos.
                titulo=f'Casa Hermosa {i+1}',
                defaults={  # Proporciona valores por defecto para la creación de un objeto.
                    'id_anfitrion': users[i % 3],
                    'descripcion': f'Descripción de la propiedad {i+1}. Una hermosa casa con vistas increíbles.',
                    'ubicacion': locations[i],
                    'precio_noche': 100 + (i * 50),
                    'precio_fin_semana': 150 + (i * 50),
                    'tarifa_limpieza': 30,
                    'estado': 'disponible',
                }
            )
            if created:
                # Agregar amenities
                propiedad.amenities.set(amenities[:3])
                self.stdout.write(self.style.SUCCESS(f'Propiedad creada: {propiedad.titulo}'))
            propiedades.append(propiedad)
        
        # Crear Disponibilidades
        for propiedad in propiedades:
            for days_ahead in range(30):  # Inicia una estructura de bloque en Python.
                fecha = datetime.now().date() + timedelta(days=days_ahead)
                disponibilidad, created = Disponibilidad.objects.get_or_create(  # Consulta o crea objetos en la base de datos.
                    id_propiedad=propiedad,
                    fecha=fecha,
                    defaults={'estado': 'disponible'}  # Proporciona valores por defecto para la creación de un objeto.
                )
                if created and days_ahead < 5:
                    self.stdout.write(f'  Disponibilidad creada para {propiedad.titulo} ({fecha})')
        
        # Crear Reservas
        reservas = []
        for i in range(5):  # Inicia una estructura de bloque en Python.
            fecha_inicio = datetime.now().date() + timedelta(days=5 + (i*5))
            fecha_fin = fecha_inicio + timedelta(days=3)
            
            reserva, created = Reserva.objects.get_or_create(  # Consulta o crea objetos en la base de datos.
                id_propiedad=propiedades[i],
                fecha_inicio=fecha_inicio,
                defaults={  # Proporciona valores por defecto para la creación de un objeto.
                    'id_huesped': users[(i+1) % len(users)],
                    'fecha_fin': fecha_fin,
                    'cantidad_huespedes': 2 + i,
                    'estado': 'confirmada',
                    'precio_total': 300 + (i * 100),
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Reserva creada: #{reserva.id}'))
            reservas.append(reserva)
        
        # Crear Notificaciones
        for i, reserva in enumerate(reservas):  # Inicia una estructura de bloque en Python.
            notificacion, created = Notificacion.objects.get_or_create(  # Consulta o crea objetos en la base de datos.
                id_usuario=reserva.id_huesped,
                id_reserva=reserva,
                defaults={  # Proporciona valores por defecto para la creación de un objeto.
                    'mensaje': f'Tu reserva en {reserva.id_propiedad.titulo} ha sido confirmada.',
                    'estado': 'no_leida',
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Notificación creada para {notificacion.id_usuario.username}'))
        
        # Crear Reviews
        for i, reserva in enumerate(reservas):  # Inicia una estructura de bloque en Python.
            review, created = Review.objects.get_or_create(  # Consulta o crea objetos en la base de datos.
                id_reserva=reserva,
                defaults={  # Proporciona valores por defecto para la creación de un objeto.
                    'id_propiedad': reserva.id_propiedad,
                    'id_usuario': reserva.id_huesped,
                    'calificacion': 4 + (i % 2),
                    'comentario': f'Excelente propiedad. El anfitrión fue muy amable y la ubicación es perfecta.',
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Review creada: {review.calificacion} estrellas'))
        
        self.stdout.write(self.style.SUCCESS('Datos de prueba cargados exitosamente!'))
