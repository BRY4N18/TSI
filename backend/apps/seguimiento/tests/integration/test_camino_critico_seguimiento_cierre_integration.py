import pytest

from apps.accidentes.domain_constants import ESTADO_CERRADO, ESTADO_EN_ATENCION
from core.repositories.accidentes.estado_accidente_repository import EstadoAccidenteRepository
from core.repositories.despacho.historial_despacho_repository import (
    ESTADO_EN_SITIO,
    HistorialDespachoRepository,
)


@pytest.mark.critical_path
class TestCaminoCriticoSeguimientoCierreIntegration:
    def test_confirmado_gps_llegada_cierre_completa_flujo(
        self,
        api_client,
        unidad_seguimiento_auth_headers,
        operador_seguimiento_auth_headers,
        accidente_activo,
        despacho_confirmado_unidad,
    ):
        # Arrange
        iddespacho = despacho_confirmado_unidad["iddespacho"]
        pos_payload = {
            "idunidademergencia": 1,
            "idaccidente": accidente_activo,
            "latitud": 19.4326,
            "longitud": -99.1332,
            "fechahora": 1_700_000_000_000,
        }

        # Act — GPS
        pos = api_client.post(
            "/api/v1/mi-seguimiento/posicion",
            pos_payload,
            format="json",
            **unidad_seguimiento_auth_headers,
        )
        # Act — llegada
        llegada = api_client.post(
            f"/api/v1/mi-seguimiento/despachos/{iddespacho}/llegada",
            {},
            format="json",
            **unidad_seguimiento_auth_headers,
        )
        # Act — cierre
        cierre = api_client.post(
            f"/api/v1/accidentes/{accidente_activo}/cerrar",
            {"resultado_atencion": "Camino crítico completado"},
            format="json",
            **operador_seguimiento_auth_headers,
        )

        # Assert
        assert pos.status_code == 202
        assert llegada.status_code == 200
        assert cierre.status_code == 200
        estado_despacho, _ = HistorialDespachoRepository().get_current_estado(iddespacho)
        assert estado_despacho == ESTADO_EN_SITIO or cierre.json()["data"]["estado_caso"] == ESTADO_CERRADO
        assert EstadoAccidenteRepository().get_current_estado(accidente_activo) == ESTADO_CERRADO
        assert cierre.json()["data"]["estado_caso"] == ESTADO_CERRADO
