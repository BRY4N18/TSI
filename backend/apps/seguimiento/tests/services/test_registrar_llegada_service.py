import pytest

from apps.accidentes.domain_constants import ESTADO_EN_ATENCION
from apps.seguimiento.services.registrar_llegada_service import RegistrarLlegadaService
from core.repositories.despacho.historial_despacho_repository import (
    ESTADO_EN_SITIO,
    HistorialDespachoRepository,
)


@pytest.mark.service
class TestRegistrarLlegadaService:
    def test_registrar_when_confirmado_transitions_to_en_sitio(
        self,
        mock_pinot,
        mock_kafka,
        accidente_activo,
        despacho_confirmado_unidad,
    ):
        # Arrange
        iddespacho = despacho_confirmado_unidad["iddespacho"]
        svc = RegistrarLlegadaService()

        # Act
        result = svc.registrar(
            iddespacho=iddespacho,
            idunidademergencia=1,
            idusuario=6,
        )

        # Assert
        assert result["fechahorallegada"] is not None
        assert result["estado_caso"] == ESTADO_EN_ATENCION
        estado, _ = HistorialDespachoRepository().get_current_estado(iddespacho)
        assert estado == ESTADO_EN_SITIO

    def test_registrar_when_already_en_sitio_raises(self, mock_pinot, mock_kafka, despacho_confirmado_unidad):
        # Arrange
        iddespacho = despacho_confirmado_unidad["iddespacho"]
        svc = RegistrarLlegadaService()
        svc.registrar(iddespacho=iddespacho, idunidademergencia=1, idusuario=6)

        # Act / Assert
        with pytest.raises(ValueError, match="ya registrada"):
            svc.registrar(iddespacho=iddespacho, idunidademergencia=1, idusuario=6)
