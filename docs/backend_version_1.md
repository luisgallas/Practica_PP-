# Practica PP - Plataforma de Booking con agente IA

Backend Django REST para una plataforma de reservas de alojamientos tipo Airbnb, orientada a propiedades locales como casas, departamentos, cabanas y quintas. El sistema permite trabajar con roles de administrador, anfitrion y huesped desde el admin de Django, mas una API REST y un agente IA que consulta datos reales del backend.

Version actual: `1.0.0`

## Estado actual del proyecto

El proyecto ya cuenta con:

- Admin de Django adaptado por roles.
- Gestion de propiedades, amenities, fotos, reglas y precios.
- Reservas con validacion de fechas, capacidad y disponibilidad.
- Confirmacion o rechazo de reservas por parte del anfitrion.
- Cancelacion de reservas con reembolso simulado.
- Notificaciones internas.
- Historial de propiedades visitadas.
- Resenas post-visita.
- API REST con autenticacion por token simple tipo JWT.
- Agente IA integrado para consultas de propiedades, disponibilidad, reservas y resenas.
- Datos demo reproducibles con `seed_data`.
- Pruebas automatizadas.

Los paneles HTML antiguos de anfitrion y huesped fueron eliminados. El flujo principal queda centralizado en `/admin/`, usando permisos segun rol.

## Tecnologias

- Python 3.10 o superior.
- Django 4.2.
- Django REST Framework 3.15.2.
- python-decouple 3.8.
- SQLite por defecto.
- PostgreSQL opcional mediante variables de entorno.

Dependencias:

```powershell
python -m pip install -r requirements.txt
```

## Estructura principal

```text
Practica_PP-/
|-- config/                  # Configuracion principal de Django
|-- presupuesto/             # App principal del sistema de booking
|   |-- admin.py             # Admin por roles
|   |-- agent.py             # Logica del agente IA
|   |-- authentication.py    # Token simple tipo JWT
|   |-- models.py            # Modelos del dominio
|   |-- permissions.py       # Permisos de negocio
|   |-- serializers.py       # Serializadores REST
|   |-- services.py          # Reglas de reservas, disponibilidad y precios
|   |-- tests.py             # Pruebas automatizadas
|   |-- urls.py              # Rutas de la API
|   |-- views.py             # Vistas REST
|-- templates/admin/         # Personalizacion del admin/login
|-- docs/                    # Documentacion y evidencias
|-- scripts/                 # Scripts de prueba/demo
|-- manage.py
|-- requirements.txt
|-- README.md
```

## Instalacion local

1. Entrar a la carpeta del proyecto:

```powershell
cd C:\Users\pedfe\Desktop\Practica_PP-
```

2. Crear y activar un entorno virtual, si se desea:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

3. Instalar dependencias:

```powershell
python -m pip install -r requirements.txt
```

4. Aplicar migraciones:

```powershell
python manage.py migrate
```

5. Cargar datos de ejemplo:

```powershell
python manage.py seed_data
```

6. Iniciar el servidor:

```powershell
python manage.py runserver 127.0.0.1:8000
```

URLs utiles:

- Home: `http://127.0.0.1:8000/`
- Admin Django: `http://127.0.0.1:8000/admin/`
- API base: `http://127.0.0.1:8000/api/`
- Health check: `http://127.0.0.1:8000/api/health/`

## Configuracion con variables de entorno

El proyecto usa `python-decouple`. Se puede crear un archivo `.env` basado en `.env.example`.

Ejemplo local con SQLite:

```env
SECRET_KEY=django-insecure-dev-key-practica-pp
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
DB_ENGINE=django.db.backends.sqlite3
DB_NAME=db.sqlite3
```

Ejemplo con PostgreSQL:

```env
SECRET_KEY=change-me-in-production
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1,midominio.com
DB_ENGINE=django.db.backends.postgresql
DB_NAME=booking_db
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=localhost
DB_PORT=5432
```

Configuraciones relevantes:

