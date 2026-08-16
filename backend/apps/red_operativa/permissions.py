"""DRF permissions for red_operativa (alta-unidades + incorporacion-regional)."""

from __future__ import annotations

from rest_framework.permissions import BasePermission

from apps.red_operativa.services.proveedor_access_service import (
    ProveedorAccessError,
    ProveedorAccessService,
)

ROLE_ADMIN = "Administrador"
ROLE_DIRECTOR_TECNOLOGICO = "DirectorTecnologico"
ROLE_CLIENTE = "Cliente"
ROLE_PROVEEDOR = "Proveedor"


class IsProveedorFlota(BasePermission):
    """CU-O54/56/57/58 — solo Proveedor (admin_local de cuenta Activo). Sin override Admin."""

    def has_permission(self, request, view) -> bool:
        user = request.user
        if not user or not getattr(user, "is_authenticated", False):
            return False
        roles = list(getattr(user, "roles", []) or [])
        if ROLE_CLIENTE not in roles and ROLE_PROVEEDOR not in roles:
            return False
        try:
            cliente = ProveedorAccessService().resolve_cliente_activo(
                user_id=user.idusuario, roles=roles
            )
        except ProveedorAccessError:
            return False
        request.proveedor_idcliente = cliente["idcliente"]
        return True


class IsAdministradorRedOperativa(BasePermission):
    """CU-O60 rechazo definitivo / O62 manual — Administrador de red operativa."""

    def has_permission(self, request, view) -> bool:
        user = request.user
        if not user or not getattr(user, "is_authenticated", False):
            return False
        return ROLE_ADMIN in getattr(user, "roles", [])


class IsProveedorFlotaOrAdministrador(BasePermission):
    """CU-O42 baja: autoservicio del Proveedor + única excepción de baja forzada
    con despacho activo, reservada a Administrador (RF-O42.4). La validación de
    quién puede completar la baja forzada vive en BajaUnidadService, no aquí."""

    def has_permission(self, request, view) -> bool:
        user = request.user
        if not user or not getattr(user, "is_authenticated", False):
            return False
        if ROLE_ADMIN in getattr(user, "roles", []):
            return True
        return IsProveedorFlota().has_permission(request, view)


class IsDirectorTecnologico(BasePermission):
    """Exclusivo para CU-O61 (re-evaluar/despublicar región en producción)."""

    def has_permission(self, request, view) -> bool:
        user = request.user
        if not user or not getattr(user, "is_authenticated", False):
            return False
        return ROLE_DIRECTOR_TECNOLOGICO in getattr(user, "roles", [])


class IsAdministradorOrDirectorTecnologico(BasePermission):
    """Ejecutar/consultar CU-O55/O60."""

    def has_permission(self, request, view) -> bool:
        user = request.user
        if not user or not getattr(user, "is_authenticated", False):
            return False
        roles = set(getattr(user, "roles", []))
        return ROLE_ADMIN in roles or ROLE_DIRECTOR_TECNOLOGICO in roles


# ── Informes tácticos ────────────────────────────────────────────────────────
#
# Quién accede a los cuatro listados, según `acceso-tactico.md` §5. Aquí la
# autoridad también está **repartida por materia**, y el §5.1 del SRS lo
# subraya: el Tecnológico fija los criterios de validación de región; el de
# Expansión decide dónde crecer.
#
# Ambos necesitan el estado de las regiones; **solo el Tecnológico** necesita el
# detalle de por qué se rechazan.
ROLE_DIRECTOR_EXPANSION = "DirectorExpansion"

#: Flota y bajas: Administrador, Expansión y los roles de cuenta proveedora.
ROLES_INFORMES_FLOTA_ACOTADOS = frozenset({ROLE_CLIENTE, ROLE_PROVEEDOR})
AMPLIOS_FLOTA = frozenset({ROLE_ADMIN, ROLE_DIRECTOR_EXPANSION})
ROLES_INFORMES_FLOTA = frozenset(AMPLIOS_FLOTA | ROLES_INFORMES_FLOTA_ACOTADOS)

#: Regiones y validaciones: **sin acotamiento y sin proveedores**. Una región no
#: pertenece a ninguna empresa de flota, y su estado es materia de gobierno de la
#: red — no información que un proveedor deba ver (FR-012).
AMPLIOS_REGION = frozenset({ROLE_ADMIN, ROLE_DIRECTOR_TECNOLOGICO, ROLE_DIRECTOR_EXPANSION})
#: Los intentos de validación son solo del Tecnológico: es quien fija los
#: criterios, y el detalle de por qué se rechaza una región no le sirve a quien
#: decide dónde crecer.
AMPLIOS_VALIDACION = frozenset({ROLE_ADMIN, ROLE_DIRECTOR_TECNOLOGICO})


class _RolesInformesPermission(BasePermission):
    """Base que falla cerrado: sin usuario, sin autenticar o sin rol, no pasa.

    Conceder aquí **no** implica ver todas las flotas: el acotamiento por
    organización lo resuelve `core/informes/acotamiento.py`, y a un proveedor lo
    fuerza a la suya.
    """

    roles_permitidos: frozenset[str] = frozenset()

    def has_permission(self, request, view) -> bool:
        user = getattr(request, "user", None)
        if not user or not getattr(user, "is_authenticated", False):
            return False
        return bool(set(getattr(user, "roles", []) or []) & self.roles_permitidos)


class InformesFlotaPermission(_RolesInformesPermission):
    """Flota y bajas de unidad: acotado al proveedor cuando procede."""

    roles_permitidos = ROLES_INFORMES_FLOTA


class InformesRegionPermission(_RolesInformesPermission):
    """Regiones operativas: Administrador, Tecnológico y Expansión."""

    roles_permitidos = AMPLIOS_REGION


class InformesValidacionPermission(_RolesInformesPermission):
    """Intentos de validación: **solo** Administrador y Director Tecnológico.

    Es quien fija los criterios de validación (§5.1). El de Expansión ve el
    estado de las regiones —le dice dónde puede crecer— pero no el detalle de
    por qué se rechazan, que no cambia su decisión.
    """

    roles_permitidos = AMPLIOS_VALIDACION
