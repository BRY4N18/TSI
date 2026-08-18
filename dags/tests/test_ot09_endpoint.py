"""T035 — el endpoint se agrupa sin cadena de consulta."""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from lib.hechos.hecho_llamada_api import construir, normalizar_path  # noqa: E402
from tests.almacen import (  # noqa: E402
    ID_LOG_PRUEBA,
    asegurar_hechos_partners,
    ejecutar_partners,
    insertar,
    llamada_de_prueba,
    limpiar_partners,
    requiere_modelo,
)


def test_normalizar_quita_la_query():
    assert normalizar_path("/api/v1/datos/accidentes?idseveridad=4") == (
        "/api/v1/datos/accidentes"
    )


@pytest.fixture
def escenario():
    asegurar_hechos_partners()
    limpiar_partners()
    insertar("hecho_llamada_api", [
        llamada_de_prueba(ID_LOG_PRUEBA, endpoint_path="/api/v1/datos/accidentes"),
        llamada_de_prueba(
            ID_LOG_PRUEBA + 1, endpoint_path="/api/v1/datos/accidentes"
        ),
    ])
    yield
    limpiar_partners()


@requiere_modelo
def test_dos_llamadas_al_mismo_path_son_un_endpoint(escenario):
    filas = ejecutar_partners("ot09_consumo_por_endpoint")
    assert len(filas) == 1
    assert int(filas[0]["llamadas"]) == 2


def test_construir_colapsa_parametros():
    ahora = datetime(2026, 8, 17, 12, 0, 0)
    filas = construir(
        {
            "llamadas": [
                {
                    "idlogllamadaapi": 1, "idpartner": 1,
                    "endpoint": "/api/v1/datos/accidentes?a=1",
                    "metodohttp": "GET", "codigohttp": 200, "latenciams": 10,
                    "fechallamada": "2026-08-17 10:00:00",
                },
                {
                    "idlogllamadaapi": 2, "idpartner": 1,
                    "endpoint": "/api/v1/datos/accidentes?b=2",
                    "metodohttp": "GET", "codigohttp": 200, "latenciams": 10,
                    "fechallamada": "2026-08-17 10:01:00",
                },
            ],
            "partners": [],
            "credenciales": [],
        },
        ahora,
    )
    assert {f["endpoint_path"] for f in filas} == {"/api/v1/datos/accidentes"}
