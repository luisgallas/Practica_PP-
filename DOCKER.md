# Dockerización del frontend – Hospeda PY

## 1. Parte seleccionada

Elegí dockerizar el frontend de Hospeda PY, desarrollado con React, Vite y TypeScript. El proyecto utiliza npm para administrar sus dependencias.

Para realizar esta actividad, creé la rama `docker/frontend-mendoza` a partir de `main`, sin fusionarla con la rama principal.

## 2. Archivos utilizados

- **Dockerfile:** contiene las instrucciones necesarias para instalar las dependencias, compilar y ejecutar la aplicación.
- **.dockerignore:** permite excluir los archivos que no son necesarios para construir la imagen.
- **DOCKER.md:** contiene los comandos utilizados y las respuestas a las preguntas de la actividad.

## 3. Comandos utilizados

Ingresar a la carpeta del frontend:

`cd frontend`

Verificar la instalación de Docker:

`docker --version`

Construir la imagen:

`docker build -t guairadevs-frontend-mendoza .`

Listar las imágenes:

`docker images`

Crear y ejecutar el contenedor:

`docker run --name hospedapy-mendoza -p 127.0.0.1:3000:3000 guairadevs-frontend-mendoza`

Verificar los contenedores en ejecución:

`docker ps`

Consultar los registros del contenedor:

`docker logs hospedapy-mendoza`

Acceder al frontend desde el navegador:

`http://localhost:3000`

Detener el contenedor:

`docker stop hospedapy-mendoza`

Eliminar el contenedor, en caso de que sea necesario:

`docker rm hospedapy-mendoza`

## 4. Preguntas

### ¿Cuál es la diferencia entre una imagen y un contenedor?

Una imagen es como una plantilla que contiene todo lo necesario para que una aplicación funcione, como el código y las dependencias. En cambio, un contenedor es una instancia que se crea a partir de esa imagen. Podemos crear varios contenedores utilizando una misma imagen.

### ¿Por qué se copia requirements.txt o package.json antes que el resto del código?

Porque de esa manera Docker puede aprovechar la caché. Si hacemos algún cambio en el código, pero las dependencias siguen siendo las mismas, Docker puede reutilizar las dependencias instaladas anteriormente. Esto nos ayuda a ahorrar tiempo al construir la imagen.

En mi caso, utilicé `package.json` y `package-lock.json`, porque el frontend utiliza npm.

### ¿Qué pasaría si no existiera el .dockerignore?

Si no tuviéramos el `.dockerignore`, Docker podría incluir archivos que no necesitamos, como `node_modules`, archivos temporales o archivos con información privada. Esto podría hacer que la imagen sea más pesada, que la construcción tarde más tiempo y que se incluyan datos sensibles.

### ¿Qué significa -p 8000:8000 en el comando docker run?

Significa que el puerto 8000 de nuestra computadora se conecta con el puerto 8000 del contenedor. De esta manera, podemos acceder a la aplicación desde el navegador.

En mi caso, utilicé el puerto 3000 para el frontend. También agregué `127.0.0.1` para que la aplicación sea accesible solamente desde mi computadora.

### Si se elimina el contenedor, ¿qué pasa con los datos que estaban dentro?

Si eliminamos el contenedor, se pierden los datos que se guardaron únicamente dentro de su sistema de archivos. Por eso, si queremos conservar información importante, podemos utilizar volúmenes, que permiten mantener los datos independientemente del contenedor.

## 5. Verificación

**Resultado de la construcción:** La imagen del frontend se construyó correctamente utilizando `docker build`, sin errores.

**Resultado de la ejecución:** El contenedor se ejecutó correctamente utilizando `docker run` y el servidor Vite inició en el puerto 3000.

**Verificación desde el navegador:** Ingresé a `http://localhost:3000` y comprobé que la aplicación Hospeda PY carga y se visualiza correctamente desde el contenedor Docker.