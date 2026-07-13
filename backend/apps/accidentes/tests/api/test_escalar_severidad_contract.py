import pytest

from apps.accidentes.domain_constants import ESTADO_ASIGNADO


@pytest.mark.api
class TestEscalarSeveridadContract:
    def test_escalar_when_valid_returns_200(
        self, api_client, unidad_auth_headers, seed_accidente, pinot_store
    ):
        # Arrange
        aid = seed_accidente(idaccidente="ACC-API-ESC", estado=ESTADO_ASIGNADO, idseveridad=2)
        pinot_store["Fact_Despacho"].append({"iddespacho": 1, "idaccidente": aid, "activo": True})

        # Act
        response = api_client.post(
            f"/api/v1/accidentes/{aid}/escalar-severidad",
            {"idseveridad": 3, "numheridos": 2, "nota": "escalamiento en sitio"},
            format="json",
            **unidad_auth_headers,
        )

        # Assert
        assert response.status_code == 200
        assert response.json()["data"]["idseveridad"] == 3

    def test_escalar_when_operador_returns_403(
        self, api_client, operador_auth_headers, seed_accidente, pinot_store
    ):
        # Arrange
        aid = seed_accidente(idaccidente="ACC-API-ESC2", estado=ESTADO_ASIGNADO)
        pinot_store["Fact_Despacho"].append({"iddespacho": 2, "idaccidente": aid, "activo": True})

        # Act
        response = api_client.post(
            f"/api/v1/accidentes/{aid}/escalar-severidad",
            {"idseveridad": 3, "nota": "x"},
            format="json",
            **operador_auth_headers,
        )

        # Assert
        assert response.status_code == 403