- `AUTH_USER_MODEL = presupuesto.Usuario`
- `LANGUAGE_CODE = es-es`
- `TIME_ZONE = America/Argentina/Buenos_Aires`
- `MEDIA_URL = /media/`
- `MEDIA_ROOT = media/`
- `STATIC_URL = /static/`

## Usuarios demo

El comando `seed_data` crea estos usuarios:

| Usuario | Clave | Rol | Acceso |
| --- | --- | --- | --- |
| `admin` | `admin123` | `admin` | Superusuario y administracion global |
| `anfitrion1` | `test123` | `anfitrion` | Gestiona sus propiedades y reservas recibidas |
| `huesped1` | `test123` | `huesped` | Reserva, consulta propiedades y deja resenas |

Todos los roles tienen `is_staff=True` para poder entrar al admin de Django. Los permisos reales se controlan en `presupuesto/admin.py`.

## Roles y permisos en el admin

### Admin

Puede:

- Ver datos globales.
- Gestionar usuarios.
- Ver propiedades.
- Ver reservas.
- Ver notificaciones.
- Ver historial de propiedades visitadas.
- Ver resenas.
- Probar el agente IA desde `Preguntar a la IA`.

No puede:

- Agregar, modificar ni borrar resenas. Las resenas son contenido generado por huespedes y quedan como solo lectura para admin.

### Anfitrion

Puede:

- Entrar al admin.
- Ver solo sus propiedades.
- Agregar, editar, pausar o eliminar sus propiedades.
- Cargar fotos de propiedades.
- Asociar amenities.
- Ver reservas recibidas sobre sus propiedades.
- Confirmar reservas pendientes.
- Rechazar reservas pendientes.
- Ver ingresos simulados desde dashboard/API.
- Ver resenas recibidas sobre sus propiedades.
- Preguntar a la IA por reservas pendientes, cantidad de reservas, detalles y reservas del mes.

No puede:

- Ver propiedades de otros anfitriones.
- Editar reservas que no correspondan a sus propiedades.
- Crear reservas como huesped desde su rol de anfitrion.

### Huesped

Puede:

- Entrar al admin.
- Ver propiedades disponibles en modo solo lectura.
- Ver detalles de propiedades, precios, amenities, reglas y politica de cancelacion.
- Crear una reserva.
- Modificar una reserva propia mientras este en estado `pendiente`.
- Cancelar reservas cuando corresponda desde API.
- Ver sus reservas.
- Ver sus notificaciones.
- Ver su historial de propiedades visitadas.
- Agregar resenas post-visita.
- Preguntar a la IA sobre propiedades, disponibilidad, amenities, resenas y reservas.

No puede:

- Modificar una reserva ya confirmada por el anfitrion.
- Editar propiedades.
- Ver reservas de otros huespedes.
- Modificar resenas desde admin despues de crearlas.

## Modelos principales

### Usuario

Extiende `AbstractUser` e incorpora:

- `rol`: `admin`, `anfitrion` o `huesped`.
- `telefono`.
- `fecha_registro`.

### Propiedad

Representa un alojamiento publicado por un anfitrion.

Campos destacados:

- `titulo`
- `descripcion`
- `calle`
- `ubicacion`
- `tipo_alojamiento`
- `capacidad_maxima_huespedes`
- `precio_noche`
- `precio_fin_semana`
- `tarifa_limpieza`
- `estado`: disponible, pausada o inactiva
- `permite_mascotas`
- `permite_fumar`
- `permite_fiestas`
- `politica_cancelacion`: flexible, moderada o estricta
- `id_anfitrion`
- `amenities`

Tipos de alojamiento:

- `casa_entera`
- `habitacion_privada`
- `habitacion_compartida`

### PropiedadFoto

Permite cargar imagenes asociadas a una propiedad:

- `foto`
- `descripcion`
- `es_portada`
- `fecha_publicacion`

### Amenity

Representa servicios o comodidades:

- WIFI
- PISCINA
- ESTACIONAMIENTO
- COCINA COMPLETA
- AIRE ACONDICIONADO
- TV SMART
- otros

Los nombres se normalizan a mayusculas y sin acentos.

### Reserva

Representa una solicitud o reserva de alojamiento.

