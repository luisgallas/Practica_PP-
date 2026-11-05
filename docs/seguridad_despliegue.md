# Seguridad y despliegue de Hospeda PY

El sistema aplica controles en Django, independientemente de lo que muestre React. Este documento describe los controles implementados y la configuración necesaria para usar más de una instancia del backend. No afirma capacidad para una cantidad determinada de usuarios; esa capacidad requiere mediciones con la infraestructura final.

## Identidad y permisos

El navegador mantiene el access token únicamente en memoria. Simple JWT limita su duración a diez minutos. El refresh se guarda durante un día en una cookie HttpOnly, con `Secure` al desactivar DEBUG, y se rota con revocación de la versión anterior. El logout invalida el refresh. Un access token ya emitido conserva validez hasta expirar; no se promete revocación inmediata de ese token.

Login, registro, renovación y salida exigen CSRF. La obtención del token CSRF usa un GET sin caché. Axios comparte una sola renovación cuando coinciden errores de autenticación y no reintenta indefinidamente. No se guardan tokens en localStorage ni sessionStorage.

Los permisos se evalúan en cada operación. Los anfitriones solo modifican sus publicaciones; los huéspedes solo acceden a sus reservas; los administradores consultan el conjunto global. Los datos públicos de anfitriones no incluyen correo ni teléfono. El registro público permite únicamente huésped o anfitrión. Un superusuario se registra con el rol administrador.

El endpoint del asistente requiere autenticación e ignora identidades enviadas por el cliente. Las acciones pendientes llevan firma, usuario y vencimiento. La pantalla de pruebas del admin también fija la identidad de usuarios no administradores y guarda las acciones pendientes en sesión.

Las rutas antiguas permanecen por compatibilidad, pero el frontend usa `/api/v1/`. Los tokens HMAC anteriores dejan de ser válidos: es necesario iniciar sesión otra vez tras actualizar.

## Fotografías

El límite de cinco fotos se verifica en la interfaz, la API, el modelo y el formulario administrativo. La API bloquea la fila del alojamiento dentro de una transacción antes de añadir fotos; PostgreSQL serializa las cargas concurrentes. El servidor verifica los bytes, no solo la extensión o el MIME.

Se admiten JPEG, PNG y WebP de hasta 5 MB y 20 megapíxeles. Pillow decodifica, corrige la orientación, reduce a un máximo de 1600 × 1600 y vuelve a codificar a WebP. No se conservan los metadatos EXIF. Los nombres se generan con UUID. SVG, archivos falsos y contenido dañado se rechazan. La validación se realiza antes de publicar un lote. Los archivos creados durante un lote fallido se eliminan como compensación.

Las fotografías antiguas no se recodifican automáticamente: deben revisarse o volver a cargarse antes de exponer archivos heredados. No se eliminó contenido anterior. En producción, el proxy debe limitar el cuerpo completo de una subida a 27 MB; el límite de Django para datos en memoria no reemplaza un límite de cuerpo en el servidor HTTP. Servir media desde un almacenamiento externo con tipos de contenido correctos y sin ejecución de scripts.

## Reservas y concurrencia

Django calcula el total usando precio por noche, viernes/sábado y limpieza. Ignora importes o estados enviados para forzar una creación. Valida fechas, capacidad, máximo de 365 noches y solapamientos. Las solicitudes pendientes, confirmadas y activas ocupan las fechas.

La creación, cancelación y transición de estado usan transacciones y bloqueos de la fila del alojamiento. El formulario administrativo revalida la disponibilidad bajo ese bloqueo. Las transiciones permitidas son pendiente → confirmada o rechazada, confirmada → activa, activa → completada. La entrada y salida no pueden registrarse antes de sus fechas. Solo reservas pendientes o confirmadas se cancelan.

SQLite sirve para desarrollo; no ofrece el bloqueo de filas utilizado para coordinar reservas concurrentes. Usar PostgreSQL antes de un despliegue con varios procesos. La prueba de concurrencia se omite expresamente con SQLite y el workflow de CI la ejecuta contra PostgreSQL 16. La configuración del workflow no es evidencia de una ejecución remota: debe revisarse su resultado en GitHub.

## Rendimiento

