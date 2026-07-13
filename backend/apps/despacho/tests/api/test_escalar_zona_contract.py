import pytest


@pytest.mark.api
class TestEscalarZonaContract:
    def test_escalar_when_operador_returns_200_or_202(
        self,
        api_client,
        operador_despacho_auth_headers,
        accidente_activo,
        unidad_con_estado_activa,
    ):
        # Act
        response = api_client.post(
            f"/api/v1/accidentes/{accidente_activo}/despacho/escalar-zona",
            {},
            format="json",
            **operador_despacho_auth_headers,
        )

        # Assert
        assert response.status_code in (200, 202)
