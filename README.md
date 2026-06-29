# Practica PP - Booking con agente IA

Backend Django REST para un sistema de reservas de propiedades con un agente IA integrado. El agente responde consultas sobre propiedades, amenities, resenas, disponibilidad y reservas usando datos reales del backend.

Version de entrega: `1.0.0`.

## Funcionalidades principales

- Gestion de usuarios con roles `admin`, `anfitrion` y `huesped`.
- Catalogo de propiedades con direccion, ciudad, precios, estado y amenities.
- Consulta de disponibilidad por rango de fechas.
- Calculo de precio estimado por noches de semana, fin de semana y tarifa de limpieza.
- Creacion de reservas pendientes con bloqueo automatico de fechas.
- Agente conversacional para consultas y reservas con confirmacion obligatoria.
- Vista de admin para probar el agente como administrador, anfitrion o huesped.
- Datos de ejemplo reproducibles con `seed_data`.

## Requisitos

- Python 3.10 o superior.
- SQLite por defecto, o PostgreSQL configurando variables de entorno.

Instalar dependencias:

```powershell
python -m pip install -r requirements.txt
```

## Configuracion

Crear un archivo `.env` a partir de `.env.example` si se desea cambiar la configuracion local:

```env
DB_ENGINE=django.db.backends.sqlite3
DB_NAME=db.sqlite3
SECRET_KEY=django-insecure-dev-key-practica-pp
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
```

## Ejecucion local

```powershell
python manage.py migrate
python manage.py seed_data
python manage.py runserver 127.0.0.1:8000
```

URLs utiles:

- Home del backend: `http://127.0.0.1:8000/`
- Admin Django: `http://127.0.0.1:8000/admin/`
- API info: `http://127.0.0.1:8000/api/`

Usuarios demo cargados por `seed_data`:

| Usuario | Clave | Rol |
| --- | --- | --- |
| `admin` | `admin123` | `admin` |
| `anfitrion1` | `test123` | `anfitrion` |
| `huesped1` | `test123` | `huesped` |

## Endpoints principales

| Metodo | Endpoint | Descripcion |
| --- | --- | --- |
| `GET` | `/api/properties/` | Lista propiedades con anfitrion y amenities. |
| `GET` | `/api/properties/{id}/` | Detalle de una propiedad. |
| `GET` | `/api/amenities/` | Lista amenities. |
| `GET` | `/api/availability/?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD&guests=2` | Consulta disponibilidad y precio estimado. |
| `GET` | `/api/reservations/?host_id=2&status=pendiente&month=2026-06` | Lista reservas filtradas. |
| `POST` | `/api/reservations/` | Crea una reserva directa desde la API. |
| `POST` | `/api/agent/chat/` | Conversacion con el agente IA. |
| `GET` | `/api/agent/system-prompt/` | Expone el prompt de sistema del agente. |

## Ejemplos de prueba

Consultar disponibilidad:

```powershell
curl.exe "http://127.0.0.1:8000/api/availability/?start_date=2026-07-20&end_date=2026-07-25&guests=2"
```

Preguntar al agente:

```powershell
curl.exe -X POST "http://127.0.0.1:8000/api/agent/chat/" -H "Content-Type: application/json" -d "{\"message\":\"Hay propiedades disponibles del 20 al 25 de julio para 2 personas?\"}"
```

Crear una reserva con confirmacion:

```powershell
curl.exe -X POST "http://127.0.0.1:8000/api/agent/chat/" -H "Content-Type: application/json" -d "{\"message\":\"Quiero reservar Quinta Guaira del 20 al 22 de julio del 2026 para 2 personas\",\"user_id\":3}"
```

La primera respuesta devuelve `pending_action`; para crear la reserva se debe enviar un segundo POST con `confirm: true` y ese `pending_action`.

## Documentacion de entrega

- Detalle del agente, diagrama Mermaid y prompt: `docs/agent_entrega.md`
- Configuracion opcional para Dify/Botpress: `docs/dify_botpress_config.md`
- Evidencias de pantalla: `docs/captura_*.png`
- Video demostrativo: `docs/video_demo.mp4`
- Requests de prueba: `docs/demo_requests.http`
- Script de demo: `scripts/demo_agent.ps1`
- Auditoria de tests y refuerzos sugeridos: `docs/auditoria_tests.md`

## Verificacion

```powershell
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test presupuesto
```

Estado verificado para la entrega: `9 tests OK`.

## Alcance del agente IA

El agente esta limitado al dominio del sistema de booking. No consulta internet ni responde temas externos. Puede:

- Buscar propiedades disponibles por fechas.
- Informar amenities y datos de propiedades.
- Consultar resenas reales.
- Preparar reservas y pedir confirmacion antes de crearlas.
- Responder a anfitriones sobre sus reservas.
- Responder a administradores sobre reservas globales.
