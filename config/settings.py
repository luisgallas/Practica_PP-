"""
Django settings for Practica_PP project.
"""

from pathlib import Path  # Importa nombres concretos desde un módulo.
from datetime import timedelta
from django.core.exceptions import ImproperlyConfigured
import os  # Importa un módulo de Python.
from decouple import config  # Importa nombres concretos desde un módulo.
#define la carpeta base del proyecto
BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = config('SECRET_KEY', default='django-insecure-test-key-change-in-production')

try:
    DEBUG = config('DEBUG', default=True, cast=bool)
except ValueError:
    DEBUG = True

ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1').split(',')
FRONTEND_URL = config('FRONTEND_URL', default='http://127.0.0.1:5173')
if not DEBUG and (SECRET_KEY.startswith('django-insecure') or len(SECRET_KEY) < 50):
    raise ImproperlyConfigured('En producción configurá SECRET_KEY con al menos 50 caracteres aleatorios.')
#activa las aplicaciones instaladas en el proyecto
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',  # Agrega Django REST Framework a las aplicaciones instaladas
    'rest_framework_simplejwt.token_blacklist',
    'corsheaders',
    'drf_spectacular',
    'presupuesto.apps.PresupuestoConfig',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]
#indica donde estan las urls principales del proyecto
ROOT_URLCONF = 'config.urls'
#configura templates html en la carpeta templates 
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'
#configura la base de datos, por defecto sqlite3, pero puede ser configurada para postgresql
DB_ENGINE = config('DB_ENGINE', default='django.db.backends.sqlite3')
DB_NAME = config('DB_NAME', default='db.sqlite3')

if DB_ENGINE == 'django.db.backends.sqlite3':
    DATABASES = {
        'default': {
            'ENGINE': DB_ENGINE,
            'NAME': BASE_DIR / DB_NAME,
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': DB_ENGINE,
            'NAME': DB_NAME,
            'USER': config('DB_USER', default='postgres'),
            'PASSWORD': config('DB_PASSWORD', default='postgres'),
            'HOST': config('DB_HOST', default='localhost'),
            'PORT': config('DB_PORT', default='5432'),
        }
    }
#defina los validadores de contraseñas para el proyecto
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]
#pone el idiomas en español y la zona horaria en Buenos Aires
LANGUAGE_CODE = 'es-es'

TIME_ZONE = 'America/Asuncion'

USE_I18N = True

USE_TZ = True

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

AUTH_USER_MODEL = 'presupuesto.Usuario'
#configura Django REST Framework para usar autenticación JWT y autenticación de sesión
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'DEFAULT_THROTTLE_CLASSES': ['rest_framework.throttling.AnonRateThrottle', 'rest_framework.throttling.UserRateThrottle'],
    'DEFAULT_THROTTLE_RATES': {'anon': '120/min', 'user': '600/min', 'ingreso': '10/min', 'fotos': '20/min'},
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=10),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
}
SPECTACULAR_SETTINGS = {'TITLE': 'Hospeda PY API', 'VERSION': '2.0.0', 'SCHEMA_PATH_PREFIX': r'/api/v1', 'SERVE_INCLUDE_SCHEMA': False, 'DEFAULT_GENERATOR_CLASS': 'presupuesto.esquema.GeneradorEsquema'}
CORS_ALLOWED_ORIGINS = config('CORS_ALLOWED_ORIGINS', default='http://127.0.0.1:5173,http://localhost:5173').split(',')
CORS_ALLOW_CREDENTIALS = True
CSRF_TRUSTED_ORIGINS = config('CSRF_TRUSTED_ORIGINS', default='http://127.0.0.1:5173,http://localhost:5173').split(',')
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
SESSION_COOKIE_HTTPONLY = True
REFRESH_COOKIE_SAMESITE = config('REFRESH_COOKIE_SAMESITE', default='Lax')
CSRF_COOKIE_SAMESITE = REFRESH_COOKIE_SAMESITE
SECURE_SSL_REDIRECT = config('SECURE_SSL_REDIRECT', default=not DEBUG, cast=bool)
SECURE_HSTS_SECONDS = 0 if DEBUG else 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = not DEBUG
SECURE_HSTS_PRELOAD = not DEBUG
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = 'same-origin'
X_FRAME_OPTIONS = 'DENY'
DATA_UPLOAD_MAX_MEMORY_SIZE = 27 * 1024 * 1024
FILE_UPLOAD_MAX_MEMORY_SIZE = 1024 * 1024
DATA_UPLOAD_MAX_NUMBER_FILES = 5
if DB_ENGINE != 'django.db.backends.sqlite3':
    DATABASES['default']['CONN_MAX_AGE'] = 60
    DATABASES['default']['CONN_HEALTH_CHECKS'] = True
else:
    DATABASES['default']['OPTIONS'] = {'timeout': 20}
if config('REDIS_URL', default=''):
    CACHES = {'default': {'BACKEND': 'django.core.cache.backends.redis.RedisCache', 'LOCATION': config('REDIS_URL')}}
if config('AWS_STORAGE_BUCKET_NAME', default=''):
    STORAGES = {
        'default': {'BACKEND': 'storages.backends.s3.S3Storage', 'OPTIONS': {
            'bucket_name': config('AWS_STORAGE_BUCKET_NAME'),
            'region_name': config('AWS_S3_REGION_NAME', default='us-east-1'),
            'default_acl': None, 'file_overwrite': False,
            'object_parameters': {'CacheControl': 'max-age=86400'},
        }},
        'staticfiles': {'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage'},
    }
