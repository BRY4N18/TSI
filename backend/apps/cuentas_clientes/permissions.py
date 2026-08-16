"""Permisos de los ocho listados tacticos de Cuentas y Clientes (FR-018, FR-019).

Sigue el patron de `apps/informes_tacticos/permissions.py` —una clase por
conjunto de roles, que falla cerrado— pero **no reutiliza sus clases**: aquellas
conceden a Operador, y aqui el Operador no accede a ninguno de los ocho.

El reparto, y por que es asimetrico
-----------------------------------
`specs/002-tactico/acceso-tactico.md` §5 clasifica los ocho endpoints de este
departamento, y arroja un hallazgo que conviene no "corregir":

**Cuentas y Clientes no tiene autoridad de negocio.** La unica que el §5.1 del
SRS le asigna es el **Director Tecnologico, limitado a la capa de accesos
tecnicos** (L8). Los otros siete listados no tienen jefatura por encima del
Administrador, que es a la vez su responsable operativo y su unica vision de
conjunto.

No es un olvido de la asignacion: es lo que dice el SRS, y esta anotado en
`decisiones-pendientes.md`. Por eso hay **dos** clases y no una: dar al Director
Tecnologico los ocho seria mas simetrico y contradiria el §5.1.
"""

from __future__ import annotations

from rest_framework.permissions import BasePermission

from core.auth.roles_tacticos import AUTORIDAD_CUENTAS_ACCESOS_TECNICOS

ROLE_ADMIN = "Administrador"

#: Los siete listados sin autoridad departamental por encima del Administrador.
INFORMES_CUENTAS_ROLES = frozenset({ROLE_ADMIN})

#: L8 — accesos tecnicos. Suma la unica autoridad que el §5.1 reconoce aqui.
INFORMES_ACCESOS_TECNICOS_ROLES = frozenset(
    INFORMES_CUENTAS_ROLES | AUTORIDAD_CUENTAS_ACCESOS_TECNICOS
)


class _RolesPermission(BasePermission):
    """Base que falla cerrado: sin usuario, sin autenticar o sin rol, no pasa.

    El orden de las comprobaciones importa. Si se leyeran los roles antes de
    verificar la autenticacion, un objeto anonimo con un atributo `roles`
    inesperado podria conceder; asi la unica via de entrada es tener el rol.
    """

    roles_permitidos: frozenset[str] = frozenset()

    def has_permission(self, request, view) -> bool:
        user = getattr(request, "user", None)
        if not user or not getattr(user, "is_authenticated", False):
            return False
        return bool(set(getattr(user, "roles", []) or []) & self.roles_permitidos)


class InformesCuentasLecturaPermission(_RolesPermission):
    """Lectura de los siete listados de cuentas, usuarios y sesiones: Administrador."""

    roles_permitidos = INFORMES_CUENTAS_ROLES


class InformesAccesosTecnicosPermission(_RolesPermission):
    """Lectura de L8 — accesos tecnicos: Director Tecnologico y Administrador.

    El Director Tecnologico accede **solo a este**. Ampliarlo a los otros siete
    contradiria el §5.1 del SRS (`acceso-tactico.md` §5, nota ⚠️).
    """

    roles_permitidos = INFORMES_ACCESOS_TECNICOS_ROLES