Estados:

- `pendiente`
- `confirmada`
- `activa`
- `completada`
- `cancelada`
- `rechazada`

Campos destacados:

- `fecha_inicio`
- `fecha_fin`
- `cantidad_huespedes`
- `estado`
- `precio_total`
- `fecha_cancelacion`
- `cancelada_por`
- `motivo_cancelacion`
- `monto_reembolso`
- `id_huesped`
- `id_propiedad`

Reglas importantes:

- No se puede reservar con fecha de entrada pasada.
- La fecha de salida debe ser posterior a la fecha de entrada.
- La cantidad de huespedes no puede superar la capacidad maxima de la propiedad.
- Una reserva pendiente bloquea disponibilidad.
- Una reserva confirmada o activa tambien bloquea disponibilidad.
- Una reserva cancelada o rechazada libera disponibilidad.

### Disponibilidad

Controla fechas disponibles, bloqueadas o reservadas por propiedad.

Estados:

- `disponible`
- `bloqueada`
- `reservada`

### Review

Resena hecha por un huesped sobre una reserva.

Campos:

- `calificacion`
- `comentario`
- `fecha`
- `id_usuario`
- `id_propiedad`
- `id_reserva`

### Notificacion

Se genera ante cambios importantes de reservas.

### HistorialPropiedadVisitada

Registra propiedades vistas por un huesped.

### AgenteIAConfig y PreguntarIA

Configuran y exponen el agente IA dentro del admin.

`PreguntarIA` es un modelo proxy usado solo para mostrar la pantalla de prueba del agente en el admin.

## Reglas de negocio de reservas

El flujo esperado es:

1. El huesped consulta propiedades.
2. El huesped crea una reserva.
3. La reserva queda en estado `pendiente`.
4. El anfitrion revisa la reserva.
5. El anfitrion puede confirmar o rechazar.
6. Si confirma, la reserva pasa a `confirmada`.
7. Si rechaza, la reserva pasa a `rechazada`.
8. Si se cancela, se calcula un reembolso simulado segun politica de cancelacion.

Validaciones aplicadas:

- Fechas pasadas: rechazadas.
- Fecha fin menor o igual a fecha inicio: rechazada.
- Capacidad excedida: rechazada.
- Solapamiento con reservas pendientes, confirmadas o activas: rechazado.
- Fechas bloqueadas en disponibilidad: rechazadas.

Calculo de precio:

- Dias de semana usan `precio_noche`.
- Viernes y sabado usan `precio_fin_semana`.
- Se suma `tarifa_limpieza`.
- El resultado se guarda en `precio_total`.

Politicas de cancelacion:

- `flexible`
- `moderada`
- `estricta`

El pago real no esta implementado. El reembolso es simulado.

## Admin de Django

Entrada:

```text
http://127.0.0.1:8000/admin/
```

El login fue personalizado en:

```text
templates/admin/login.html
```

Tambien se agrego un boton `Cancelar` en formularios del admin mediante:

```text
templates/admin/submit_line.html
```

Modulos visibles segun rol:

- Preguntar a la IA
- Amenities
- Notificaciones
- Propiedades
- Reservas
- Resenas
- Usuarios
- Agente IA
- Historial de propiedades visitadas

El orden y permisos se configuran en:

```text
presupuesto/admin.py
```

## API REST

Base:

```text
http://127.0.0.1:8000/api/
```

Tambien existe alias en mayuscula:

```text
http://127.0.0.1:8000/API/
```

### Endpoints publicos o de consulta

| Metodo | Endpoint | Descripcion |
| --- | --- | --- |
| `GET` | `/api/` | Informacion basica de la API |
| `GET` | `/api/health/` | Estado del servicio |
| `GET` | `/api/salud/` | Alias de health |
| `GET` | `/api/properties/` | Lista propiedades |
| `GET` | `/api/properties/{id}/` | Detalle de propiedad |
| `GET` | `/api/propiedades/` | Alias en espanol |
| `GET` | `/api/propiedades/{id}/` | Alias en espanol |
| `GET` | `/api/amenities/` | Lista amenities |
| `GET` | `/api/availability/` | Consulta disponibilidad |
| `GET` | `/api/agent/system-prompt/` | Prompt del agente |

