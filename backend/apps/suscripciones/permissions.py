"""DRF permissions — Proveedor / Administrador / DirectorEstrategia billing."""

from __future__ import annotations

from rest_framework.permissions import BasePermission

from apps.red_operativa.services.proveedor_access_service import (
    ProveedorAccessError,
    ProveedorAccessService,
)

ROLE_ADMIN = "Administrador"
ROLE_CLIENTE = "Cliente"
ROLE_PROVEEDOR = "Proveedor"
ROLE_DIRECTOR_ESTRATEGIA = "DirectorEstrategia"


class IsProveedorCuenta(BasePermission):
    """Proveedor/Cliente admin_local de cuenta Activo — setea request.billing_idcliente."""

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
        request.billing_idcliente = cliente["idcliente"]
        return True


class IsAdministradorBilling(BasePermission):
    def has_permission(self, request, view) -> bool:
        user = request.user
        if not user or not getattr(user, "is_authenticated", False):
            return False
        return ROLE_ADMIN in getattr(user, "roles", [])


class IsDirectorEstrategiaBilling(BasePermission):
    """RF-SUSF-001 — mutaciones Dim_Plan."""

    def has_permission(self, request, view) -> bool:
        user = request.user
        if not user or not getattr(user, "is_authenticated", False):
            return False
        return ROLE_DIRECTOR_ESTRATEGIA in getattr(user, "roles", [])


class IsProveedorOrAdminBilling(BasePermission):
    def has_permission(self, request, view) -> bool:
        if IsAdministradorBilling().has_permission(request, view):
            return True
        return IsProveedorCuenta().has_permission(request, view)


class IsCatalogoPlanesReader(BasePermission):
    """GET catálogo: Proveedor, Administrador o DirectorEstrategia."""

    def has_permission(self, request, view) -> bool:
        if IsDirectorEstrategiaBilling().has_permission(request, view):
            return True
        if IsAdministradorBilling().has_permission(request, view):
            return True
        return IsProveedorCuenta().has_permission(request, view)


# ── Informes tácticos ────────────────────────────────────────────────────────
#
# Quién accede a los cuatro listados, según `specs/002-tactico/acceso-tactico.md` §5.
#
# **Rol amplio**: ve todas las cuentas y puede filtrar por una. Incluye al
# Administrador y a las **dos autoridades departamentales** — aquí la autoridad
# está *repartida por materia*, y el §5.1 del SRS lo subraya: Estrategia decide
# catálogo y precios (suscripciones y cambios de plan), Financiero responde por
# el resultado económico (facturas y medios de cobro).
#
# **Rol acotado**: Cliente y Proveedor, forzados a su propia cuenta.
#
# ⚠️ **No se reutiliza `IsProveedorCuenta`.** Aquella clase admite solo Cliente y
# Proveedor: un Administrador que consultara facturas por esa vía recibiría un
# rechazo, y el Administrador es la mitad del caso de uso táctico. Además exige
# cuenta `Activo`, lo que dejaría sin ver su propia deuda a quien más necesita
# verla.
ROLES_INFORMES_ACOTADOS = frozenset({ROLE_CLIENTE, ROLE_PROVEEDOR})

#: L1 suscripciones y L3 cambios de plan → Estrategia (catálogo y precios).
ROLES_INFORMES_CATALOGO = frozenset(
    {ROLE_ADMIN, ROLE_DIRECTOR_ESTRATEGIA} | ROLES_INFORMES_ACOTADOS
)
AMPLIOS_CATALOGO = frozenset({ROLE_ADMIN, ROLE_DIRECTOR_ESTRATEGIA})

#: L2 facturas y L4 métodos de pago → Financiero (resultado económico).
ROLE_DIRECTOR_FINANCIERO = "DirectorFinanciero"
ROLES_INFORMES_FINANZAS = frozenset(
    {ROLE_ADMIN, ROLE_DIRECTOR_FINANCIERO} | ROLES_INFORMES_ACOTADOS
)
AMPLIOS_FINANZAS = frozenset({ROLE_ADMIN, ROLE_DIRECTOR_FINANCIERO})


class _RolesInformesPermission(BasePermission):
    """Base que falla cerrado: sin usuario, sin autenticar o sin rol, no pasa.

    Conceder aquí **no** implica ver todas las cuentas: el acotamiento por
    organización lo resuelve `core/informes/acotamiento.py`, y a un Cliente lo
    fuerza a la suya. Este permiso solo decide quién llega al endpoint.
    """

    roles_permitidos: frozenset[str] = frozenset()

    def has_permission(self, request, view) -> bool:
        user = getattr(request, "user", None)
        if not user or not getattr(user, "is_authenticated", False):
            return False
        return bool(set(getattr(user, "roles", []) or []) & self.roles_permitidos)


class InformesCatalogoPermission(_RolesInformesPermission):
    """Suscripciones y solicitudes de cambio: + Director de Estrategia."""

    roles_permitidos = ROLES_INFORMES_CATALOGO


class InformesFinanzasPermission(_RolesInformesPermission):
    """Facturas y métodos de pago: + Director Financiero."""

    roles_permitidos = ROLES_INFORMES_FINANZAS
