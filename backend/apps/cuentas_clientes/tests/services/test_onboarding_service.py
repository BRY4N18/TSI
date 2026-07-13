import pytest

from apps.cuentas_clientes.services.onboarding_service import OnboardingService


@pytest.mark.service
class TestOnboardingService:
    def test_get_progreso_when_pendiente_returns_first_etapa(
        self, mock_pinot, mock_kafka, mock_cuenta_pendiente_onboarding
    ):
        # Arrange
        service = OnboardingService()
        cliente_id = mock_cuenta_pendiente_onboarding

        # Act
        result = service.get_progreso(
            user_id=5, roles=["Cliente"], cliente_id=cliente_id
        )

        # Assert
        assert result["etapa_actual"] == "cambio_password"
        assert result["estado_onboarding"] == "Pendiente"

    def test_completar_cambio_password_when_credencial_activa(
        self, mock_pinot, mock_kafka, mock_cuenta_pendiente_onboarding
    ):
        # Arrange
        service = OnboardingService()
        cliente_id = mock_cuenta_pendiente_onboarding

        # Act
        result = service.completar_etapa(
            user_id=5,
            roles=["Cliente"],
            cliente_id=cliente_id,
            etapa="cambio_password",
        )

        # Assert
        assert result["etapa"] == "cambio_password"
        assert "cambio_password" in result["progreso"]["etapas_completadas"]

    def test_completar_perfil_after_password(
        self, mock_pinot, mock_kafka, mock_onboarding_etapas
    ):
        # Arrange
        service = OnboardingService()
        cliente_id = mock_onboarding_etapas

        # Act
        result = service.completar_etapa(
            user_id=5,
            roles=["Cliente"],
            cliente_id=cliente_id,
            etapa="perfil_corporativo",
            datos_etapa={"nombre": "Actualizado"},
        )

        # Assert
        assert result["etapa"] == "perfil_corporativo"
