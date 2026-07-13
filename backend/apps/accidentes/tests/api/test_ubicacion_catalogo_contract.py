import pytest


@pytest.mark.api
class TestUbicacionCatalogoContract:
    def test_listar_paises_returns_200(self, api_client, operador_auth_headers):
        # Act
        response = api_client.get("/api/v1/accidentes/paises", **operador_auth_headers)

        # Assert
        assert response.status_code == 200
        assert response.json()["data"] == [{"id": 1, "nombre": "México"}]

    def test_listar_estados_when_idpais_provided_returns_200(
        self, api_client, operador_auth_headers
    ):
        # Act
        response = api_client.get(
            "/api/v1/accidentes/estados", {"idpais": 1}, **operador_auth_headers
        )

        # Assert
        assert response.status_code == 200
        assert {e["id"] for e in response.json()["data"]} == {1, 2}

    def test_listar_estados_when_idpais_missing_returns_400(
        self, api_client, operador_auth_headers
    ):
        # Act
        response = api_client.get("/api/v1/accidentes/estados", {}, **operador_auth_headers)

        # Assert
        assert response.status_code == 400

    def test_listar_condados_when_idestado_provided_returns_200(
        self, api_client, operador_auth_headers
    ):
        # Act
        response = api_client.get(
            "/api/v1/accidentes/condados", {"idestado": 1}, **operador_auth_headers
        )

        # Assert
        assert response.status_code == 200
        assert {c["id"] for c in response.json()["data"]} == {1, 2}

    def test_listar_ciudades_when_idcondado_provided_returns_200(
        self, api_client, operador_auth_headers
    ):
        # Act
        response = api_client.get(
            "/api/v1/accidentes/ciudades", {"idcondado": 1}, **operador_auth_headers
        )

        # Assert
        assert response.status_code == 200
        assert response.json()["data"] == [{"id": 1, "nombre": "Ciudad de México"}]

    def test_listar_calles_when_idciudad_provided_returns_200(
        self, api_client, operador_auth_headers
    ):
        # Act
        response = api_client.get(
            "/api/v1/accidentes/calles", {"idciudad": 1}, **operador_auth_headers
        )

        # Assert
        assert response.status_code == 200
        assert response.json()["data"] == [{"id": 1, "nombre": "Av. Reforma"}]

    def test_listar_calles_without_auth_returns_401_or_403(self, api_client):
        # Act
        response = api_client.get("/api/v1/accidentes/calles", {"idciudad": 1})

        # Assert
        assert response.status_code in (401, 403)
