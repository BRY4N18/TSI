import pytest

from apps.despacho.services.consulta_candidatas_service import ConsultaCandidatasService


@pytest.mark.service
class TestConsultaCandidatasService:
    def test_listar_puntuadas_when_unidad_activa_returns_ranked(
        self, mock_pinot, mock_kafka, accidente_activo, unidad_con_estado_activa
    ):
        # Arrange
        svc = ConsultaCandidatasService()

        # Act
        ranked = svc.listar_puntuadas(accidente_activo)

        # Assert
        assert len(ranked) >= 1
        assert ranked[0]["idunidademergencia"] == 1
        assert ranked[0]["puntuacion"] > 0

    def test_listar_puntuadas_when_accidente_missing_raises(self, mock_pinot, mock_kafka):
        # Arrange
        svc = ConsultaCandidatasService()

        # Act / Assert
        with pytest.raises(LookupError):
            svc.listar_puntuadas("ACC-NO-EXISTE")