### Endpoints con autenticacion

| Metodo | Endpoint | Rol esperado | Descripcion |
| --- | --- | --- | --- |
| `POST` | `/api/auth/login/` | Todos | Devuelve token de acceso |
| `GET` | `/api/auth/me/` | Todos | Datos del usuario autenticado |
| `GET` | `/api/reservations/` | Todos | Lista reservas segun rol |
| `POST` | `/api/reservations/` | Huesped/Admin | Crea reserva |
| `POST` | `/api/reservations/{id}/status/` | Anfitrion/Admin | Cambia estado |
| `POST` | `/api/reservations/{id}/cancel/` | Huesped/Admin | Cancela reserva |
| `GET` | `/api/notifications/` | Todos | Notificaciones del usuario |
| `GET` | `/api/guest/history/` | Huesped | Historial de visitas |
| `GET` | `/api/host/dashboard/` | Anfitrion | Estadisticas del anfitrion |
| `POST` | `/api/agent/chat/` | Opcional | Chat con agente IA |

## Autenticacion API

Login:

```powershell
curl.exe -X POST "http://127.0.0.1:8000/api/auth/login/" `
  -H "Content-Type: application/json" `
  -d "{\"username\":\"huesped1\",\"password\":\"test123\"}"
```

Respuesta esperada:

```json
{
  "access": "TOKEN",
  "user": {
    "id": 3,
    "username": "huesped1",
    "rol": "huesped"
  }
}
```

Usar token:

```powershell
curl.exe "http://127.0.0.1:8000/api/auth/me/" `
  -H "Authorization: Bearer TOKEN"
```

## Ejemplos de uso

### Consultar disponibilidad

```powershell
curl.exe "http://127.0.0.1:8000/api/availability/?start_date=2026-07-20&end_date=2026-07-25&guests=2"
```

### Crear reserva desde API

```powershell
curl.exe -X POST "http://127.0.0.1:8000/api/reservations/" `
  -H "Content-Type: application/json" `
  -H "Authorization: Bearer TOKEN" `
  -d "{\"id_propiedad\":1,\"fecha_inicio\":\"2026-07-20\",\"fecha_fin\":\"2026-07-22\",\"cantidad_huespedes\":2}"
```

### Confirmar reserva como anfitrion

```powershell
curl.exe -X POST "http://127.0.0.1:8000/api/reservations/1/status/" `
  -H "Content-Type: application/json" `
  -H "Authorization: Bearer TOKEN_ANFITRION" `
  -d "{\"estado\":\"confirmada\"}"
```

### Rechazar reserva como anfitrion

```powershell
curl.exe -X POST "http://127.0.0.1:8000/api/reservations/1/status/" `
  -H "Content-Type: application/json" `
  -H "Authorization: Bearer TOKEN_ANFITRION" `
  -d "{\"estado\":\"rechazada\"}"
```

### Cancelar reserva

```powershell
curl.exe -X POST "http://127.0.0.1:8000/api/reservations/1/cancel/" `
  -H "Content-Type: application/json" `
  -H "Authorization: Bearer TOKEN" `
  -d "{\"motivo\":\"Cambio de planes\"}"
```

## Agente IA

El agente IA vive en:

```text
presupuesto/agent.py
```

Pantalla de prueba en admin:

```text
Admin > Preguntar a la IA
```

Endpoint:

```text
POST /api/agent/chat/
```

El agente no consulta internet. Solo responde con datos reales disponibles en la base de datos del proyecto.

Puede:

- Consultar disponibilidad.
- Listar propiedades disponibles.
- Informar amenities.
- Informar reglas de casa.
- Informar precios y capacidad.
- Consultar resenas.
- Preparar una reserva.
- Pedir confirmacion antes de crear una reserva.
- Responder a anfitriones sobre reservas pendientes.
- Responder a administradores sobre cantidad y detalle de reservas globales.

No puede:

- Crear reservas sin confirmacion.
- Responder temas fuera del sistema de booking.
- Buscar informacion externa.

### Ejemplo: preguntar disponibilidad

```powershell
curl.exe -X POST "http://127.0.0.1:8000/api/agent/chat/" `
  -H "Content-Type: application/json" `
  -d "{\"message\":\"Hay propiedades disponibles del 20 al 25 de julio para 2 personas?\"}"
