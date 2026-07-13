import pytest


@pytest.mark.api
class TestCoordinarDespachoContract:
    def test_coordinar_when_second_unit_returns_201(
        self,
        api_client,
        operador_despacho_auth_headers,
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

        # Act
        response = api_client.post(
            f"/api/v1/accidentes/{accidente_activo}/despacho/coordinar",
            {"idunidademergencia": 2},
            format="json",
            **operador_despacho_auth_headers,
        )

        # Assert
        assert response.status_code == 201
