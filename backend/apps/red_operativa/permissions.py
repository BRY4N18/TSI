"""DRF permissions for red_operativa (alta-unidades)."""

from __future__ import annotations

from rest_framework.permissions import BasePermission

ROLE_ADMIN = "Administrador"
ROLE_OPERADOR = "Operador"
ROLE_DIRECTOR_TECNOLOGICO = "DirectorTecnologico"


class IsAdministradorRedOperativa(BasePermission):
    """Exclusivo para CU-O54, O56, O57, O58 (RN-CAM-002)."""

    def has_permission(self, request, view) -> bool:
        user = request.user
        if not user or not getattr(user, "is_authenticated", False):
            return False
        return ROLE_ADMIN in getattr(user, "roles", [])


class IsOperadorDisponibilidadExterna(BasePermission):
    """Exclusivo para CU-O59 (RN-CAM-002)."""

    def has_permission(self, request, view) -> bool:
        user = request.user
        if not user or not getattr(user, "is_authenticated", False):
            return False
        return ROLE_OPERADOR in getattr(user, "roles", [])


class IsAdministradorOrOperador(BasePermission):
    """Lectura de detalle: ambos roles pueden consultar una unidad."""

    def has_permission(self, request, view) -> bool:
        user = request.user
        if not user or not getattr(user, "is_authenticated", False):
            return False
        roles = set(getattr(user, "roles", []))
        return ROLE_ADMIN in roles or ROLE_OPERADOR in roles


class IsDirectorTecnologico(BasePermission):
    """Exclusivo para CU-O61 (re-evaluar/despublicar región en producción)."""

    def has_permission(self, request, view) -> bool:
        user = request.user
        if not user or not getattr(user, "is_authenticated", False):
            return False
        return ROLE_DIRECTOR_TECNOLOGICO in getattr(user, "roles", [])


class IsAdministradorOrDirectorTecnologico(BasePermission):
    """Ejecutar/consultar CU-O55/O60: Administrador ejecuta, Director Tecnológico aprueba;
    ambos pueden consultar historial y ejecutar la validación (RF-REGON-001.5)."""

    def has_permission(self, request, view) -> bool:
        user = request.user
        if not user or not getattr(user, "is_authenticated", False):
            return False
        roles = set(getattr(user, "roles", []))
        return ROLE_ADMIN in roles or ROLE_DIRECTOR_TECNOLOGICO in roles
