import pytest


@pytest.mark.api
class TestAsignarManualContract:
    def test_asignar_when_valid_returns_201(
        self,
        api_client,
        operador_despacho_auth_headers,
        accidente_activo,
        unidad_con_estado_activa,
    ):
        # Act
        response = api_client.post(
            f"/api/v1/accidentes/{accidente_activo}/despacho/asignar-manual",
            {"idunidademergencia": 1},
            format="json",
            **operador_despacho_auth_headers,
        )

        # Assert
        assert response.status_code == 201
        assert response.json()["data"]["origen"] == "Manual"
