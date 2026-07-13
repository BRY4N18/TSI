import pytest


@pytest.mark.api
class TestRechazarDespachoContract:
    def test_rechazar_when_pendiente_returns_200(
        self,
        api_client,
        unidad_auth_headers,
        accidente_activo,
        unidad_con_estado_activa,
        despacho_pendiente_unidad,
    ):
        # Arrange
        from core.repositories.despacho.historial_estado_unidad_repository import (
            HistorialEstadoUnidadRepository,
        )

        HistorialEstadoUnidadRepository().append_estado(
            idunidademergencia=2,
            estadonuevo="Activa",
            idusuario=99,
            estadoanterior="Fuera de servicio",
        )
        idnotif = despacho_pendiente_unidad["idnotificaciondespacho"]

        # Act
        response = api_client.post(
            f"/api/v1/mi-despacho/{idnotif}/rechazar",
            {"motivo": "Fuera de zona"},
            format="json",
            **unidad_auth_headers,
        )

        # Assert
        assert response.status_code == 200
        body = response.json()
        assert body["data"]["reasignacion_iniciada"] is True

    def test_rechazar_when_sin_motivo_returns_400(
        self,
        api_client,
        unidad_auth_headers,
        accidente_activo,
        unidad_con_estado_activa,
        despacho_pendiente_unidad,
    ):
        # Arrange
        idnotif = despacho_pendiente_unidad["idnotificaciondespacho"]

        # Act
        response = api_client.post(
            f"/api/v1/mi-despacho/{idnotif}/rechazar",
            {},
            format="json",
            **unidad_auth_headers,
        )

        # Assert
        assert response.status_code == 400