La API nueva pagina doce registros por defecto y limita a 48 por página. Los filtros de ciudad, precio, capacidad, servicios y fechas se ejecutan en la base de datos. La disponibilidad usa subconsultas `EXISTS`. Las consultas de alojamiento y reservas precargan fotos, anfitriones y servicios para evitar consultas adicionales por tarjeta. Hay índices de estado/ciudad y de alojamiento/estado/fechas de reserva.

React carga páginas bajo demanda. TanStack Query conserva respuestas durante treinta segundos, evita repetir consultas equivalentes e invalida los datos después de escrituras. Las fotografías de tarjetas se cargan de forma diferida y tienen dimensiones explícitas. El build usa recursos con hash para almacenamiento en caché.

La búsqueda `icontains` por ciudad necesita índices de texto adicionales si el catálogo crece mucho; el índice compuesto no garantiza optimizar búsquedas de subcadenas. Los listados antiguos y las consultas conversacionales amplias requieren evaluación adicional de volumen. No se realizaron pruebas de carga ni se declara una cifra de usuarios concurrentes soportados.

## Configuración de producción

1. Crear PostgreSQL y ejecutar las migraciones. Usar credenciales de aplicación con privilegios mínimos y backups restaurables.
2. Configurar `DEBUG=False`, `SECRET_KEY` aleatoria de al menos 50 caracteres y `ALLOWED_HOSTS` con los dominios reales. El arranque rechaza la clave insegura de desarrollo cuando DEBUG está desactivado.
3. Servir Django con un servidor WSGI/ASGI de producción detrás de HTTPS; `runserver` es solo para desarrollo. Configurar el proveedor para comunicar HTTPS correctamente. Si se termina TLS en un proxy, habilitar `SECURE_PROXY_SSL_HEADER` solamente cuando ese proxy limpie y establezca de forma fiable el encabezado reenviado. No confiar en encabezados recibidos directamente de Internet.
4. Ejecutar `collectstatic`. WhiteNoise sirve recursos estáticos; las fotografías deben estar en almacenamiento compartido.
5. Configurar `AWS_STORAGE_BUCKET_NAME`, región y credenciales mediante variables secretas o identidad del proveedor. Django usa el backend S3. No guardar las credenciales en Git ni en variables `VITE_*`.
6. Configurar `REDIS_URL` para compartir contadores de límite de solicitudes entre instancias. Sin Redis, el caché local solo limita dentro de un proceso. Los límites de DRF son una capa adicional, no una defensa suficiente contra ataques distribuidos; aplicar límites y monitoreo en el proxy.
7. Configurar CORS y CSRF con los orígenes exactos del frontend. Preferir `app.ejemplo.com` y `api.ejemplo.com` bajo el mismo sitio y HTTPS, manteniendo `SameSite=Lax`. Para dominios de sitios distintos, `REFRESH_COOKIE_SAMESITE=None` exige HTTPS y está sujeto al bloqueo de cookies de terceros del navegador. La opción más robusta es compartir sitio o usar un proxy de mismo origen.
8. Compilar React con `VITE_API_URL=https://api.ejemplo.com/api/v1/`. En Vercel, elegir `frontend` como raíz, `npm run build` y `dist` como salida. `vercel.json` configura la recuperación de rutas de la SPA. No publica el backend ni sustituye sus variables de entorno.
9. Ejecutar las pruebas con PostgreSQL, `check --deploy`, revisión visual, auditorías de accesibilidad y pruebas de carga antes de habilitar usuarios reales.
10. Programar diariamente `python manage.py flushexpiredtokens`, mantener backups, observabilidad y actualizaciones de dependencias. Revisar políticas de caché y expiración de los archivos en el almacenamiento.

No se aprovisionaron servicios de terceros ni se transmitieron documentos o datos del proyecto a un hosting.

## Referencias técnicas

- [Configuración oficial de Simple JWT](https://django-rest-framework-simplejwt.readthedocs.io/en/stable/settings.html): duración, rotación y revocación de tokens.
- [Lista de revocación de Simple JWT](https://django-rest-framework-simplejwt.readthedocs.io/en/stable/blacklist_app.html): limpieza de tokens vencidos.
- [Seguridad de contenido subido en Django](https://docs.djangoproject.com/en/5.2/topics/security/#user-uploaded-content): riesgos del almacenamiento y entrega de archivos.
- [Guía de Vite](https://vite.dev/guide/): ejecución y construcción del frontend.
