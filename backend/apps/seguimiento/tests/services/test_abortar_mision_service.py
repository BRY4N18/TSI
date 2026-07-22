import pytest

from apps.seguimiento.services.abortar_mision_service import AbortarMisionService
from core.repositories.despacho.historial_despacho_repository import ESTADO_ABORTADO


@pytest.mark.service
class TestAbortarMisionService:
    def test_abortar_when_confirmado_publica_evento(
        self,
        mock_pinot,
        mock_kafka,
        accidente_activo,
        despacho_confirmado_unidad,
    ):
        # Arrange
        iddespacho = despacho_confirmado_unidad["iddespacho"]
        svc = AbortarMisionService()

        # Act
        result = svc.abortar(
            iddespacho=iddespacho,
            idunidademergencia=1,
            idusuario=6,
            motivo="Ruta bloqueada",
        )

        # Assert
        assert result["estado_despacho"] == ESTADO_ABORTADO
        assert result["reasignacion_disparada"] is True
        assert any("Abortado" in m["topic"] for m in mock_kafka)

    def test_abortar_when_en_sitio_raises(
        self,
        mock_pinot,
        mock_kafka,
        accidente_activo,
        despacho_confirmado_unidad,
    ):
        # Arrange
        from apps.seguimiento.services.registrar_llegada_service import (
            RegistrarLlegadaService,
        )

        iddespacho = despacho_confirmado_unidad["iddespacho"]
        RegistrarLlegadaService().registrar(iddespacho=iddespacho, idunidademergencia=1, idusuario=6)
        svc = AbortarMisionService()

        # Act / Assert
        with pytest.raises(ValueError, match="inválido"):
            svc.abortar(iddespacho=iddespacho, idunidademergencia=1, idusuario=6)
