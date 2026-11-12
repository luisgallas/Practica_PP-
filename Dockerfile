# Backend Django: ejecutar docker build desde la raiz del repositorio.
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Los cambios del codigo no obligan a reinstalar las dependencias.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN mkdir -p /app/data /app/media

EXPOSE 8000

# La base se prepara al arrancar, no durante la construccion de la imagen.
# exec permite que Gunicorn reciba directamente la senal de docker stop.
CMD ["sh", "-c", "python manage.py migrate --noinput && python manage.py collectstatic --noinput && exec gunicorn config.wsgi:application --bind 0.0.0.0:8000 --access-logfile - --error-logfile -"]
