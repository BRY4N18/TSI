import pytest

from apps.accidentes.services.registro_accidente_service import RegistroAccidenteService


@pytest.mark.service
class TestRegistroAccidenteService:
    def test_registrar_when_no_advertencias_promotes_to_reportado(
        self, mock_pinot, mock_kafka, accidente_payload
    ):
        # Arrange
        service = RegistroAccidenteService()

        # Act
        result = service.registrar(accidente_payload, idusuario=2)

        # Assert
        assert result["estado"] == "REPORTADO"
        assert result["idaccidente"].startswith("ACC-")
