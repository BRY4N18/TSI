import pytest

from apps.accidentes.domain_constants import ESTADO_CERRADO
from apps.seguimiento.services.forzar_retiro_service import ForzarRetiroService
from apps.seguimiento.services.registrar_llegada_service import RegistrarLlegadaService
from core.repositories.despacho.historial_despacho_repository import (
    ESTADO_RETIRADO,
    HistorialDespachoRepository,
)


@pytest.mark.service
class TestForzarRetiroService:
    def test_forzar_when_unico_despacho_cierra_caso(
        self,
        mock_pinot,
        mock_kafka,
        accidente_activo,
        despacho_confirmado_unidad,
    ):
        # Arrange
        iddespacho = despacho_confirmado_unidad["iddespacho"]
        RegistrarLlegadaService().registrar(iddespacho=iddespacho, idunidademergencia=1, idusuario=6)
        svc = ForzarRetiroService()

        # Act
        result = svc.forzar(iddespacho=iddespacho, idusuario=2)

        # Assert
        assert result["caso_cerrado"] is True
        assert result["estado_caso"] == ESTADO_CERRADO
        estado, _ = HistorialDespachoRepository().get_current_estado(iddespacho)
        assert estado == ESTADO_RETIRADO

    def test_forzar_when_not_found_raises(
        self,
        mock_pinot,
        mock_kafka,
    ):
        # Arrange
        svc = ForzarRetiroService()

        # Act / Assert
        with pytest.raises(LookupError):
            svc.forzar(iddespacho=99999, idusuario=2)
