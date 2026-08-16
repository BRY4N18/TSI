"""T043 — primera página de los cuatro listados por debajo del umbral (SC-006).

Sobre el doble en memoria: mide que la capa de informes no introduzca coste
propio, no mide Pinot. El objetivo de 2 s se verifica contra el stack real.

Lo que sí detecta es el coste que crece con las filas por resolver catálogos una
consulta por fila. Aquí hay un coste extra respecto a los otros departamentos —
**la resolución de la cuenta del solicitante**, que ocurre en cada petición de un
rol acotado— y conviene que sea una sola consulta, no una por fila.
"""

from __future__ import annotations

import time

import pytest

BASE = "/api/v1/informes/suscripciones-facturacion"

LISTADOS = ["suscripciones", "facturas", "metodos-pago", "solicitudes-cambio-plan"]

UMBRAL_MS = 300


@pytest.mark.slow
@pytest.mark.api
@pytest.mark.parametrize("informe", LISTADOS)
def test_primera_pagina_bajo_el_umbral(
    api_client, admin_auth_headers, informe, todo_sembrado
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
class TestElCosteNoCreceConLasFilas:
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

    @pytest.fixture
    def muchas_facturas(self, mock_pinot, dos_cuentas):
        """Cuarenta facturas de la misma cuenta, todas del mismo tipo.

        Así la única variable entre las dos medidas es **el número de filas**,
        que es justo lo que no debe influir.
        """
        from conftest import PINOT_STORE
        from apps.suscripciones.tests.conftest import AHORA_MS, CUENTA_A, DIA_MS

        for i in range(40):
            PINOT_STORE["Fact_Factura"].append(
                {
                    "id_factura": f"FAC-PERF-{i:08d}", "id_cliente": CUENTA_A,
                    "id_suscripcion": 7001, "idmetodopago": 7601,
                    "numero_factura": f"P{i:03d}", "periodo": "2026-05",
                    "estado_pago": "Pagada", "tipo": "cargo", "es_nota_credito": False,
                    "id_factura_original": None, "motivo_anulacion": None,
                    "activo": True, "reintentos": 0, "monto_base": 10.0,
                    "impuestos": 1.0, "monto_total": 11.0,
                    "fecha_emision": AHORA_MS - (100 + i) * DIA_MS,
                    "fecha_vencimiento": AHORA_MS - (85 + i) * DIA_MS,
                    "fecha_actualizacion": AHORA_MS,
                }
            )

    def test_el_numero_de_consultas_no_depende_del_numero_de_filas(
        self, api_client, admin_auth_headers, muchas_facturas
    ):
        pocas = self._consultas(
            api_client, admin_auth_headers, f"{BASE}/facturas?limit=4"
        )
        muchas = self._consultas(
            api_client, admin_auth_headers, f"{BASE}/facturas?limit=40"
        )

        assert muchas == pocas, (
            f"40 filas cuestan {muchas} consultas y 4 cuestan {pocas}: "
            "el catalogo se esta resolviendo fila a fila"
        )

    @pytest.mark.parametrize("informe", LISTADOS)
    def test_ninguna_pagina_grande_dispara_el_coste(
        self, api_client, admin_auth_headers, informe, todo_sembrado
    ):
        """Cota superior floja, incluidas las consultas de autenticación."""
        consultas = self._consultas(
            api_client, admin_auth_headers, f"{BASE}/{informe}?limit=50"
        )

        assert consultas <= 7, f"'{informe}' hace {consultas} consultas por peticion"

    @pytest.mark.parametrize("informe", LISTADOS)
    def test_la_cuenta_del_solicitante_se_resuelve_una_sola_vez(
        self, api_client, cliente_a_headers, informe, todo_sembrado
    ):
        """El coste extra propio de este departamento.

        Un rol acotado necesita resolver a qué cuenta pertenece. Esa resolución
        es **una consulta por petición**, no una por fila — si creciera, el
        acotamiento se volvería el cuello de botella del listado.
        """
        una = self._consultas(
            api_client, cliente_a_headers, f"{BASE}/{informe}?limit=1"
        )
        muchas = self._consultas(
            api_client, cliente_a_headers, f"{BASE}/{informe}?limit=50"
        )

        assert muchas <= una + 1, (
            f"'{informe}': {una} consultas con 1 fila y {muchas} con 50"
        )
