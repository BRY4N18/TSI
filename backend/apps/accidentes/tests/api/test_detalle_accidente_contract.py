import pytest


@pytest.mark.api
class TestDetalleAccidenteContract:
    def test_detalle_when_exists_returns_200_with_history(
        self, api_client, operador_auth_headers, seed_accidente
    ):
        # Arrange
        aid = seed_accidente(idaccidente="ACC-DET-1")

        # Act
        response = api_client.get(f"/api/v1/accidentes/{aid}", **operador_auth_headers)

        # Assert
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["idaccidente"] == aid
        assert data["estado_actual"] == "REPORTADO"
        assert len(data["historial_estados"]) >= 2

    def test_detalle_when_missing_returns_404(self, api_client, operador_auth_headers):
        # Act
        response = api_client.get("/api/v1/accidentes/ACC-MISSING", **operador_auth_headers)

        # Assert
        assert response.status_code == 404
