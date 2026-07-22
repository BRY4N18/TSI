"""DRF permissions for gestión de tickets de soporte."""

from __future__ import annotations

from rest_framework.permissions import BasePermission

from apps.soporte_cliente.domain_constants import (
    ROL_ADMINISTRADOR,
    ROL_CLIENTE,
    ROL_DESARROLLADOR_APIS,
    ROL_DIRECTOR_TECNOLOGICO,
    ROL_SOPORTE,
)


class IsClienteSoporte(BasePermission):
    """Cliente role — registra tickets, comenta, confirma cierre, reabre."""

    def has_permission(self, request, view) -> bool:
        user = request.user
        if not user or not getattr(user, "is_authenticated", False):
            return False
        return ROL_CLIENTE in getattr(user, "roles", [])


class IsSoporteAgente(BasePermission):
    """Soporte al cliente (agente) — toma, comenta, escala, resuelve."""

    def has_permission(self, request, view) -> bool:
        user = request.user
        if not user or not getattr(user, "is_authenticated", False):
            return False
        roles = set(getattr(user, "roles", []))
        return ROL_SOPORTE in roles or ROL_ADMINISTRADOR in roles


class IsNivelEscaladoSoporte(BasePermission):
    """Desarrollador de APIs o Director Tecnológico — nivel de escalado."""

    def has_permission(self, request, view) -> bool:
        user = request.user
        if not user or not getattr(user, "is_authenticated", False):
            return False
        roles = set(getattr(user, "roles", []))
        return (
            ROL_DESARROLLADOR_APIS in roles
            or ROL_DIRECTOR_TECNOLOGICO in roles
            or ROL_ADMINISTRADOR in roles
        )


class IsSoporteAgenteOrNivelEscalado(BasePermission):
    """Soporte al cliente, Desarrollador de APIs o Director Tecnológico — resuelve tickets
    (incluye los ya escalados, ver transición Escalado -> Resuelto)."""

    def has_permission(self, request, view) -> bool:
        user = request.user
        if not user or not getattr(user, "is_authenticated", False):
            return False
        roles = set(getattr(user, "roles", []))
        return bool(
            roles
            & {ROL_SOPORTE, ROL_ADMINISTRADOR, ROL_DESARROLLADOR_APIS, ROL_DIRECTOR_TECNOLOGICO}
        )


class IsAdministradorSLA(BasePermission):
    """Administrador — configura Dim_SLAConfig (CU-O95)."""

    def has_permission(self, request, view) -> bool:
        user = request.user
        if not user or not getattr(user, "is_authenticated", False):
            return False
        return ROL_ADMINISTRADOR in getattr(user, "roles", [])


class IsSoporteAgenteOrCliente(BasePermission):
    """Lectura/listado accesible a Cliente (sus tickets) y agentes/admin (todos)."""

    def has_permission(self, request, view) -> bool:
        user = request.user
        if not user or not getattr(user, "is_authenticated", False):
            return False
        roles = set(getattr(user, "roles", []))
        return bool(
            roles
            & {ROL_CLIENTE, ROL_SOPORTE, ROL_ADMINISTRADOR, ROL_DESARROLLADOR_APIS, ROL_DIRECTOR_TECNOLOGICO}
        )
