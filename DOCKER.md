# Dockerización del backend Django

Elegí el backend porque este proyecto usa Django y su frontend es React con Vite, no Next.js. La imagen contiene Python 3.12, las dependencias y el código del backend. Gunicorn ejecuta `config.wsgi:application` en `0.0.0.0:8000` para aceptar conexiones desde fuera del contenedor.

Esta configuración sirve para la práctica local. Usa SQLite y `DEBUG=True`; no es una configuración de despliegue público. El contenedor empieza con una base nueva: no copia los usuarios, reservas ni fotos de mi instalación local.

## Rama de entrega

Desde la raíz del repositorio, con el árbol de trabajo limpio:

```powershell
git fetch origin main
git switch -c docker/backend-ferreira origin/main
```

La rama parte de `origin/main`, commit `280aca9`. Se usa la referencia remota actualizada porque el `main` local estaba atrasado. La entrega se sube como rama independiente y no se mergea a `main`.

## Construcción y ejecución

Abrir Docker Desktop y esperar a que el motor esté listo. En esta ejecución se inició con:

```powershell
docker desktop start
docker version
docker build -t hospeda-backend:ferreira .
```

El punto indica que la raíz del repositorio es el contexto de construcción. El `Dockerfile` copia primero `requirements.txt`, instala las dependencias (incluido Gunicorn) y después copia el código permitido por `.dockerignore`.

El puerto 8000 debe estar libre: si se está ejecutando Django localmente con `runserver`, detenerlo antes. Ejecutar en PowerShell:

```powershell
docker run -d --name hospeda-backend-ferreira -p 127.0.0.1:8000:8000 -e DEBUG=True -e ALLOWED_HOSTS=localhost,127.0.0.1 -e DB_ENGINE=django.db.backends.sqlite3 -e DB_NAME=/app/data/db.sqlite3 --mount type=volume,source=hospeda-ferreira-db,target=/app/data --mount type=volume,source=hospeda-ferreira-media,target=/app/media hospeda-backend:ferreira
docker ps --filter name=hospeda-backend-ferreira
docker logs hospeda-backend-ferreira
```

Se publica el puerto solamente en la interfaz local de la computadora. Los volúmenes nombrados se crean automáticamente si todavía no existen. Al arrancar se aplican las migraciones, se recopilan los archivos estáticos y se inicia Gunicorn. Si una preparación falla, el servidor no arranca y el error aparece en `docker logs`.

La configuración se pasa con `-e`; el archivo `.env` local no se incluye en la imagen. Para esta práctica se utiliza la clave de desarrollo predeterminada del proyecto. En un despliegue real se debe proporcionar una `SECRET_KEY` propia y configurar el entorno de producción.

## Verificación

Abrir en el navegador:

- http://localhost:8000/ : redirige al frontend React configurado en `FRONTEND_URL`; el frontend no forma parte de esta imagen.
- http://localhost:8000/api/health/ : estado del servicio.
- http://localhost:8000/api/v1/alojamientos/ : consulta a la base de datos; inicialmente estará vacía.

Comprobaciones adicionales:

```powershell
docker exec hospeda-backend-ferreira python manage.py check
docker exec hospeda-backend-ferreira python manage.py showmigrations --plan
```

Resultados obtenidos el 12/11/2026:

- La imagen se construyó correctamente; una segunda construcción reutilizó la caché de dependencias.
- El contenedor quedó en estado `Up`, publicando `127.0.0.1:8000->8000/tcp`.
- `/api/health/` respondió HTTP 200 con `{"status":"ok","service":"booking-api"}`.
- `/api/v1/alojamientos/` respondió HTTP 200 con `count: 0`, como corresponde a la base nueva.
- `manage.py check` no encontró problemas y `showmigrations --plan` mostró todas las migraciones aplicadas (`[X]`).
- Chrome en modo headless cargó `/api/health/` y renderizó `HTTP 200 OK`, `status: ok` y `service: booking-api`. La automatización de la ventana interactiva no estuvo disponible; se verificó con un perfil temporal separado.

Para repetir la comprobación con Chrome desde PowerShell:

```powershell
& 'C:\Program Files\Google\Chrome\Application\chrome.exe' --headless --disable-gpu --user-data-dir="$env:TEMP\hospeda-docker-browser" --dump-dom http://localhost:8000/api/health/
```

En la primera ejecución el puerto 8000 estaba ocupado por el `runserver` local. Se detuvo ese proceso y se arrancó el contenedor ya creado con `docker start hospeda-backend-ferreira`. La base SQLite local no se modificó.

## Detener y volver a iniciar

```powershell
docker stop hospeda-backend-ferreira
docker start hospeda-backend-ferreira
```

Para reemplazar el contenedor después de modificar el código, detenerlo, eliminarlo con `docker rm hospeda-backend-ferreira`, reconstruir la imagen y repetir el comando `docker run`. Los volúmenes nombrados conservan la base y las fotos. No eliminar esos volúmenes si se quieren mantener los datos.

## Preguntas

### ¿Cuál es la diferencia entre una imagen y un contenedor?

La imagen es el paquete preparado con el código y lo necesario para ejecutarlo. El contenedor es una instancia creada a partir de ese paquete, con sus procesos y su espacio de escritura. Puedo crear varios contenedores de una misma imagen. Detener un contenedor no elimina la imagen ni el contenedor.

### ¿Por qué se copia requirements.txt o package.json antes que el resto del código?

Para aprovechar la caché de construcción. Si cambio una vista de Django pero no las dependencias, Docker puede reutilizar el paso donde ya las instaló. Si copiara todo antes de instalarlas, un cambio pequeño del código invalidaría ese paso y tendría que repetir la instalación.

### ¿Qué pasaría si no existiera el .dockerignore?

Docker recibiría archivos que no necesita para construir el backend. Con `COPY . .` podrían terminar en la imagen el entorno virtual de Windows, el frontend, archivos temporales, la base local o claves del `.env`. Eso aumentaría el tamaño y el tiempo de construcción, y podría exponer datos privados. `.gitignore` no reemplaza a `.dockerignore`.

### ¿Qué significa -p 8000:8000 en el comando docker run?

El primer 8000 es el puerto de la computadora y el segundo es el puerto dentro del contenedor. Una petición a ese puerto de la computadora se redirige al servidor del contenedor. En mi comando agregué `127.0.0.1:` para que la publicación sea accesible solo desde esta computadora. `EXPOSE 8000` documenta el puerto, pero no lo publica: eso lo hace `-p`.

### Si se elimina el contenedor, ¿qué pasa con los datos que estaban dentro?

Se pierde lo escrito en su capa de archivos propia. La imagen original sigue existiendo, pero no incorpora automáticamente esos cambios. Los datos guardados en un volumen nombrado o en una carpeta montada desde la computadora permanecen fuera del ciclo de vida del contenedor. En este caso la base está en `hospeda-ferreira-db` y las fotos en `hospeda-ferreira-media`, por eso se pueden recuperar montando los mismos volúmenes en un contenedor nuevo. Detener el contenedor, sin eliminarlo, también conserva su capa de escritura.

## Subir la entrega sin mergear

```powershell
git add Dockerfile .dockerignore requirements.txt DOCKER.md
git commit -m "Dockerizar backend Django y documentar la practica"
git push -u origin docker/backend-ferreira
```

No ejecutar merge a `main`.
