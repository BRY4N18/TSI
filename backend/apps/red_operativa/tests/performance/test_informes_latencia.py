"""T044 — primera página de los cuatro listados bajo el umbral, **con volumen** (SC-006).

⚠️ **Con al menos 100 unidades**, y eso es el punto de la prueba.

La resolución geográfica por lotes solo se distingue de una consulta por fila
cuando hay suficientes filas: con diez unidades las dos implementaciones parecen
igual de rápidas, y la prueba pasaría sin detectar nada.
"""

from __future__ import annotations

import time

import pytest

from apps.red_operativa.tests.conftest import PROVEEDOR_A, _unidad

BASE = "/api/v1/informes/red-operativa"

LISTADOS = ["flota", "bajas-unidad", "regiones", "validaciones-region"]

UMBRAL_MS = 300


@pytest.fixture
def flota_de_cien(mock_pinot, geografia_y_proveedores):
    """Cien unidades: el volumen mínimo en que el defecto se nota."""
    from conftest import PINOT_STORE

    for i in range(100):
        PINOT_STORE["Dim_UnidadEmergencia"].append(
            _unidad(5400 + i, placa=f"PERF-{i:03d}", idcliente=PROVEEDOR_A)
        )


@pytest.fixture
def sembrado(flota_de_cien, bajas_sembradas, validaciones_sembradas):
    return True


@pytest.mark.slow
@pytest.mark.api
@pytest.mark.parametrize("informe", LISTADOS)
def test_primera_pagina_bajo_el_umbral(
    api_client, admin_auth_headers, informe, sembrado
):
    muestras: list[float] = []

    for _ in range(20):
        inicio = time.perf_counter()
        respuesta = api_client.get(f"{BASE}/{informe}", **admin_auth_headers)
        muestras.append((time.perf_counter() - inicio) * 1000)
        assert respuesta.status_code == 200

    muestras.sort()
    p95 = muestras[int(len(muestras) * 0.95) - 1]

    assert p95 <= UMBRAL_MS, f"'{informe}' tarda {p95:.1f} ms en la primera pagina"


@pytest.mark.slow
@pytest.mark.api
class TestLaFlotaGrandeNoDisparaElCoste:
    @staticmethod
    def _consultas(api_client, headers, url) -> int:
        from unittest.mock import patch

        from conftest import _pinot_query_impl

        contador = {"n": 0}

        def contando(self, sql, params=None):
            contador["n"] += 1
            return _pinot_query_impl(sql, params)

        with patch("core.pinot.client.PinotClient.query", contando):
            api_client.get(url, **headers)
        return contador["n"]

    def test_una_pagina_de_100_cuesta_lo_mismo_que_una_de_5(
        self, api_client, admin_auth_headers, flota_de_cien
    ):
        """La garantía de research D3, medida de punta a punta."""
        pocas = self._consultas(
            api_client, admin_auth_headers, f"{BASE}/flota?limit=5"
        )
        muchas = self._consultas(
            api_client, admin_auth_headers, f"{BASE}/flota?limit=100"
        )

        assert muchas == pocas, (
            f"100 filas cuestan {muchas} consultas y 5 cuestan {pocas}: "
            "la geografia se esta resolviendo fila a fila"
        )

    def test_una_pagina_de_100_sigue_bajo_el_umbral(
        self, api_client, admin_auth_headers, flota_de_cien
    ):
        inicio = time.perf_counter()
        respuesta = api_client.get(f"{BASE}/flota?limit=100", **admin_auth_headers)
        transcurrido = (time.perf_counter() - inicio) * 1000

        assert respuesta.status_code == 200
        assert len(respuesta.json()["data"]) == 100
        assert transcurrido <= UMBRAL_MS * 2

    @pytest.mark.parametrize("informe", LISTADOS)
    def test_ninguno_pasa_de_un_punado_de_consultas(
        self, api_client, admin_auth_headers, informe, sembrado
    ):
        consultas = self._consultas(
            api_client, admin_auth_headers, f"{BASE}/{informe}?limit=100"
        )

        assert consultas <= 8, f"'{informe}' hace {consultas} consultas por peticion"
