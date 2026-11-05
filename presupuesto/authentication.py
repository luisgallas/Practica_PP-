"""Compatibilidad del backend anterior con JWT de Simple JWT."""
from datetime import timedelta
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.tokens import AccessToken

class SimpleJWTAuthentication(JWTAuthentication):
    pass

def create_jwt_for_user(user, expires_in=600):
    token = AccessToken.for_user(user)
    token.set_exp(lifetime=timedelta(seconds=expires_in))
    return str(token)

def decode_jwt(token):
    return AccessToken(token).payload
