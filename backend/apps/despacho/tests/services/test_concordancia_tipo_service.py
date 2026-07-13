import pytest

from apps.despacho.services.concordancia_tipo_service import ConcordanciaTipoService


@pytest.mark.service
class TestConcordanciaTipoService:
    def test_score_when_ambulancia_first_for_critica(self, mock_pinot, mock_kafka):
        # Arrange
        svc = ConcordanciaTipoService()

        # Act
        score = svc.score_tipo(idseveridad=4, tipounidademergencia="Ambulancia")

        # Assert
        assert score == 1.0

    def test_score_when_moderada_keyword_prefers_ambulancia(self, mock_pinot, mock_kafka):
        # Arrange
        svc = ConcordanciaTipoService()

        # Act
        score_amb = svc.score_tipo(
            idseveridad=3,
            tipounidademergencia="Ambulancia",
            descripcion="herido leve en vía",
        )
        score_grua = svc.score_tipo(
            idseveridad=3,
            tipounidademergencia="Grua",
            descripcion="herido leve en vía",
        )

        # Assert
        assert score_amb > score_grua
