"""T024 — control de acceso de los cuatro listados (FR-019, SC-006).

Dos garantías distintas:

* **El Operador recibe 403 en los cuatro, sin que se filtre ninguna fila.** Un
  `403` que además devolviera datos sería peor que no tener permiso alguno, y es
  un fallo posible si la comprobación ocurre después de consultar.
* **El Director Tecnológico recibe 200 solo en `accesos-tecnicos`.** Ampliarlo a
  los otros tres contradiría el §5.1 del SRS (`acceso-tactico.md` §5).
"""

from __future__ import annotations

import json

import pytest

BASE = "/api/v1/informes/cuentas-clientes"

ENDPOINTS = [
    "usuarios-por-rol",
    "sesiones-activas",
    "credenciales-temporales",
    "accesos-tecnicos",
]


@pytest.mark.api
class TestSinPermiso:
    @pytest.mark.parametrize("informe", ENDPOINTS)
    def test_operador_recibe_403(self, api_client, operator_auth_headers, informe):
        respuesta = api_client.get(f"{BASE}/{informe}", **operator_auth_headers)

        assert respuesta.status_code == 403

    @pytest.mark.parametrize("informe", ENDPOINTS)
    def test_el_403_no_filtra_ninguna_fila(
        self, api_client, operator_auth_headers, informe
    ):
        respuesta = api_client.get(f"{BASE}/{informe}", **operator_auth_headers)

        assert "data" not in json.loads(respuesta.content)

    @pytest.mark.parametrize("informe", ENDPOINTS)
    def test_sin_token_es_401(self, api_client, mock_pinot, informe):
        # 401 y no 403: la diferencia importa para el consumidor, que en un caso
        # debe autenticarse y en el otro no tiene nada que hacer.
        respuesta = api_client.get(f"{BASE}/{informe}")

        assert respuesta.status_code == 401

    @pytest.mark.parametrize("informe", ENDPOINTS)
    def test_cliente_recibe_403(self, api_client, cliente_auth_headers, informe):
        respuesta = api_client.get(f"{BASE}/{informe}", **cliente_auth_headers)

        assert respuesta.status_code == 403


@pytest.mark.api
class TestAdministrador:
    @pytest.mark.parametrize("informe", ENDPOINTS)
    def test_accede_a_los_cuatro(self, api_client, admin_auth_headers, informe):
        respuesta = api_client.get(f"{BASE}/{informe}", **admin_auth_headers)

        assert respuesta.status_code == 200


@pytest.mark.api
class TestDirectorTecnologico:
    """§5.1 del SRS: su autoridad alcanza **solo** a la capa de accesos técnicos."""

    def test_accede_a_accesos_tecnicos(
        self, api_client, director_tecnologico_auth_headers
    ):
        respuesta = api_client.get(
            f"{BASE}/accesos-tecnicos", **director_tecnologico_auth_headers
        )

        assert respuesta.status_code == 200

    @pytest.mark.parametrize(
        "informe", ["usuarios-por-rol", "sesiones-activas", "credenciales-temporales"]
    )
    def test_no_accede_a_los_otros_tres(
        self, api_client, director_tecnologico_auth_headers, informe
    ):
        respuesta = api_client.get(f"{BASE}/{informe}", **director_tecnologico_auth_headers)

        assert respuesta.status_code == 403, (
            "ampliar al Director Tecnologico mas alla de accesos tecnicos "
            "contradice el §5.1 del SRS"
        )
