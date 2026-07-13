import pytest


@pytest.mark.api
class TestListarAccidentesContract:
    def test_listar_when_activos_returns_200(self, api_client, operador_auth_headers, seed_accidente):
        # Arrange
        seed_accidente(idaccidente="ACC-LIST-1")

        # Act
        response = api_client.get("/api/v1/accidentes", **operador_auth_headers)

        # Assert
        assert response.status_code == 200
        body = response.json()
        assert isinstance(body["data"], list)
        assert any(a["idaccidente"] == "ACC-LIST-1" for a in body["data"])

    def test_listar_when_filter_severidad_returns_filtered(
        self, api_client, operador_auth_headers, seed_accidente
    ):
        # Arrange
        seed_accidente(idaccidente="ACC-S1", idseveridad=1)
        seed_accidente(idaccidente="ACC-S2", idseveridad=3)

        # Act
        response = api_client.get(
            "/api/v1/accidentes",
            {"idseveridad": 1},
            **operador_auth_headers,
        )

        # Assert
        assert response.status_code == 200
        ids = [a["idaccidente"] for a in response.json()["data"]]
        assert "ACC-S1" in ids
        assert "ACC-S2" not in ids

    def test_listar_when_filter_estado_returns_filtered(
        self, api_client, operador_auth_headers, seed_accidente
    ):
        # Arrange
        seed_accidente(idaccidente="ACC-E1", estado="BORRADOR")
        seed_accidente(idaccidente="ACC-E2", estado="REPORTADO")

        # Act
        response = api_client.get(
            "/api/v1/accidentes",
            {"estado": "REPORTADO"},
            **operador_auth_headers,
        )

        # Assert
        assert response.status_code == 200
        ids = [a["idaccidente"] for a in response.json()["data"]]
        assert "ACC-E2" in ids
        assert "ACC-E1" not in ids

    def test_listar_when_filter_fecha_range_returns_filtered(
        self, api_client, operador_auth_headers, seed_accidente
    ):
        # Arrange
        seed_accidente(idaccidente="ACC-F1", fechahoraaccidente=1_000)
        seed_accidente(idaccidente="ACC-F2", fechahoraaccidente=9_000)

        # Act
        response = api_client.get(
            "/api/v1/accidentes",
            {"fecha_desde": 5_000, "fecha_hasta": 10_000},
            **operador_auth_headers,
        )

        # Assert
        assert response.status_code == 200
        ids = [a["idaccidente"] for a in response.json()["data"]]
        assert "ACC-F2" in ids
        assert "ACC-F1" not in ids

    def test_listar_when_filter_idciudad_returns_filtered(
        self, api_client, operador_auth_headers, seed_accidente
    ):
        # Arrange
        seed_accidente(idaccidente="ACC-CIU1", idcalle=1)
        seed_accidente(idaccidente="ACC-CIU99", idcalle=99)

        # Act
        response = api_client.get(
            "/api/v1/accidentes",
            {"idciudad": 1},
            **operador_auth_headers,
        )

        # Assert
        assert response.status_code == 200
        ids = [a["idaccidente"] for a in response.json()["data"]]
        assert "ACC-CIU1" in ids
        assert "ACC-CIU99" not in ids

    def test_listar_when_filter_idestadoregion_returns_filtered(
        self, api_client, operador_auth_headers, seed_accidente
    ):
        # Arrange
        seed_accidente(idaccidente="ACC-EST1", idcalle=1)
        seed_accidente(idaccidente="ACC-EST99", idcalle=99)

        # Act
        response = api_client.get(
            "/api/v1/accidentes",
            {"idestadoregion": 1},
            **operador_auth_headers,
        )

        # Assert
        assert response.status_code == 200
        ids = [a["idaccidente"] for a in response.json()["data"]]
        assert "ACC-EST1" in ids
        assert "ACC-EST99" not in ids

    def test_listar_when_filter_parametros_invalidos_returns_400(
        self, api_client, operador_auth_headers
    ):
        # Act
        response = api_client.get(
            "/api/v1/accidentes",
            {"idseveridad": "no-es-numero"},
            **operador_auth_headers,
        )

        # Assert
        assert response.status_code == 400
