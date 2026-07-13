import pytest


@pytest.mark.api
class TestListarCandidatasContract:
    def test_listar_when_operador_returns_200(
        self,
        api_client,
        operador_despacho_auth_headers,
        accidente_activo,
        unidad_con_estado_activa,
    ):
        # Act
        response = api_client.get(
            f"/api/v1/accidentes/{accidente_activo}/despacho/unidades-candidatas",
            **operador_despacho_auth_headers,
        )

        # Assert
        assert response.status_code == 200
        assert len(response.json()["data"]["candidatas"]) >= 1
