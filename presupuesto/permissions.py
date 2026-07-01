from rest_framework import permissions


class IsHost(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.rol == "anfitrion"


class IsGuest(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.rol == "huesped"


class IsAdminRole(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.rol == "admin"


def can_manage_reservation(user, reserva):
    if not user.is_authenticated:
        return False
    if user.rol == "admin":
        return True
    return user.rol == "anfitrion" and reserva.id_propiedad.id_anfitrion_id == user.id


def can_cancel_reservation(user, reserva):
    if not user.is_authenticated:
        return False
    if user.rol == "admin":
        return True
    if user.rol == "huesped":
        return reserva.id_huesped_id == user.id
    return user.rol == "anfitrion" and reserva.id_propiedad.id_anfitrion_id == user.id
