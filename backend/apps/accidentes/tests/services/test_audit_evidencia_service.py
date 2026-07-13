import logging

import pytest

from apps.accidentes.services.audit_evidencia_service import AuditEvidenciaService


@pytest.mark.service
class TestAuditEvidenciaService:
    def test_log_captura_foto_emits_structured_log(self, caplog):
        # Arrange
        service = AuditEvidenciaService()

        # Act
        with caplog.at_level(logging.INFO, logger="tsi.evidencia.audit"):
            service.log_captura_foto(
                user_id=7,
                idaccidente="ACC-1",
                idevidenciafoto=99,
            )

        # Assert
        assert any("evidencia_audit" in r.message for r in caplog.records)

    def test_log_cambio_disponibilidad_emits_structured_log(self, caplog):
        # Arrange
        service = AuditEvidenciaService()

        # Act
        with caplog.at_level(logging.INFO, logger="tsi.evidencia.audit"):
            service.log_cambio_disponibilidad(
                user_id=6,
                idunidademergencia=1,
                estadoanterior="Activa",
                estadonuevo="Ocupada",
            )

        # Assert
        assert any("evidencia_audit" in r.message for r in caplog.records)
