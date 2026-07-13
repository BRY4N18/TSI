import pytest

from core.repositories.cuentas_clientes.onboarding_repository import OnboardingRepository


@pytest.mark.repository
class TestOnboardingRepository:
    def test_complete_etapa_publishes_fact_onboarding(self, mock_pinot, mock_kafka):
        # Arrange
        repo = OnboardingRepository()

        # Act
        result = repo.complete_etapa(1, "cambio_password")

        # Assert
        assert result["completado"] is True
        assert result["etapa"] == "cambio_password"
        assert len(mock_kafka) == 1

    def test_list_by_cliente_returns_etapas(self, mock_pinot, mock_kafka):
        # Arrange
        repo = OnboardingRepository()
        repo.complete_etapa(1, "cambio_password")

        # Act
        rows = repo.list_by_cliente(1)

        # Assert
        assert len(rows) == 1

    def test_find_etapa_when_exists_returns_row(self, mock_pinot, mock_kafka):
        # Arrange
        repo = OnboardingRepository()
        repo.complete_etapa(1, "perfil_corporativo")

        # Act
        row = repo.find_etapa(1, "perfil_corporativo")

        # Assert
        assert row is not None
        assert row["completado"] is True
