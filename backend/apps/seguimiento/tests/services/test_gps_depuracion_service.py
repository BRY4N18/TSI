import pytest

from apps.seguimiento.services.gps_depuracion_service import GpsDepuracionService
from apps.seguimiento.services.registrar_llegada_service import RegistrarLlegadaService
from apps.seguimiento.services.retiro_despacho_service import RetiroDespachoService
from core.repositories.seguimiento.historial_ubicacion_repository import (
    HistorialUbicacionRepository,
)


@pytest.mark.service
class TestGpsDepuracionService:
    def test_puntos_a_conservar_keeps_origen_llegada_cierre(
        self,
        mock_pinot,
        mock_kafka,
        accidente_activo,
        despacho_confirmado_unidad,
    ):
        # Arrange
        repo = HistorialUbicacionRepository()
        iddespacho = despacho_confirmado_unidad["iddespacho"]
        base = 1_700_000_000_000
        for i in range(5):
            repo.publish(
                idunidademergencia=1,
                idaccidente=accidente_activo,
                latitud=19.43 + i * 0.001,
                longitud=-99.13,
                fechahora=base + i * 10_000,
            )
        RegistrarLlegadaService().registrar(iddespacho=iddespacho, idunidademergencia=1, idusuario=6)
        RetiroDespachoService().retirar(iddespacho=iddespacho, idusuario=2)
        svc = GpsDepuracionService()

        # Act
        conservar = svc.puntos_a_conservar(iddespacho)

        # Assert
        assert len(conservar) >= 2
        assert len(conservar) <= 3

    def test_depurar_returns_summary(
        self,
        mock_pinot,
        mock_kafka,
        accidente_activo,
        despacho_confirmado_unidad,
    ):
        # Arrange
        svc = GpsDepuracionService()

        # Act
        result = svc.depurar()

        # Assert
        assert "depurados" in result
        assert "retencion_dias" in result
