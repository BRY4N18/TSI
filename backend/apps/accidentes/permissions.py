"""DRF permissions for accidentes module."""

from rest_framework.permissions import BasePermission

ROLE_TECNICO = "Tecnico"
ROLE_OPERADOR = "Operador"
ROLE_UNIDAD = "Unidad"
ROLE_ADMIN = "Administrador"
ROLE_CLIENTE = "Cliente"
ROLE_PROVEEDOR = "Proveedor"

TECNICO_CAMPO_ROLES = frozenset({ROLE_TECNICO, ROLE_OPERADOR})


class UbicacionCatalogoLecturaPermission(BasePermission):
    """Read-only access to the shared location catalog (país/estado/condado/ciudad/calle).

    Compartido entre accidentes, seguimiento y red-operativa/alta-unidades
    (proveedores de flota dan de alta unidades con este catálogo), ver
    proveedor-flota.guard.ts en el frontend.
    """

    def has_permission(self, request, view) -> bool:
        user = request.user
        if not user or not getattr(user, "is_authenticated", False):
            return False
        roles = set(getattr(user, "roles", []))
        return bool(
            roles & {ROLE_OPERADOR, ROLE_TECNICO, ROLE_ADMIN, ROLE_CLIENTE, ROLE_PROVEEDOR}
        )


class OperadorEmergenciasPermission(BasePermission):
    """Allows Operador de emergencias (JWT role: Operador)."""

    def has_permission(self, request, view) -> bool:
        user = request.user
        if not user or not getattr(user, "is_authenticated", False):
            return False
        return ROLE_OPERADOR in getattr(user, "roles", [])


class AccidentesLecturaPermission(BasePermission):
    """Read-only access to accidentes (list/detail): Operador, Tecnico or Administrador."""

    def has_permission(self, request, view) -> bool:
        user = request.user
        if not user or not getattr(user, "is_authenticated", False):
            return False
        roles = set(getattr(user, "roles", []))
        return bool(roles & {ROLE_OPERADOR, ROLE_TECNICO, ROLE_ADMIN})


class UnidadEmergenciaPermission(BasePermission):
    """Allows Unidad de emergencia (JWT role: Unidad)."""

    def has_permission(self, request, view) -> bool:
        user = request.user
        if not user or not getattr(user, "is_authenticated", False):
            return False
        return ROLE_UNIDAD in getattr(user, "roles", [])


class IsTecnicoCampoOrUnidadOrAdmin(BasePermission):
    """Gallery read: Técnico/Operador, Unidad or Administrador (RN-EVI-012)."""

    def has_permission(self, request, view) -> bool:
        user = request.user
        if not user or not getattr(user, "is_authenticated", False):
            return False
        roles = set(getattr(user, "roles", []))
        return bool(roles & TECNICO_CAMPO_ROLES) or ROLE_UNIDAD in roles or ROLE_ADMIN in roles


class IsTecnicoCampoOrUnidad(BasePermission):
    """Capture/write evidencia: Técnico/Operador or Unidad (not Administrador)."""

    def has_permission(self, request, view) -> bool:
        user = request.user
        if not user or not getattr(user, "is_authenticated", False):
            return False
        roles = set(getattr(user, "roles", []))
        return bool(roles & TECNICO_CAMPO_ROLES) or ROLE_UNIDAD in roles


# ── Informes tácticos simples (OT21–OT25) ────────────────────────────────────
#
# ⚠️ El acotamiento NO se declara aquí, sino en `resolver_cobertura`. Estos
# permisos solo abren la puerta; qué zonas ve cada quien lo decide el eje.

from core.auth.roles_tacticos import ROL_DIRECTOR_OPERACIONES  # noqa: E402

#: Quien opera el sistema por dentro. Ve todo, en cualquier situación.
#:
#: `DirectorOperaciones` es la autoridad del departamento (acceso-tactico §5).
#: ⚠️ Su exención es de **acotamiento**: no levanta la exclusión de coordenadas
#: ni de identidad de implicados, que son constitucionales (FR-014b).
ROLES_INTERNOS_EMERGENCIAS = frozenset(
    {ROLE_OPERADOR, ROLE_TECNICO, ROLE_ADMIN, ROL_DIRECTOR_OPERACIONES}
)

#: Acotado a sus zonas contratadas y a los casos ya cerrados.
#:
#: ⚠️ `PartnerIntegracion` **no está aquí**: el acceso programático a los datos
#: de siniestralidad tiene su propio camino, con su alcance y su auditoría
#: (`consumo_datos_service`). Dejarlo entrar por el listado táctico duplicaría
#: ese control con otro que no lo audita (FR-013, escenario 8 de US1).
ROLES_CLIENTE_EMERGENCIAS = frozenset({ROLE_CLIENTE})

#: Casos: internos y Cliente. Los otros cuatro: **solo internos** (FR-013).
ROLES_INFORMES_CASOS = frozenset(
    ROLES_INTERNOS_EMERGENCIAS | ROLES_CLIENTE_EMERGENCIAS
)
ROLES_INFORMES_INTERNOS = frozenset(ROLES_INTERNOS_EMERGENCIAS)


class _RolesInformesPermission(BasePermission):
    """Base que falla cerrado: sin usuario, sin autenticar o sin rol, no pasa."""

    roles_permitidos: frozenset = frozenset()

    def has_permission(self, request, view) -> bool:
        user = request.user
        if not user or not getattr(user, "is_authenticated", False):
            return False
        return bool(self.roles_permitidos & set(getattr(user, "roles", []) or []))


class InformesCasosPermission(_RolesInformesPermission):
    """Casos: lo ve quien opera y el Cliente, cada uno con su alcance.

    Conceder aquí **no** implica ver todos los casos: un Cliente entra y queda
    limitado a sus zonas contratadas y a los ya cerrados.
    """

    roles_permitidos = ROLES_INFORMES_CASOS


class InformesEmergenciasInternoPermission(_RolesInformesPermission):
    """Despachos, evidencia y cierres: **solo roles internos** (FR-013)."""

    roles_permitidos = ROLES_INFORMES_INTERNOS
