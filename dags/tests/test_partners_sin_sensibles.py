"""T020 — sin IP, sin hash, sin contacto, sin ejecutor (SC-008)."""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from lib.dimensiones.dim_credencial_api import CONSULTA_CREDENCIALES  # noqa: E402
from lib.dimensiones.dim_partner import CONSULTA as CONSULTA_PARTNER  # noqa: E402
from lib.hechos.hecho_cambio_acceso import CONSULTA_BITACORA  # noqa: E402
from lib.hechos.hecho_llamada_api import CONSULTA_LLAMADAS, construir  # noqa: E402
from tests.almacen import requiere_modelo  # noqa: E402

from lib.clickhouse_http_client import query_clickhouse  # noqa: E402

TABLAS = (
    "dim_partner",
    "dim_credencial_api",
    "dim_version_contrato",
    "hecho_llamada_api",
    "hecho_cambio_acceso",
)
PROHIBIDAS = (
    "iporigen", "client_secret", "hash",
    "contacto_tecnico", "gmail", "ejecutado_por",
)


@requiere_modelo
class TestEsquemaPartners:
    @classmethod
    def setup_class(cls):
        from lib.ddl import ensure_modelo_analitico

        ensure_modelo_analitico()

    def test_hecho_llamada_sin_ip(self):
        columnas = {
            f["name"]
            for f in query_clickhouse(
                "SELECT name FROM system.columns "
                "WHERE database = currentDatabase() AND table = 'hecho_llamada_api'"
            )
        }
        assert "iporigen" not in columnas
        assert "latencia_ms" in columnas

    def test_dimensiones_sin_secreto_ni_contacto(self):
        tablas = ", ".join(f"'{t}'" for t in TABLAS)
        columnas = query_clickhouse(
            "SELECT table, name FROM system.columns "
            f"WHERE database = currentDatabase() AND table IN ({tablas})"
        )
        for c in columnas:
            bajo = c["name"].lower()
            for p in PROHIBIDAS:
                if p == "hash" and c["name"] == "hash":
                    raise AssertionError(f"{c['table']}.{c['name']}")
                if p != "hash" and p in bajo:
                    raise AssertionError(f"{c['table']}.{c['name']}")


def test_consultas_de_carga_no_piden_sensibles():
    texto = CONSULTA_LLAMADAS + CONSULTA_PARTNER + CONSULTA_CREDENCIALES + CONSULTA_BITACORA
    bajo = texto.lower()
    assert "iporigen" not in bajo
    assert "client_secret" not in bajo
    assert "contacto_tecnico" not in bajo
    assert "ejecutado_por" not in bajo


def test_construir_llamada_no_lleva_ip():
    ahora = datetime(2026, 8, 17, 12, 0, 0)
    filas = construir(
        {
            "llamadas": [{
                "idlogllamadaapi": 1,
                "idpartner": 7,
                "idcredencialapi": 1,
                "endpoint": "/api/v1/datos/accidentes?x=1",
                "metodohttp": "GET",
                "codigohttp": 200,
                "latenciams": 80,
                "fechallamada": "2026-08-17 10:00:00",
            }],
            "partners": [{"idpartner": 7, "nombre_partner": "Acme", "idcliente": 1, "plan_api": "pro"}],
            "credenciales": [{"idcredencial": 1, "entorno": "Producción"}],
        },
        ahora,
    )
    assert "iporigen" not in filas[0]
    assert filas[0]["endpoint_path"] == "/api/v1/datos/accidentes"
    assert filas[0]["version_contrato"] == "v1"
    assert filas[0]["version_es_derivada"] == 1
