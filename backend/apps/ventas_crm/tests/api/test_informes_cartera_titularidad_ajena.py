"""T020 — pedir la cartera ajena responde `403` **sin devolver filas** (SC-002).

La alternativa tentadora es la sustitución silenciosa: si un gerente pide la
cartera de otro, devolverle la suya con `200`. Es lo que FR-008 prohíbe, y por
dos razones que se acumulan:

1. **Le oculta al solicitante que pidió algo indebido.** No puede corregir lo que
   no sabe que hizo mal.
2. **Produce un informe que responde a una pregunta que nadie hizo.** Los datos
   son correctos y la respuesta es falsa: dicen ser la cartera de otro.

Un `403` es información. Una sustitución es una mentira plausible.
"""

from __future__ import annotations

import json

import pytest

from apps.ventas_crm.tests.conftest import GERENTE_A, GERENTE_B

RUTA = "/api/v1/informes/ventas-crm/prospectos"


@pytest.mark.api
class TestPedirLoAjeno:
    def test_responde_403(self, api_client, gerente_a_headers, dos_carteras):
        respuesta = api_client.get(f"{RUTA}?ejecutivo={GERENTE_B}", **gerente_a_headers)

        assert respuesta.status_code == 403

    def test_no_devuelve_ninguna_fila(self, api_client, gerente_a_headers, dos_carteras):
        respuesta = api_client.get(f"{RUTA}?ejecutivo={GERENTE_B}", **gerente_a_headers)

        assert "data" not in json.loads(respuesta.content)

    def test_no_devuelve_la_cartera_propia_disfrazada(
        self, api_client, gerente_a_headers, dos_carteras
    ):
        """El defecto exacto que FR-008 previene."""
        respuesta = api_client.get(f"{RUTA}?ejecutivo={GERENTE_B}", **gerente_a_headers)
        cuerpo = respuesta.content.decode()

        assert respuesta.status_code == 403
        for propia in ("Alfa Seguros", "Beta Logistica", "Gamma Municipal"):
            assert propia not in cuerpo, (
                "devolvio la cartera propia ante una peticion de la ajena"
            )

    def test_el_error_es_forbidden_y_lo_explica(
        self, api_client, gerente_a_headers, dos_carteras
    ):
        cuerpo = api_client.get(
            f"{RUTA}?ejecutivo={GERENTE_B}", **gerente_a_headers
        ).json()

        assert cuerpo["error"] == "forbidden"
        assert cuerpo["code"] == "403"
        assert cuerpo["detail"]

    def test_en_el_sentido_contrario_tambien(
        self, api_client, gerente_b_headers, dos_carteras
    ):
        respuesta = api_client.get(f"{RUTA}?ejecutivo={GERENTE_A}", **gerente_b_headers)

        assert respuesta.status_code == 403


@pytest.mark.api
class TestPedirseASiMismo:
    def test_es_valido_y_devuelve_lo_propio(
        self, api_client, gerente_a_headers, dos_carteras
    ):
        respuesta = api_client.get(f"{RUTA}?ejecutivo={GERENTE_A}", **gerente_a_headers)

        assert respuesta.status_code == 200
        assert {f["empresa"] for f in respuesta.json()["data"]} == {
            "Alfa Seguros",
            "Beta Logistica",
            "Gamma Municipal",
        }

    def test_sigue_declarandose_acotado(self, api_client, gerente_a_headers, dos_carteras):
        cuerpo = api_client.get(
            f"{RUTA}?ejecutivo={GERENTE_A}", **gerente_a_headers
        ).json()

        assert cuerpo["meta"]["acotado_a"] == "propios"


@pytest.mark.api
class TestUnEjecutivoInexistente:
    def test_el_rol_amplio_obtiene_lista_vacia_no_error(
        self, api_client, admin_auth_headers, dos_carteras
    ):
        # La consulta es válida y el resultado vacío: `200`, no `404`.
        respuesta = api_client.get(f"{RUTA}?ejecutivo=999999", **admin_auth_headers)

        assert respuesta.status_code == 200
        assert respuesta.json()["data"] == []

    def test_el_gerente_recibe_403_igualmente(
        self, api_client, gerente_a_headers, dos_carteras
    ):
        # No es suyo, exista o no: la negativa no depende de que el otro exista.
        respuesta = api_client.get(f"{RUTA}?ejecutivo=999999", **gerente_a_headers)

        assert respuesta.status_code == 403
