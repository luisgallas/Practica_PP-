"""Validación por contenido y recodificación de fotografías, sin metadatos."""
from io import BytesIO
from uuid import uuid4
import warnings

from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from PIL import Image, ImageOps, UnidentifiedImageError

MAXIMO_FOTOS = 5
MAXIMO_BYTES = 5 * 1024 * 1024
MAXIMO_PIXELES = 20_000_000


def preparar_imagen(archivo):
    if archivo.size > MAXIMO_BYTES:
        raise ValidationError('Cada foto debe pesar como máximo 5 MB.')
    try:
        archivo.seek(0)
        with warnings.catch_warnings():
            warnings.simplefilter('error', Image.DecompressionBombWarning)
            with Image.open(archivo) as imagen:
                if imagen.format not in ('JPEG', 'PNG', 'WEBP'):
                    raise ValidationError('Solo se permiten imágenes JPEG, PNG o WebP.')
                if imagen.width * imagen.height > MAXIMO_PIXELES:
                    raise ValidationError('La imagen no puede superar 20 megapíxeles.')
                imagen.verify()
            archivo.seek(0)
            with Image.open(archivo) as original:
                imagen = ImageOps.exif_transpose(original).convert('RGB')
                imagen.thumbnail((1600, 1600))
                salida = BytesIO()
                imagen.save(salida, format='WEBP', quality=82, method=4)
        return ContentFile(salida.getvalue(), name=f'{uuid4().hex}.webp')
    except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError, Image.DecompressionBombWarning) as error:
        raise ValidationError('El archivo no es una imagen válida o está dañado.') from error
    finally:
        archivo.seek(0)
