import logging

import pytest

from apps.accidentes.services.audit_accidente_service import AuditAccidenteService


@pytest.mark.service
class TestAuditAccidenteService:
    def test_log_action_when_called_emits_info(self, caplog):
        # Arrange
        service = AuditAccidenteService()

        # Act
        with caplog.at_level(logging.INFO, logger="tsi.accidentes.audit"):
            service.log_action(action="crear", user_id=2, idaccidente="ACC-1")

        # Assert
        assert any("accidente_audit" in r.message for r in caplog.records)
