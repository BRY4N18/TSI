"""Quién entra a los informes estratégicos de OE6.

Entran `DirectorOperaciones` (autoridad de Emergencias) y `Gerente`. Cualquier
otro rol recibe `403`, **incluidos** `Operador`, `Despacho` y `Unidad`: la
versión de empresa de su operación no es una ampliación de su pantalla.

Un `200` con `data: []` diría «no hay datos» donde el sistema quiso decir «no
tienes acceso», y son cosas distintas.

⚠️ La autoridad **no** levanta la exclusión constitucional. Coordenadas,
identidad de personas y texto libre siguen fuera para todos los cargos. Esta
clase decide quién entra, nunca qué se le muestra de más.
"""

from rest_framework.permissions import BasePermission

from core.auth.roles_tacticos import (
    AUTORIDAD_ESTRATEGICA_OE6,
    AUTORIDAD_OE3,
    AUTORIDAD_OE3_CAPACIDAD,
    AUTORIDAD_OE3_DESPACHO,
)


class Oe6Permission(BasePermission):
    """Acceso a los doce informes de OE6 (FR-OE6-013, FR-OE6-014)."""

    def has_permission(self, request, view) -> bool:
        user = request.user
        if not user or not getattr(user, "is_authenticated", False):
            return False
        roles = set(getattr(user, "roles", []))
        return bool(roles & AUTORIDAD_ESTRATEGICA_OE6)


#: Permiso **por informe**, no por módulo. Un permiso de módulo concedería
#: de más a `DirectorExpansion` en los de despacho, justo donde el SRS
#: advierte que la autoridad no es una cadena de mando única.
AUTORIDAD_POR_INFORME_OE3 = {
    "latencia-asignacion": AUTORIDAD_OE3_DESPACHO,
    "evolucion-latencia": AUTORIDAD_OE3_DESPACHO,
    "tasa-error-registro": AUTORIDAD_OE3_DESPACHO,
    "primer-intento": AUTORIDAD_OE3_DESPACHO,
    "ratio-demanda-capacidad": AUTORIDAD_OE3_CAPACIDAD,
    "cobertura-de-respaldo": AUTORIDAD_OE3_CAPACIDAD,
    "perdida-de-senal": AUTORIDAD_OE3_CAPACIDAD,
}


class Oe3Permission(BasePermission):
    """Acceso a OE3: la autoridad está repartida por materia (FR-OE3)."""

    def has_permission(self, request, view) -> bool:
        user = request.user
        if not user or not getattr(user, "is_authenticated", False):
            return False
        roles = set(getattr(user, "roles", []))
        informe = getattr(view, "kwargs", {}).get("informe")
        permitidos = AUTORIDAD_POR_INFORME_OE3.get(informe)
        if permitidos is None:
            # Bloqueado o desconocido: la vista responde 404. Un 403 aquí
            # confundiría «no existe» con «no puedes verlo».
            return bool(roles & AUTORIDAD_OE3)
        return bool(roles & permitidos)
