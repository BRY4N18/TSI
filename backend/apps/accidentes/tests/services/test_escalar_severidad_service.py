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

    def test_escalar_when_unidad_adicional_triggers_o38(
        self, mock_pinot, mock_kafka, seed_accidente, pinot_store
    ):
        # Arrange
        aid = seed_accidente(
            idaccidente="ACC-ESC-O38",
            estado=ESTADO_ASIGNADO,
            idseveridad=2,
            numheridos=1,
        )
        pinot_store["Fact_Despacho"].append(
            {
                "iddespacho": 10,
                "idaccidente": aid,
                "idunidademergencia": 1,
                "activo": True,
            }
        )
        called: dict = {}

        class FakeCoord:
            def coordinar(self, **kwargs):
                called.update(kwargs)
                return {"iddespacho": 99, "message": "Despacho múltiple coordinado"}

        service = EscalarSeveridadService(coordinacion_factory=lambda: FakeCoord())

        # Act
        result = service.escalar(
            idaccidente=aid,
            data={
                "idseveridad": 4,
                "nota": "fatal — necesita segunda unidad",
                "idunidademergencia_adicional": 2,
            },
            idusuario=6,
        )

        # Assert
        assert result["despacho_adicional"]["iddespacho"] == 99
        assert called["idunidademergencia"] == 2
        assert "CU-O38" in result["message"]

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
