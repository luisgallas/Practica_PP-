from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from presupuesto.models import Propiedad, Amenity, Disponibilidad, Reserva, Notificacion, Review
from datetime import datetime, timedelta

User = get_user_model()


class Command(BaseCommand):
    help = 'Carga datos de prueba en la base de datos'

    def handle(self, *args, **options):
        # Limpiar datos previos (opcional)
        self.stdout.write(self.style.WARNING('Creando datos de prueba...'))
        
        # Crear Usuarios
        users = []
        for i in range(5):
            username = f'usuario{i+1}'
            email = f'usuario{i+1}@example.com'
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
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
                user.set_password('password123')
                user.save()
                self.stdout.write(self.style.SUCCESS(f'✓ Usuario creado: {username}'))
        
        # Crear Amenities
        amenities_names = ['WiFi', 'Piscina', 'Estacionamiento', 'Aire acondicionado', 'TV']
        amenities = []
        for name in amenities_names:
            amenity, created = Amenity.objects.get_or_create(nombre=name)
            amenities.append(amenity)
            if created:
                self.stdout.write(self.style.SUCCESS(f'✓ Amenity creada: {name}'))
        
        # Crear Propiedades
        propiedades = []
        locations = ['Buenos Aires', 'Córdoba', 'Mendoza', 'Rosario', 'La Plata']
        for i in range(5):
            propiedad, created = Propiedad.objects.get_or_create(
                titulo=f'Casa Hermosa {i+1}',
                defaults={
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
                self.stdout.write(self.style.SUCCESS(f'✓ Propiedad creada: {propiedad.titulo}'))
            propiedades.append(propiedad)
        
        # Crear Disponibilidades
        for propiedad in propiedades:
            for days_ahead in range(30):
                fecha = datetime.now().date() + timedelta(days=days_ahead)
                disponibilidad, created = Disponibilidad.objects.get_or_create(
                    id_propiedad=propiedad,
                    fecha=fecha,
                    defaults={'estado': 'disponible'}
                )
                if created and days_ahead < 5:
                    self.stdout.write(f'  ✓ Disponibilidad creada para {propiedad.titulo} ({fecha})')
        
        # Crear Reservas
        reservas = []
        for i in range(5):
            fecha_inicio = datetime.now().date() + timedelta(days=5 + (i*5))
            fecha_fin = fecha_inicio + timedelta(days=3)
            
            reserva, created = Reserva.objects.get_or_create(
                id_propiedad=propiedades[i],
                fecha_inicio=fecha_inicio,
                defaults={
                    'id_huesped': users[(i+1) % len(users)],
                    'fecha_fin': fecha_fin,
                    'cantidad_huespedes': 2 + i,
                    'estado': 'confirmada',
                    'precio_total': 300 + (i * 100),
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'✓ Reserva creada: #{reserva.id}'))
            reservas.append(reserva)
        
        # Crear Notificaciones
        for i, reserva in enumerate(reservas[:3]):
            notificacion, created = Notificacion.objects.get_or_create(
                id_usuario=reserva.id_huesped,
                id_reserva=reserva,
                defaults={
                    'mensaje': f'Tu reserva en {reserva.id_propiedad.titulo} ha sido confirmada.',
                    'estado': 'no_leida',
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'✓ Notificación creada para {notificacion.id_usuario.username}'))
        
        # Crear Reviews
        for i, reserva in enumerate(reservas[:3]):
            review, created = Review.objects.get_or_create(
                id_reserva=reserva,
                defaults={
                    'id_propiedad': reserva.id_propiedad,
                    'id_usuario': reserva.id_huesped,
                    'calificacion': 4 + (i % 2),
                    'comentario': f'Excelente propiedad. El anfitrión fue muy amable y la ubicación es perfecta.',
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'✓ Review creada: {review.calificacion} estrellas'))
        
        self.stdout.write(self.style.SUCCESS('✓ ¡Datos de prueba cargados exitosamente!'))
