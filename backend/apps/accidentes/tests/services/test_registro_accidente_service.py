import time

import pytest

from apps.accidentes.services.registro_accidente_service import RegistroAccidenteService


@pytest.mark.service
class TestRegistroAccidenteService:
    def test_registrar_when_retrospectivo_audita_justificacion(
        self, mock_pinot, mock_kafka, accidente_payload
    ):
        # Arrange — RN-REG-004/RNF-REG-004: la justificación de un registro
        # retrospectivo (>24h) debe quedar auditada, no solo validada.
        logged: dict = {}

        class SpyAudit:
            def log_action(self, **kwargs):
                logged.update(kwargs)

        service = RegistroAccidenteService(audit=SpyAudit())
        payload = {
            **accidente_payload,
            "fechahoraaccidente": int(time.time() * 1000) - 30 * 3600 * 1000,
            "registroRetrospectivo": True,
            "justificacionRetrospectiva": "Reporte recibido tarde por el cliente",
        }

        # Act
        service.registrar(payload, idusuario=2)

        # Assert
        assert logged["extra"]["registroRetrospectivo"] is True
        assert logged["extra"]["justificacionRetrospectiva"] == (
            "Reporte recibido tarde por el cliente"
        )

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
