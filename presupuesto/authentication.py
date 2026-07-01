import base64
import hashlib
import hmac
import json
import time

from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework import authentication, exceptions


def _b64encode(payload):
    return base64.urlsafe_b64encode(payload).rstrip(b"=").decode("ascii")


def _b64decode(payload):
    padding = "=" * (-len(payload) % 4)
    return base64.urlsafe_b64decode(payload + padding)


def _sign(message):
    return _b64encode(
        hmac.new(settings.SECRET_KEY.encode("utf-8"), message.encode("ascii"), hashlib.sha256).digest()
    )


def create_jwt_for_user(user, expires_in=3600):
    header = {"alg": "HS256", "typ": "JWT"}
    payload = {
        "sub": user.id,
        "username": user.username,
        "rol": user.rol,
        "iat": int(time.time()),
        "exp": int(time.time()) + expires_in,
    }
    header_part = _b64encode(json.dumps(header, separators=(",", ":")).encode("utf-8"))
    payload_part = _b64encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    signature = _sign(f"{header_part}.{payload_part}")
    return f"{header_part}.{payload_part}.{signature}"


def decode_jwt(token):
    try:
        header_part, payload_part, signature = token.split(".")
    except ValueError as exc:
        raise exceptions.AuthenticationFailed("Token JWT invalido.") from exc

    expected_signature = _sign(f"{header_part}.{payload_part}")
    if not hmac.compare_digest(signature, expected_signature):
        raise exceptions.AuthenticationFailed("Firma JWT invalida.")

    try:
        payload = json.loads(_b64decode(payload_part).decode("utf-8"))
    except (ValueError, json.JSONDecodeError) as exc:
        raise exceptions.AuthenticationFailed("Payload JWT invalido.") from exc

    if payload.get("exp", 0) < int(time.time()):
        raise exceptions.AuthenticationFailed("Token JWT expirado.")
    return payload


class SimpleJWTAuthentication(authentication.BaseAuthentication):
    def authenticate(self, request):
        auth_header = authentication.get_authorization_header(request).decode("utf-8")
        if not auth_header:
            return None
        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            return None

        payload = decode_jwt(parts[1])
        user = get_user_model().objects.filter(id=payload.get("sub"), is_active=True).first()
        if not user:
            raise exceptions.AuthenticationFailed("Usuario del token no existe o esta inactivo.")
        return user, payload
