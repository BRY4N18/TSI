"""T019 — pedir otra cuenta responde `403` **sin devolver filas** (SC-002, FR-010).

La sustitución silenciosa —devolverle su propia cuenta a quien pidió la ajena—
es lo que FR-010 prohíbe, y aquí el material es financiero: facturas, importes y
mora de otra organización. Un informe que dice ser de la cuenta 99 y trae la 7
no solo es incorrecto: es incorrecto **de una forma que nadie va a revisar**,
porque los datos son internamente coherentes.
"""

from __future__ import annotations

import json

import pytest

from apps.suscripciones.tests.conftest import CUENTA_A, CUENTA_B

RUTA = "/api/v1/informes/suscripciones-facturacion/suscripciones"


@pytest.mark.api
class TestPedirOtraCuenta:
    def test_responde_403(self, api_client, cliente_a_headers, dos_cuentas):
        respuesta = api_client.get(f"{RUTA}?cuenta={CUENTA_B}", **cliente_a_headers)

        assert respuesta.status_code == 403

    def test_no_devuelve_ninguna_fila(self, api_client, cliente_a_headers, dos_cuentas):
        respuesta = api_client.get(f"{RUTA}?cuenta={CUENTA_B}", **cliente_a_headers)

        assert "data" not in json.loads(respuesta.content)

    def test_no_devuelve_la_propia_disfrazada(
        self, api_client, cliente_a_headers, dos_cuentas
    ):
        respuesta = api_client.get(f"{RUTA}?cuenta={CUENTA_B}", **cliente_a_headers)

        assert respuesta.status_code == 403
        assert "Aseguradora Torres S.A." not in respuesta.content.decode(), (
            "devolvio la cuenta propia ante una peticion de la ajena"
        )

    def test_ni_la_ajena(self, api_client, cliente_a_headers, dos_cuentas):
        respuesta = api_client.get(f"{RUTA}?cuenta={CUENTA_B}", **cliente_a_headers)

        assert "Transportes Beltran Ltda." not in respuesta.content.decode()

    def test_el_error_es_forbidden_y_lo_explica(
        self, api_client, cliente_a_headers, dos_cuentas
    ):
        cuerpo = api_client.get(f"{RUTA}?cuenta={CUENTA_B}", **cliente_a_headers).json()

        assert cuerpo["error"] == "forbidden"
        assert cuerpo["code"] == "403"
        assert cuerpo["detail"]

    def test_en_el_sentido_contrario_tambien(
        self, api_client, cliente_b_headers, dos_cuentas
    ):
        respuesta = api_client.get(f"{RUTA}?cuenta={CUENTA_A}", **cliente_b_headers)

        assert respuesta.status_code == 403


@pytest.mark.api
class TestPedirLaPropia:
    def test_es_valido(self, api_client, cliente_a_headers, dos_cuentas):
        respuesta = api_client.get(f"{RUTA}?cuenta={CUENTA_A}", **cliente_a_headers)

        assert respuesta.status_code == 200
        assert {f["cuenta"] for f in respuesta.json()["data"]} == {
            "Aseguradora Torres S.A."
        }

    def test_sigue_declarandose_acotado(
        self, api_client, cliente_a_headers, dos_cuentas
    ):
        cuerpo = api_client.get(f"{RUTA}?cuenta={CUENTA_A}", **cliente_a_headers).json()

        assert cuerpo["meta"]["acotado_a"] == "propios"


@pytest.mark.api
class TestUnaCuentaInexistente:
    def test_el_rol_amplio_obtiene_lista_vacia_no_error(
        self, api_client, admin_auth_headers, dos_cuentas
    ):
        respuesta = api_client.get(f"{RUTA}?cuenta=999999", **admin_auth_headers)

        assert respuesta.status_code == 200
        assert respuesta.json()["data"] == []

    def test_el_cliente_recibe_403_igualmente(
        self, api_client, cliente_a_headers, dos_cuentas
    ):
        # No es la suya, exista o no: la negativa no depende de que exista.
        respuesta = api_client.get(f"{RUTA}?cuenta=999999", **cliente_a_headers)

        assert respuesta.status_code == 403
