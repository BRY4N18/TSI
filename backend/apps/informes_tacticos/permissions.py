"""DRF permissions for informes_tacticos module.

FR-007 de la spec pedía roles "Operador y Supervisor" — el rol "Supervisor" no
existe en el sistema (ver `.specify/docs/actors.md`). Se usan los roles reales:
Operador (uso operativo diario) y Administrador (función de supervisión dentro
del alcance operativo actual), igual que `apps.accidentes.permissions`.
"""

from rest_framework.permissions import BasePermission

ROLE_OPERADOR = "Operador"
ROLE_ADMIN = "Administrador"

INFORMES_TACTICOS_ROLES = frozenset({ROLE_OPERADOR, ROLE_ADMIN})


class InformesTacticosLecturaPermission(BasePermission):
    """Read access to informes tácticos simples: Operador or Administrador."""

    def has_permission(self, request, view) -> bool:
        user = request.user
        if not user or not getattr(user, "is_authenticated", False):
            return False
        roles = set(getattr(user, "roles", []))
        return bool(roles & INFORMES_TACTICOS_ROLES)


class InformesTacticosCompuestosPermission(BasePermission):
    """Read access to informes tácticos compuestos: solo Administrador (FR-009).

    A diferencia de los 16 informes simples (Operador + Administrador), los 3
    informes compuestos son indicadores de gestión — la spec pedía "Supervisor,
    no Operador raso"; con los roles reales disponibles, `Administrador` es la
    interpretación más fiel de esa restricción (research.md §5).
    """

    def has_permission(self, request, view) -> bool:
        user = request.user
        if not user or not getattr(user, "is_authenticated", False):
            return False
        return ROLE_ADMIN in getattr(user, "roles", [])
