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

    def test_registrar_when_tiporeportado_persists(
        self, mock_pinot, mock_kafka, accidente_payload, pinot_store
    ):
        # Arrange
        service = RegistroAccidenteService()
        payload = {
            **accidente_payload,
            "idtiporeportado": 2,
            "idreferenciaestacion": 5,
        }

        # Act
        result = service.registrar(payload, idusuario=2)
        stored = next(
            a for a in pinot_store["Fact_Accidente"] if a["idaccidente"] == result["idaccidente"]
        )

        # Assert
        assert stored["idtiporeportado"] == 2
        assert stored["idreferenciaestacion"] == 5
