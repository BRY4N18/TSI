import pytest

from apps.accidentes.domain_constants import ESTADO_BORRADOR, ESTADO_DESCARTADO
from apps.accidentes.services.confirmar_reporte_service import ConflictError
from apps.accidentes.services.descartar_caso_service import DescartarCasoService


@pytest.mark.service
class TestDescartarCasoService:
    def test_descartar_when_borrador_sets_inactivo(self, mock_pinot, mock_kafka, seed_accidente):
        # Arrange
        aid = seed_accidente(idaccidente="ACC-D-SVC", estado=ESTADO_BORRADOR)
        service = DescartarCasoService()

        # Act
        result = service.descartar(idaccidente=aid, idusuario=2, motivo="test")

        # Assert
        assert result["estado"] == ESTADO_DESCARTADO

    def test_descartar_when_not_borrador_raises(self, mock_pinot, mock_kafka, seed_accidente):
        # Arrange
        aid = seed_accidente(idaccidente="ACC-D-SVC2", estado="REPORTADO")
        service = DescartarCasoService()

        # Act / Assert
        with pytest.raises(ConflictError):
            service.descartar(idaccidente=aid, idusuario=2)
