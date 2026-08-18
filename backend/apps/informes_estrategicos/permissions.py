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
    AUTORIDAD_OE1,
    AUTORIDAD_OE1_CICLO,
    AUTORIDAD_OE1_ESTRATEGIA,
    AUTORIDAD_OE1_FINANZAS,
    AUTORIDAD_OE1_MARKETING,
    AUTORIDAD_OE5,
    AUTORIDAD_OE5_ESTRATEGIA,
    AUTORIDAD_OE5_FINANZAS,
    AUTORIDAD_OE5_RIESGO,
    AUTORIDAD_OE5_SOPORTE,
    AUTORIDAD_OE2,
    AUTORIDAD_OE2_CONSUMO,
    AUTORIDAD_OE2_DINERO,
    AUTORIDAD_OE3,
    AUTORIDAD_OE3_CAPACIDAD,
    AUTORIDAD_OE3_DESPACHO,
    AUTORIDAD_OE4,
    AUTORIDAD_OE4_EXPEDIENTE,
    AUTORIDAD_OE4_INTELIGENCIA,
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


AUTORIDAD_POR_INFORME_OE4 = {
    "indice-calidad-historico": AUTORIDAD_OE4_EXPEDIENTE,
    "completitud-campos-criticos": AUTORIDAD_OE4_EXPEDIENTE,
    "campos-mas-ausentes": AUTORIDAD_OE4_EXPEDIENTE,
    "calidad-por-origen": AUTORIDAD_OE4_EXPEDIENTE,
    "impacto-humano-por-zona": AUTORIDAD_OE4_EXPEDIENTE,
    "impacto-vial-por-zona": AUTORIDAD_OE4_EXPEDIENTE,
    "concentracion-siniestralidad": AUTORIDAD_OE4_INTELIGENCIA,
    "patron-horario-climatico": AUTORIDAD_OE4_INTELIGENCIA,
    "cobertura-del-historico": AUTORIDAD_OE4_INTELIGENCIA,
}


AUTORIDAD_POR_INFORME_OE2 = {
    "integraciones-activas": AUTORIDAD_OE2_CONSUMO,
    "consumo-por-partner": AUTORIDAD_OE2_CONSUMO,
    "latencia-por-endpoint": AUTORIDAD_OE2_CONSUMO,
    "taxonomia-errores": AUTORIDAD_OE2_CONSUMO,
    "adopcion-versiones": AUTORIDAD_OE2_CONSUMO,
    "comparativa-partners": AUTORIDAD_OE2_CONSUMO,
    "crecimiento-ecosistema": AUTORIDAD_OE2_CONSUMO,
    "excedente-facturable": AUTORIDAD_OE2_DINERO,
    "participacion-ingresos-api": AUTORIDAD_OE2_DINERO,
    "mrr-por-linea": AUTORIDAD_OE2_DINERO,
}


AUTORIDAD_POR_INFORME_OE1 = {
    "mrr-mensual": AUTORIDAD_OE1_FINANZAS,
    "arr-proyeccion": AUTORIDAD_OE1_FINANZAS,
    "tasa-renovacion": AUTORIDAD_OE1_FINANZAS,
    "mrr-por-segmento": AUTORIDAD_OE1_FINANZAS | AUTORIDAD_OE1_ESTRATEGIA,
    "cartera-por-plan": AUTORIDAD_OE1_ESTRATEGIA,
    "embudo-conversion": AUTORIDAD_OE1_MARKETING,
    "velocidad-ciclo-venta": AUTORIDAD_OE1_MARKETING,
    "tiempo-onboarding": AUTORIDAD_OE1_CICLO,
    "abandono-onboarding": AUTORIDAD_OE1_CICLO,
    "churn-por-cohorte": AUTORIDAD_OE1_CICLO,
}


AUTORIDAD_POR_INFORME_OE5 = {
    "cumplimiento-sla": AUTORIDAD_OE5_SOPORTE,
    "evolucion-incumplimiento": AUTORIDAD_OE5_SOPORTE,
    "rendimiento-por-agente": AUTORIDAD_OE5_SOPORTE,
    "reincidencia-soporte": AUTORIDAD_OE5_SOPORTE,
    "sla-por-plan": AUTORIDAD_OE5_SOPORTE | AUTORIDAD_OE5_ESTRATEGIA,
    "retencion-neta-ingresos": AUTORIDAD_OE5_FINANZAS,
    "movimientos-de-plan": AUTORIDAD_OE5_ESTRATEGIA | AUTORIDAD_OE5_FINANZAS,
    "antiguedad-de-cuenta": AUTORIDAD_OE5_ESTRATEGIA,
    "cuentas-en-riesgo": AUTORIDAD_OE5_RIESGO,
}


class Oe5Permission(BasePermission):
    """OE5: soporte / finanzas / estrategia / riesgo. Un partner no entra."""

    def has_permission(self, request, view) -> bool:
        user = request.user
        if not user or not getattr(user, "is_authenticated", False):
            return False
        roles = set(getattr(user, "roles", []))
        informe = getattr(view, "kwargs", {}).get("informe")
        permitidos = AUTORIDAD_POR_INFORME_OE5.get(informe)
        if permitidos is None:
            return bool(roles & AUTORIDAD_OE5)
        return bool(roles & permitidos)


class Oe1Permission(BasePermission):
    """OE1: finanzas / estrategia / marketing / ciclo. Un partner no entra (FR-OE1)."""

    def has_permission(self, request, view) -> bool:
        user = request.user
        if not user or not getattr(user, "is_authenticated", False):
            return False
        roles = set(getattr(user, "roles", []))
        informe = getattr(view, "kwargs", {}).get("informe")
        permitidos = AUTORIDAD_POR_INFORME_OE1.get(informe)
        if permitidos is None:
            return bool(roles & AUTORIDAD_OE1)
        return bool(roles & permitidos)


class Oe2Permission(BasePermission):
    """OE2: consumo vs dinero. Un partner no entra en ninguna (FR-OE2-007)."""

    def has_permission(self, request, view) -> bool:
        user = request.user
        if not user or not getattr(user, "is_authenticated", False):
            return False
        roles = set(getattr(user, "roles", []))
        informe = getattr(view, "kwargs", {}).get("informe")
        permitidos = AUTORIDAD_POR_INFORME_OE2.get(informe)
        if permitidos is None:
            return bool(roles & AUTORIDAD_OE2)
        return bool(roles & permitidos)


class Oe4Permission(BasePermission):
    """OE4: expediente vs inteligencia vendible (FR-OE4 permisos)."""

    def has_permission(self, request, view) -> bool:
        user = request.user
        if not user or not getattr(user, "is_authenticated", False):
            return False
        roles = set(getattr(user, "roles", []))
        informe = getattr(view, "kwargs", {}).get("informe")
        permitidos = AUTORIDAD_POR_INFORME_OE4.get(informe)
        if permitidos is None:
            return bool(roles & AUTORIDAD_OE4)
        return bool(roles & permitidos)
