# Ejecutar Hospeda PY

Requisitos: Python 3.12 y Node.js 22.12 o posterior de la rama 22 LTS. También se admite Node 24. La máquina de desarrollo tenía Node 23.3; las pruebas y compilación pasaron, pero Vitest advierte que esa rama no está soportada. Preferir la versión LTS indicada en `frontend/.nvmrc`.

## Backend

Desde la raíz del proyecto, en una terminal PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000
```

Si el entorno ya existe y las dependencias están instaladas, ejecutar solo los dos últimos comandos. La actualización incorpora Django 5.2 y librerías nuevas: no usar el Python global anterior con Django 4.2. El archivo `.env.example` explica las variables; no reemplazar un `.env` existente sin conservar su configuración.

Para una base de demostración vacía se puede ejecutar `manage.py seed_data`. Este comando configura usuarios y propiedades de ejemplo; no debe ejecutarse sobre producción. Los usuarios de demostración son `admin` / `admin123`, `anfitrion1` / `test123` y `huesped1` / `test123`. Sus claves débiles son exclusivas de pruebas y deben reemplazarse antes de exponer la instalación.

Para crear un administrador propio:

```powershell
.\.venv\Scripts\python.exe manage.py createsuperuser
```

## Frontend

En otra terminal, desde la raíz:

```powershell
cd frontend
npm.cmd ci
npm.cmd run dev
```

Abrir **http://127.0.0.1:5173/**. Mantener ambas terminales abiertas. Usar el mismo nombre de host durante el recorrido; no alternar entre `localhost` y `127.0.0.1` para la sesión.

Vite redirige `/api`, `/media`, `/admin` y `/static` al backend local. No es necesario habilitar CORS abierto ni guardar tokens en el navegador. Si Django usa otro puerto, iniciar Vite así:

```powershell
$env:HOSPEDA_API_PROXY='http://127.0.0.1:8001'
npm.cmd run dev
```

La versión npm 10.9.0 instalada en esta máquina falló internamente al resolver la actualización de Vitest. Se completó con una versión temporal de npm, sin cambiar la instalación global. Si se reproduce ese error de npm, usar:

```powershell
npx.cmd --yes npm@11.6.2 ci
```

## Direcciones útiles

| Dirección | Uso |
| --- | --- |
| `http://127.0.0.1:5173/` | Aplicación Hospeda PY |
| `http://127.0.0.1:8000/admin/` | Administración Django |
| `http://127.0.0.1:8000/api/v1/documentacion/` | Swagger |
| `http://127.0.0.1:8000/api/v1/redoc/` | ReDoc |
| `http://127.0.0.1:8000/api/v1/esquema/` | Contrato OpenAPI |
| `http://127.0.0.1:8000/api/health/` | Estado del backend |

## Comprobar cambios

Desde la raíz:

```powershell
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py makemigrations --check --dry-run
.\.venv\Scripts\python.exe manage.py test presupuesto --noinput
.\.venv\Scripts\python.exe manage.py spectacular --validate --fail-on-warn --file docs/openapi.yaml
```

Desde `frontend`:

```powershell
npm.cmd test
npm.cmd run build
npm.cmd audit
```

`dist/` contiene el frontend compilado. `npm run preview` sirve ese build para inspección, pero no configura por sí solo el proxy de desarrollo: para un entorno completo usar `npm run dev` o desplegar el build con la API configurada.

## Solución de problemas

- **No conecta con el servidor:** comprobar que Django está en el puerto 8000 y que Vite está iniciado. Revisar las dos terminales.
- **Faltan tablas:** ejecutar las migraciones con el Python del entorno `.venv`.
- **Token anterior inválido:** volver a iniciar sesión; se sustituyó el formato propio por Simple JWT.
- **La foto no se publica:** comprobar formato, tamaño, dimensiones y límite acumulado de cinco fotos. El mensaje de la API explica el rechazo.
- **Error 429:** esperar un minuto. Hay límites de solicitudes para evitar abuso.
- **Swagger no carga su interfaz:** usa recursos CDN de la herramienta; la API y el archivo OpenAPI siguen disponibles. El frontend principal no depende de esos recursos.
- **Producción:** seguir `seguridad_despliegue.md`; no publicar `runserver`, credenciales demo, SQLite o media local como infraestructura multiusuario.