```

### Ejemplo: preparar reserva con confirmacion

Primer mensaje:

```powershell
curl.exe -X POST "http://127.0.0.1:8000/api/agent/chat/" `
  -H "Content-Type: application/json" `
  -d "{\"message\":\"Quiero reservar Quinta Guaira del 20 al 22 de julio del 2026 para 2 personas\",\"user_id\":3}"
```

La respuesta devuelve `pending_action`. Para confirmar, enviar otro POST:

```json
{
  "message": "confirmo",
  "confirm": true,
  "pending_action": {
    "type": "create_reservation",
    "data": {
      "property_id": 4,
      "guest_id": 3,
      "start_date": "2026-07-20",
      "end_date": "2026-07-22",
      "guests": 2
    }
  }
}
```

## Datos de ejemplo

`seed_data` crea:

- Usuarios demo.
- Configuracion del agente IA.
- Amenities base.
- Propiedades demo:
  - Casa cerca del centro.
  - Departamento moderno.
  - Cabana en la montana.
  - Quinta Guaira.
- Reservas demo.
- Una resena demo.
- Disponibilidad inicial.

Comando:

```powershell
python manage.py seed_data
```

## Pruebas y verificacion

Comandos recomendados:

```powershell
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test presupuesto
```

Estado actual verificado:

```text
19 tests OK
No changes detected
System check identified no issues
```

## Seguridad y configuracion sensible

El proyecto contempla:

- Variables de entorno para `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS` y base de datos.
- Control de permisos por rol.
- Proteccion CSRF en admin Django.
- Autenticacion API por token HMAC simple.
- Restriccion de edicion segun propietario y rol.

Para produccion se recomienda:

- Usar `DEBUG=False`.
- Cambiar `SECRET_KEY`.
- Configurar `ALLOWED_HOSTS`.
- Usar PostgreSQL.
- Servir `static` y `media` con una configuracion adecuada.
- Hacer backups periodicos de base de datos.
- Usar HTTPS.
- Reemplazar el token simple por JWT estandar o un proveedor de autenticacion robusto si el sistema pasa a produccion real.

## Alcance funcional frente a los requerimientos

Implementado:

- Publicacion de propiedades.
- Fotos de propiedades.
- Tipos de alojamiento.
- Precios por noche, fin de semana y limpieza.
- Amenities.
- Reglas de casa.
- Politica de cancelacion.
- Activar, pausar o inactivar propiedad.
- Calendario/disponibilidad por propiedad.
- Solicitud de reserva.
- Validacion de disponibilidad sin solapamiento.
- Estados completos de reserva.
- Cancelacion con reembolso simulado.
- Notificaciones.
- Panel por roles usando admin Django.
- Reviews.
- Historial de propiedades visitadas.
- IA de consultas.
- Variables de entorno.
- Pruebas automatizadas.

Pendiente o simulado:

- Pago real.
- Reembolso real.
- Backups automaticos de produccion.
- Envio real de email/SMS/push.
- Frontend publico independiente del admin.

## Documentacion adicional

- `docs/agent_entrega.md`
- `docs/dify_botpress_config.md`
- `docs/demo_requests.http`
- `docs/auditoria_tests.md`
- `scripts/demo_agent.ps1`

## Comandos rapidos

Instalar:

```powershell
python -m pip install -r requirements.txt
```

Migrar:

```powershell
python manage.py migrate
```

Cargar datos:

```powershell
python manage.py seed_data
```

Correr servidor:

```powershell
python manage.py runserver 127.0.0.1:8000
```

Probar:

```powershell
python manage.py test presupuesto
```

Entrar al admin:

```text
http://127.0.0.1:8000/admin/
```
