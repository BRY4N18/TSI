import pytest

from apps.accidentes.domain_constants import ESTADO_FUSIONADO
from apps.accidentes.services.fusionar_reportes_service import FusionarReportesService


@pytest.mark.service
class TestFusionarReportesService:
    def test_fusionar_when_valid_marks_duplicado_fusionado(
        self, mock_pinot, mock_kafka, seed_accidente
    ):
        # Arrange
        principal = seed_accidente(idaccidente="ACC-F-P")
        duplicado = seed_accidente(idaccidente="ACC-F-D")
        service = FusionarReportesService()

        # Act
        result = service.fusionar(
            idaccidente_duplicado=duplicado,
            idaccidente_principal=principal,
            idusuario=2,
            confirmacion=True,
        )

        # Assert
        assert result["estado_duplicado"] == ESTADO_FUSIONADO
