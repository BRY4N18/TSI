from rest_framework.permissions import BasePermission

from core.auth.roles_tacticos import AUTORIDAD_VENTAS_CRM

CRM_ROLES = {"Administrador", "GerenteVentas", "GerenteCuentasPublicas"}
NOTIF_ROLES = {"Administrador", "GerenteVentas", "GerenteCuentasPublicas"}

# ── Informes tácticos ────────────────────────────────────────────────────────
#
# Quién accede a los cuatro listados, según `specs/002-tactico/acceso-tactico.md` §5.
#
# **Rol amplio**: ve toda la cartera del departamento y puede filtrar por un
# ejecutivo concreto. Incluye al Administrador y al **Director de Marketing**,
# que es la autoridad departamental del §5.1 del SRS — accede a los cuatro
# listados **sin acotamiento por titularidad**, porque su función es supervisar
# y no tiene pantalla operativa que espejar.
#
# **Rol acotado**: los dos gerentes, forzados a su propia cartera. Es la regla
# del contrato común: un informe nunca es más amplio que la pantalla operativa
# del mismo dato.
ROLES_INFORMES_AMPLIOS = frozenset({"Administrador"} | set(AUTORIDAD_VENTAS_CRM))
ROLES_INFORMES_ACOTADOS = frozenset({"GerenteVentas", "GerenteCuentasPublicas"})

ROLES_INFORMES_VENTAS = frozenset(ROLES_INFORMES_AMPLIOS | ROLES_INFORMES_ACOTADOS)

#: L2 reasignaciones es supervisión pura: el reparto de cartera es decisión de
#: jefatura, no herramienta del gerente cuya cartera se reparte
#: (`acceso-tactico.md` §5, Ventas y CRM, fila 2).
ROLES_INFORMES_REASIGNACIONES = frozenset(ROLES_INFORMES_AMPLIOS)


class IsCRMUser(BasePermission):
    def has_permission(self, request, view):
        return bool(
            getattr(request.user, "is_authenticated", False)
            and CRM_ROLES.intersection(getattr(request.user, "roles", []) or [])
        )


class IsAdministradorCrm(BasePermission):
    def has_permission(self, request, view):
        roles = getattr(request.user, "roles", []) or []
        return bool(
            getattr(request.user, "is_authenticated", False) and "Administrador" in roles
        )


class IsGerenteOrAdminNotificaciones(BasePermission):
    def has_permission(self, request, view):
        return bool(
            getattr(request.user, "is_authenticated", False)
            and NOTIF_ROLES.intersection(getattr(request.user, "roles", []) or [])
        )


class _RolesInformesPermission(BasePermission):
    """Base que falla cerrado: sin usuario, sin autenticar o sin rol, no pasa.

    El orden importa. Si se leyeran los roles antes de verificar la
    autenticación, un objeto anónimo con un atributo `roles` inesperado podría
    conceder; así la única vía de entrada es tener el rol.
    """

    roles_permitidos: frozenset[str] = frozenset()

    def has_permission(self, request, view) -> bool:
        user = getattr(request, "user", None)
        if not user or not getattr(user, "is_authenticated", False):
            return False
        return bool(set(getattr(user, "roles", []) or []) & self.roles_permitidos)


class InformesVentasLecturaPermission(_RolesInformesPermission):
    """Cartera, demos y notificaciones: Administrador, Director de Marketing y gerentes.

    Conceder aquí **no** implica ver toda la cartera: el acotamiento por
    titularidad lo resuelve `core/informes/acotamiento.py`, y a un gerente lo
    fuerza a lo suyo. Este permiso solo decide quién llega al endpoint.
    """

    roles_permitidos = ROLES_INFORMES_VENTAS


class InformesReasignacionesPermission(_RolesInformesPermission):
    """Reasignaciones: solo rol amplio.

    Un gerente **no** accede, ni siquiera acotado a lo suyo. El reparto de
    cartera es una decisión sobre él, no una herramienta suya, y dársela acotada
    le mostraría de quién recibió o a quién perdió prospectos —información de
    jefatura— disfrazada de listado propio.
    """

    roles_permitidos = ROLES_INFORMES_REASIGNACIONES
