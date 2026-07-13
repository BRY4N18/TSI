import pytest

from apps.accidentes.domain_constants import ESTADO_ASIGNADO
from apps.accidentes.services.confirmar_reporte_service import ConflictError
from apps.accidentes.services.escalar_severidad_service import EscalarSeveridadService


@pytest.mark.service
class TestEscalarSeveridadService:
    def test_escalar_when_valid_increments_severity(
        self, mock_pinot, mock_kafka, seed_accidente, pinot_store
    ):
        # Arrange
        aid = seed_accidente(
            idaccidente="ACC-ESC", estado=ESTADO_ASIGNADO, idseveridad=2, numheridos=1
        )
        pinot_store["Fact_Despacho"].append({"iddespacho": 1, "idaccidente": aid, "activo": True})
        service = EscalarSeveridadService()

        # Act
        result = service.escalar(
            idaccidente=aid,
            data={"idseveridad": 3, "numheridos": 2, "nota": "más heridos"},
            idusuario=6,
        )

        # Assert
        assert result["idseveridad"] == 3

    def test_escalar_when_no_despacho_raises(self, mock_pinot, mock_kafka, seed_accidente):
        # Arrange
        aid = seed_accidente(idaccidente="ACC-ESC2", estado=ESTADO_ASIGNADO)
        service = EscalarSeveridadService()

        # Act / Assert
        with pytest.raises(ConflictError):
            service.escalar(
                idaccidente=aid,
                data={"idseveridad": 3, "nota": "x"},
                idusuario=6,
            )
