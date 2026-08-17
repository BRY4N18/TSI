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
