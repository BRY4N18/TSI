import pytest

from apps.accidentes.domain_constants import ESTADO_CERRADO
from apps.seguimiento.services.cancelar_caso_service import CancelarCasoService
from core.repositories.accidentes.estado_accidente_repository import EstadoAccidenteRepository


@pytest.mark.service
class TestCancelarCasoService:
    def test_cancelar_when_motivo_cierra_caso(
        self,
        mock_pinot,
        mock_kafka,
        accidente_activo,
        despacho_confirmado_unidad,
    ):
        # Arrange
        svc = CancelarCasoService()

        # Act
        result = svc.cancelar(
            idaccidente=accidente_activo,
            idusuario=2,
            motivo="Falsa alarma",
        )

        # Assert
        assert result["estado_caso"] == ESTADO_CERRADO
        assert EstadoAccidenteRepository().get_current_estado(accidente_activo) == ESTADO_CERRADO

    def test_cancelar_when_sin_motivo_raises(
        self,
        mock_pinot,
        mock_kafka,
        accidente_activo,
    ):
        # Arrange
        svc = CancelarCasoService()

        # Act / Assert
        with pytest.raises(ValueError, match="Motivo requerido"):
            svc.cancelar(idaccidente=accidente_activo, idusuario=2, motivo="")
