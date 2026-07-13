import pytest

from apps.accidentes.domain_constants import ESTADO_EN_ATENCION
from core.repositories.accidentes.estado_accidente_repository import EstadoAccidenteRepository
from core.repositories.despacho.historial_despacho_repository import (
    ESTADO_EN_SITIO,
    HistorialDespachoRepository,
)


@pytest.mark.critical_path
class TestGpsLlegadaIntegration:
    def test_gps_then_manual_llegada_sets_en_atencion(
        self,
        api_client,
        unidad_seguimiento_auth_headers,
        accidente_activo,
        despacho_confirmado_unidad,
    ):
        # Arrange
        iddespacho = despacho_confirmado_unidad["iddespacho"]
        pos_payload = {
            "idunidademergencia": 1,
            "idaccidente": accidente_activo,
            "latitud": 19.44,
            "longitud": -99.14,
            "fechahora": 1_700_000_000_000,
        }

        # Act
        pos = api_client.post(
            "/api/v1/mi-seguimiento/posicion",
            pos_payload,
            format="json",
            **unidad_seguimiento_auth_headers,
        )
        llegada = api_client.post(
            f"/api/v1/mi-seguimiento/despachos/{iddespacho}/llegada",
            {},
            format="json",
            **unidad_seguimiento_auth_headers,
        )

        # Assert
        assert pos.status_code == 202
        assert llegada.status_code == 200
        estado_despacho, _ = HistorialDespachoRepository().get_current_estado(iddespacho)
        assert estado_despacho == ESTADO_EN_SITIO
        assert EstadoAccidenteRepository().get_current_estado(accidente_activo) == ESTADO_EN_ATENCION

    def test_gps_geofencing_auto_llegada_sets_en_atencion(
        self,
        api_client,
        unidad_seguimiento_auth_headers,
        accidente_activo,
        despacho_confirmado_unidad,
    ):
        # Arrange
        iddespacho = despacho_confirmado_unidad["iddespacho"]
        base = 1_700_000_000_000
        coords = {"latitud": 19.4326, "longitud": -99.1332}

        # Act
        api_client.post(
            "/api/v1/mi-seguimiento/posicion",
            {"idunidademergencia": 1, "idaccidente": accidente_activo, **coords, "fechahora": base},
            format="json",
            **unidad_seguimiento_auth_headers,
        )
        response = api_client.post(
            "/api/v1/mi-seguimiento/posicion",
            {
                "idunidademergencia": 1,
                "idaccidente": accidente_activo,
                **coords,
                "fechahora": base + 31_000,
            },
            format="json",
            **unidad_seguimiento_auth_headers,
        )

        # Assert
        assert response.status_code == 202
        assert response.json()["data"]["llegada_automatica"] is True
        estado_despacho, _ = HistorialDespachoRepository().get_current_estado(iddespacho)
        assert estado_despacho == ESTADO_EN_SITIO
