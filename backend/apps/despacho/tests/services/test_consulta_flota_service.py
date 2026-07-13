import pytest

from apps.despacho.services.consulta_flota_service import ConsultaFlotaService
from core.repositories.despacho.historial_estado_unidad_repository import (
    HistorialEstadoUnidadRepository,
)


@pytest.mark.service
class TestConsultaFlotaService:
    def test_listar_when_units_exist_returns_with_estado(
        self, mock_pinot, mock_kafka, unidad_con_estado_activa
    ):
        # Arrange
        HistorialEstadoUnidadRepository().append_estado(
            idunidademergencia=2,
            estadonuevo="Fuera de servicio",
            idusuario=1,
        )
        service = ConsultaFlotaService()

        # Act
        items, _ = service.listar()

        # Assert
        assert len(items) >= 2
        activa = next(i for i in items if i["idunidademergencia"] == 1)
        assert activa["estado_actual"] == "Activa"
        assert activa["incluido_en_despacho"] is True

    def test_listar_when_estado_filter_applied_returns_matching(
        self, mock_pinot, mock_kafka, unidad_con_estado_activa
    ):
        # Arrange
        service = ConsultaFlotaService()

        # Act
        items, _ = service.listar(estado="Activa")

        # Assert
        assert all(i["estado_actual"] == "Activa" for i in items)
