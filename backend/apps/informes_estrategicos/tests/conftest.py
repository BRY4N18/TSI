"""Ayudantes compartidos de las pruebas de OE6."""

from __future__ import annotations

import pytest
from rest_framework.test import APIClient

from core.jwt_utils import create_access_token

BASE = "/api/v1/informes-estrategicos/oe6"

PERIODO = {
    "desde": "2026-01-01",
    "hasta": "2026-12-31",
    "granularidad": "mes",
}

INFORMES = (
    "tiempo-respuesta-global",
    "tiempo-respuesta-por-severidad",
    "tramos-del-ciclo",
    "origen-de-asignacion",
    "rechazo-y-timeout-por-unidad",
    "abortos-y-misiones-fallidas",
    "desviacion-de-llegada",
    "impacto-humano",
    "cierres-forzados",
    "envejecimiento-de-casos-abiertos",
    "escaladas-de-severidad",
    "cobertura-de-evidencia",
)

SENSIBLES = (
    "latitud", "longitud", "idusuario", "nombres", "apellidos",
    "identificacion", "gmail", "observaciones",
)


@pytest.fixture(autouse=True)
def _jwt_con_sesion(mock_pinot):
    """El JWT valida Fact_Session en Pinot; sin el mock la sesión 1 no existe."""
    return mock_pinot


def cliente(roles):
    api = APIClient()
    api.credentials(
        HTTP_AUTHORIZATION=f"Bearer {create_access_token(user_id=1, roles=roles, session_id=1)}"
    )
    return api


def pedir(api, informe, **extra):
    params = {**PERIODO, **extra}
    return api.get(f"{BASE}/{informe}", params)


BASE_OE3 = "/api/v1/informes-estrategicos/oe3"

INFORMES_OE3 = (
    "latencia-asignacion",
    "evolucion-latencia",
    "tasa-error-registro",
    "primer-intento",
    "ratio-demanda-capacidad",
    "cobertura-de-respaldo",
    "perdida-de-senal",
)

BLOQUEADOS_OE3 = (
    "uptime-por-region",
    "tiempo-puesta-operacion",
    "curva-maduracion",
    "cohorte-region",
    "margen-operativo",
    "reasignacion-manual",
    "cobertura-pruebas",
)


def pedir_oe3(api, informe, **extra):
    params = {**PERIODO, **extra}
    return api.get(f"{BASE_OE3}/{informe}", params)


BASE_OE4 = "/api/v1/informes-estrategicos/oe4"

INFORMES_OE4 = (
    "indice-calidad-historico",
    "completitud-campos-criticos",
    "campos-mas-ausentes",
    "calidad-por-origen",
    "concentracion-siniestralidad",
    "patron-horario-climatico",
    "impacto-humano-por-zona",
    "impacto-vial-por-zona",
    "cobertura-del-historico",
)

BLOQUEADOS_OE4 = (
    "precision-del-modelo",
    "contraste-prediccion-ocurrencia",
    "unidades-preposicionadas",
    "versiones-del-modelo",
    "productos-de-inteligencia",
    "latencia-de-ingesta",
)


def pedir_oe4(api, informe, **extra):
    params = {**PERIODO, **extra}
    return api.get(f"{BASE_OE4}/{informe}", params)


BASE_OE2 = "/api/v1/informes-estrategicos/oe2"

INFORMES_OE2 = (
    "integraciones-activas",
    "consumo-por-partner",
    "latencia-por-endpoint",
    "taxonomia-errores",
    "excedente-facturable",
    "participacion-ingresos-api",
    "mrr-por-linea",
    "adopcion-versiones",
    "comparativa-partners",
    "crecimiento-ecosistema",
)

DINERO_OE2 = (
    "excedente-facturable",
    "participacion-ingresos-api",
    "mrr-por-linea",
)

BLOQUEADOS_OE2 = ("disponibilidad-api",)


def pedir_oe2(api, informe, **extra):
    params = {**PERIODO, **extra}
    return api.get(f"{BASE_OE2}/{informe}", params)


BASE_OE1 = "/api/v1/informes-estrategicos/oe1"

INFORMES_OE1 = (
    "mrr-mensual",
    "arr-proyeccion",
    "mrr-por-segmento",
    "cartera-por-plan",
    "embudo-conversion",
    "velocidad-ciclo-venta",
    "tasa-renovacion",
    "tiempo-onboarding",
    "abandono-onboarding",
    "churn-por-cohorte",
)

FINANZAS_OE1 = ("mrr-mensual", "arr-proyeccion", "tasa-renovacion")
CICLO_OE1 = ("tiempo-onboarding", "abandono-onboarding", "churn-por-cohorte")
BLOQUEADOS_OE1 = ("cac-por-canal", "mercados-activos", "cartera-mrr-por-mercado")


def pedir_oe1(api, informe, **extra):
    params = {**PERIODO, **extra}
    return api.get(f"{BASE_OE1}/{informe}", params)


BASE_OE5 = "/api/v1/informes-estrategicos/oe5"

INFORMES_OE5 = (
    "cumplimiento-sla",
    "evolucion-incumplimiento",
    "sla-por-plan",
    "retencion-neta-ingresos",
    "movimientos-de-plan",
    "rendimiento-por-agente",
    "reincidencia-soporte",
    "cuentas-en-riesgo",
    "antiguedad-de-cuenta",
)

SOPORTE_OE5 = (
    "cumplimiento-sla",
    "evolucion-incumplimiento",
    "rendimiento-por-agente",
    "reincidencia-soporte",
)
BLOQUEADOS_OE5 = (
    "nps-satisfaccion",
    "reportes-sin-correccion",
    "tasa-renovacion",
    "churn-por-cohorte",
    "tiempo-onboarding",
    "abandono-onboarding",
)


def pedir_oe5(api, informe, **extra):
    params = {**PERIODO, **extra}
    return api.get(f"{BASE_OE5}/{informe}", params)
