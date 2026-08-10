"""Contrato de `GET /api/v1/contrato-integracion` (CU-O50, RF-PON-011).

`id_servicio` es obligatorio a proposito: el contrato se versiona POR
SERVICIO, y un endpoint que devolviera «la version vigente» sin decir de que
servicio estaria mintiendo en cuanto existiera el segundo.
"""

from __future__ import annotations

import pytest

from conftest import PINOT_STORE

pytestmark = [pytest.mark.django_db, pytest.mark.api]

DESPACHO = 1
ACCIDENTES = 2
URL = "/api/v1/contrato-integracion"


def _servicio(id_servicio, nombre):
    PINOT_STORE["Dim_Servicio"].append(
        {
            "id_servicio": id_servicio,
            "nombre": nombre,
            "descripcion": "",
            "tipo": "api",
            "activo": True,
            "fecha_actualizacion": 1,
        }
    )


def _version(idversion, id_servicio, version, estado="vigente", fecha_publicacion=1):
    PINOT_STORE["Dim_VersionContratoAPI"].append(
        {
            "idversion": idversion,
            "id_servicio": id_servicio,
            "version": version,
            "estado": estado,
            "spec_url": "",
            "fecha_publicacion": fecha_publicacion,
            "fecha_retiro": 0,
            "activo": True,
            "fecha_actualizacion": 1,
        }
    )


@pytest.fixture
def catalogo(mock_pinot, mock_kafka):
    _servicio(DESPACHO, "API Despacho")
    _servicio(ACCIDENTES, "API Registro de accidentes")
    _version(1, DESPACHO, "v1", estado="soportada", fecha_publicacion=1)
    _version(2, DESPACHO, "v2", estado="vigente", fecha_publicacion=2)
    _version(3, ACCIDENTES, "v1", estado="vigente", fecha_publicacion=1)


class TestConsultaContrato:
    def test_get_when_servicio_valido_returns_200_con_la_vigente(
        self, api_client, catalogo, partner_auth_headers
    ):
        # Act
        response = api_client.get(
            f"{URL}?id_servicio={DESPACHO}", **partner_auth_headers
        )

        # Assert
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["version"] == "v2"
        assert data["estado"] == "vigente"

    def test_get_devuelve_tambien_el_listado_del_servicio(
        self, api_client, catalogo, partner_auth_headers
    ):
        """El partner necesita saber que versiones siguen soportadas para
        planificar su migracion, no solo cual es la vigente."""
        # Act
        response = api_client.get(
            f"{URL}?id_servicio={DESPACHO}", **partner_auth_headers
        )

        # Assert
        versiones = response.json()["data"]["versiones"]
        assert {v["version"] for v in versiones} == {"v1", "v2"}

    def test_get_when_version_concreta_la_devuelve(
        self, api_client, catalogo, partner_auth_headers
    ):
        # Act
        response = api_client.get(
            f"{URL}?id_servicio={DESPACHO}&version=v1", **partner_auth_headers
        )

        # Assert
        assert response.status_code == 200
        assert response.json()["data"]["version"] == "v1"

    def test_get_no_mezcla_servicios(self, api_client, catalogo, partner_auth_headers):
        """Ambos servicios tienen una «v1»; no son la misma."""
        # Act
        response = api_client.get(
            f"{URL}?id_servicio={ACCIDENTES}", **partner_auth_headers
        )

        # Assert
        data = response.json()["data"]
        assert data["version"] == "v1"
        assert len(data["versiones"]) == 1


class TestErrores:
    def test_get_when_falta_id_servicio_returns_400(
        self, api_client, catalogo, partner_auth_headers
    ):
        # Act
        response = api_client.get(URL, **partner_auth_headers)

        # Assert
        assert response.status_code == 400
        assert response.json()["code"] == "validation_error"

    def test_get_when_id_servicio_no_numerico_returns_400(
        self, api_client, catalogo, partner_auth_headers
    ):
        # Act
        response = api_client.get(f"{URL}?id_servicio=abc", **partner_auth_headers)

        # Assert
        assert response.status_code == 400

    def test_get_when_servicio_inexistente_returns_404(
        self, api_client, catalogo, partner_auth_headers
    ):
        # Act
        response = api_client.get(f"{URL}?id_servicio=99999", **partner_auth_headers)

        # Assert
        assert response.status_code == 404

    def test_get_when_version_inexistente_returns_404(
        self, api_client, catalogo, partner_auth_headers
    ):
        # Act
        response = api_client.get(
            f"{URL}?id_servicio={DESPACHO}&version=v99", **partner_auth_headers
        )

        # Assert
        assert response.status_code == 404


class TestAcceso:
    def test_get_when_sin_token_returns_401(self, api_client, catalogo):
        # Act
        response = api_client.get(f"{URL}?id_servicio={DESPACHO}")

        # Assert
        assert response.status_code == 401

    def test_get_when_gestor_returns_200(
        self, api_client, catalogo, devapis_auth_headers
    ):
        """El catalogo lo consultan tanto el partner como quien lo gestiona."""
        # Act
        response = api_client.get(
            f"{URL}?id_servicio={DESPACHO}", **devapis_auth_headers
        )

        # Assert
        assert response.status_code == 200
