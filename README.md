# Practica Profesional I - Sistema de Alquiler de Propiedades

## 📋 Descripción del Proyecto

Sistema de alquiler de propiedades (similar a Airbnb) desarrollado con Django y PostgreSQL. Permite a los usuarios ser anfitriones para alquilar sus propiedades y huéspedes para reservar alojamientos.

## 🛠️ Tecnologías Utilizadas

- **Backend**: Django 4.2.0
- **Base de Datos**: PostgreSQL
- **Python**: 3.8+
- **Gestión de Dependencias**: pip

## 📁 Estructura del Proyecto

```
Practica_PP-/
├── config/                     # Configuración principal de Django
│   ├── settings.py            # Configuración del proyecto
│   ├── urls.py                # URLs principales
│   ├── wsgi.py                # Configuración WSGI
│   └── asgi.py                # Configuración ASGI
├── presupuesto/               # App principal
│   ├── migrations/            # Migraciones de base de datos
│   ├── management/commands/   # Comandos personalizados
│   │   └── seed_data.py       # Script para cargar datos de prueba
│   ├── models.py              # Modelos de datos
│   ├── admin.py               # Configuración del admin
│   ├── views.py               # Vistas
│   ├── urls.py                # URLs de la app
│   └── tests.py               # Tests
├── manage.py                  # Gestor de Django
├── requirements.txt           # Dependencias del proyecto
├── .env.example               # Archivo de ejemplo para variables de entorno
└── README.md                  # Este archivo
```

## 🗂️ Modelos de Datos

### Usuario
- Extensión de AbstractUser de Django
- Campos: username, email, contraseña, rol, teléfono, fecha_registro
- Roles: anfitrión, huésped, administrador

### Propiedad
- Gestiona las propiedades disponibles
- Relacionada con Usuario (anfitrión)
- Campos: título, descripción, ubicación, precios, estado
- Relación M2M con Amenities

### Amenity
- Comodidades disponibles en las propiedades
- Ejemplo: WiFi, Piscina, Estacionamiento

### Disponibilidad
- Controla los días disponibles de cada propiedad
- Estados: disponible, ocupada, bloqueada

### Reserva
- Gestiona las reservas de huéspedes
- Relaciona Usuario (huésped) con Propiedad
- Estados: pendiente, confirmada, cancelada, completada

### Notificación
- Notificaciones para usuarios sobre sus reservas
- Estados: no leída, leída, archivada

### Review
- Reseñas y calificaciones de propiedades
- Calificaciones de 1 a 5 estrellas

## 🚀 Instalación y Configuración

### 1. Clonar el Repositorio

```bash
git clone https://github.com/luisgallas/Practica_PP-.git
cd Practica_PP-
```

### 2. Crear un Entorno Virtual

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### 3. Instalar Dependencias

```bash
pip install -r requirements.txt
```

### 4. Configurar Variables de Entorno

Copiar el archivo `.env.example` a `.env` y actualizar las credenciales:

```bash
cp .env.example .env
```

Editar `.env` con tus credenciales de PostgreSQL:

```env
# Database Configuration
DB_ENGINE=django.db.backends.postgresql
DB_NAME=practica_pp
DB_USER=postgres
DB_PASSWORD=tu_contraseña
DB_HOST=localhost
DB_PORT=5432

# Django Settings
SECRET_KEY=tu_clave_secreta
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
```

### 5. Crear Base de Datos en PostgreSQL

```sql
CREATE DATABASE practica_pp;
```

### 6. Ejecutar Migraciones

```bash
python manage.py migrate
```

### 7. Crear Superusuario

```bash
python manage.py createsuperuser
```

Sigue las instrucciones para crear un usuario administrador.

### 8. Cargar Datos de Prueba

```bash
python manage.py seed_data
```

Este comando cargará:
- 5 usuarios de prueba (3 anfitriones, 2 huéspedes)
- 5 amenities (WiFi, Piscina, Estacionamiento, A/C, TV)
- 5 propiedades con amenities asociadas
- Disponibilidades para los próximos 30 días
- 5 reservas de prueba
- Notificaciones y reviews

### 9. Iniciar el Servidor de Desarrollo

```bash
python manage.py runserver
```

El servidor estará disponible en `http://localhost:8000`

## 🔐 Acceso al Panel de Administración

Una vez que el servidor esté corriendo, accede a:

```
http://localhost:8000/admin/
```

Usa las credenciales del superusuario que creaste.

## 📊 Funcionalidades Implementadas

✅ Modelos Django correctamente implementados
✅ Relaciones ForeignKey y ManyToMany configuradas
✅ Migraciones generadas y aplicadas
✅ Todos los modelos registrados en Django Admin
✅ list_display configurado con campos relevantes
✅ Base de datos PostgreSQL
✅ Variables de entorno con .env
✅ Script de datos de prueba (seed)
✅ README con instrucciones completas
✅ GitHub Actions configurado
✅ Branch protection rules habilitadas

## 🧪 Ejecutar Tests

```bash
python manage.py test
```

## 📝 Variables de Entorno Requeridas

- `DB_ENGINE`: Motor de base de datos (django.db.backends.postgresql)
- `DB_NAME`: Nombre de la base de datos
- `DB_USER`: Usuario de PostgreSQL
- `DB_PASSWORD`: Contraseña de PostgreSQL
- `DB_HOST`: Host de la base de datos
- `DB_PORT`: Puerto de la base de datos
- `SECRET_KEY`: Clave secreta de Django
- `DEBUG`: Modo debug (True/False)
- `ALLOWED_HOSTS`: Hosts permitidos

## 🔗 Relaciones de Modelos

```
Usuario (1) ──← (M) Propiedad
Usuario (1) ──← (M) Reserva (como huésped)
Usuario (1) ──← (M) Notificación
Usuario (1) ──← (M) Review

Propiedad (1) ──← (M) Reserva
Propiedad (1) ──← (M) Disponibilidad
Propiedad (1) ──← (M) Review
Propiedad (M) ── (M) Amenity (through PropiedadAmenity)

Reserva (1) ──← (1) Review
```

## 📦 Requisitos Mínimos

- Python 3.8 o superior
- PostgreSQL 12 o superior
- pip (gestor de paquetes de Python)

## 🐛 Solución de Problemas

### Error: "psycopg2 no se encuentra"

```bash
pip install psycopg2-binary
```

### Error: Conexión rechazada a PostgreSQL

Asegúrate de que:
1. PostgreSQL está ejecutándose
2. Las credenciales en `.env` son correctas
3. La base de datos existe

### Error: "tabla no existe"

Ejecuta las migraciones:

```bash
python manage.py migrate
```

## 👨‍💻 Autor

Luis Gallas

## 📅 Fecha

17 de mayo de 2026

## 📄 Licencia

Este proyecto es parte de la evaluación de Práctica Profesional I.
