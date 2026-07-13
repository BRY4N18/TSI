import pytest

from core.repositories.despacho.historial_despacho_repository import (
    ESTADO_ABORTADO,
    HistorialDespachoRepository,
)


@pytest.mark.api
class TestAbortarMisionContract:
    def test_post_abortar_when_confirmado_returns_200(
        self,
        api_client,
        unidad_seguimiento_auth_headers,
        accidente_activo,
        despacho_confirmado_unidad,
    ):
        # Arrange
        iddespacho = despacho_confirmado_unidad["iddespacho"]

        # Act
        response = api_client.post(
            f"/api/v1/mi-seguimiento/despachos/{iddespacho}/abortar",
            {"motivo": "Imposible llegar"},
            format="json",
            **unidad_seguimiento_auth_headers,
        )

        # Assert
        assert response.status_code == 200
        body = response.json()
        assert body["data"]["estado_despacho"] == ESTADO_ABORTADO
        assert body["data"]["reasignacion_disparada"] is True
        estado, _ = HistorialDespachoRepository().get_current_estado(iddespacho)
        assert estado == ESTADO_ABORTADO

    def test_post_abortar_when_not_found_returns_404(
        self,
        api_client,
        unidad_seguimiento_auth_headers,
    ):
        # Arrange

        # Act
        response = api_client.post(
            "/api/v1/mi-seguimiento/despachos/99999/abortar",
            {},
            format="json",
            **unidad_seguimiento_auth_headers,
        )

        # Assert
        assert response.status_code == 404
