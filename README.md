# Hospeda PY

Aplicacion de alojamientos en Paraguay con frontend React y API Django. Mantiene los roles de administrador, anfitrion y huesped, reservas reales, favoritos, resenas, notificaciones y un asistente conectado al backend.

Version de la integracion: 2.0.0.

## Ejecutar el sistema

Las dependencias locales y la migracion nueva ya se prepararon. Iniciar ambas terminales desde la raiz del proyecto:

```powershell
# Terminal 1: Django
.\.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000
```

```powershell
# Terminal 2: React
cd frontend
npm.cmd run dev
```

Abrir **http://127.0.0.1:5173/**. Para instalar en otro equipo, consultar [Instalacion e inicio rapido](docs/inicio_rapido.md). Usar Python 3.12 y Node 22 LTS.

## Funciones principales

- Busqueda por destino, fechas, capacidad, precio, servicios y calificacion, con paginacion.
- Detalle con galeria, reglas, resenas y disponibilidad real.
- Solicitudes de reserva con total calculado en Django y confirmacion del anfitrion.
- Paneles diferenciados para huesped, anfitrion y administrador.
- Publicacion y edicion de alojamientos, incluyendo departamentos.
- Hasta cinco fotos por alojamiento: vista previa, validacion de contenido, compresion WebP y portada.
- Favoritos persistentes, notificaciones y resenas de estadias completadas.
- JWT estandar, cookie de renovacion HttpOnly, CSRF y permisos verificados en el servidor.
- Configuracion para PostgreSQL, Redis y almacenamiento S3; SQLite para desarrollo.

## Documentacion

- [Instalacion, comandos y solucion de problemas](docs/inicio_rapido.md)
- [Arquitectura frontend, requisitos de los documentos y manual por rol](docs/frontend.md)
- [Seguridad, rendimiento y despliegue](docs/seguridad_despliegue.md)
- [Resultados de pruebas y verificaciones pendientes](docs/verificacion_frontend.md)
- [Contrato OpenAPI](docs/openapi.yaml)
- [Documentacion historica del backend 1.0](docs/backend_version_1.md), conservada como referencia; no sustituye la documentacion actual.

Swagger: http://127.0.0.1:8000/api/v1/documentacion/.
Administracion: http://127.0.0.1:8000/admin/.

La implementacion esta conectada a datos reales. No procesa pagos. La revision visual en navegador y las pruebas de carga en infraestructura de produccion siguen pendientes; no se afirma capacidad para una cifra determinada de usuarios.
