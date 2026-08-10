"""T104 — Reasignación O63 agotada notifica Administrador (CA-DES-007)."""

from unittest.mock import MagicMock

import pytest

from apps.despacho.services.alerta_admin_service import AlertaAdminService
from apps.despacho.services.reasignacion_despacho_service import (
    ReasignacionDespachoService,
)
from core.notificaciones.email_sender import EmailSendError


@pytest.mark.service
class TestReasignacionAlertaAdmin:
    def test_ejecutar_when_no_units_notifies_admin(
        self, mock_pinot, mock_kafka, accidente_activo
    ):
        # Arrange
        mock_sender = MagicMock()
        alerta = AlertaAdminService(sender=mock_sender)
        svc = ReasignacionDespachoService(alerta_admin=alerta)

        # Act
        result = svc.ejecutar(
            idaccidente=accidente_activo, incluir_vecinos=True, idusuario=2
        )

        # Assert
        assert result.get("alerta") is True
        assert result["reasignacion_iniciada"] is False
        notas = [m for m in mock_kafka if m["payload"].get("tipo") == "escalamiento_fallido"]
        assert len(notas) >= 1
        mock_sender.send.assert_called()
        call_kwargs = mock_sender.send.call_args.kwargs
        assert call_kwargs["gmail"] == "admin@tsi.com"
        assert "reasignacion_agotamiento" in call_kwargs["body"] or accidente_activo in (
            call_kwargs["subject"]
        )

    def test_alerta_critica_when_smtp_fails_still_creates_nota(
        self, mock_pinot, mock_kafka, accidente_activo
    ):
        # Arrange
        mock_sender = MagicMock()
        mock_sender.send.side_effect = EmailSendError("smtp down")
        alerta = AlertaAdminService(sender=mock_sender)
        svc = ReasignacionDespachoService(alerta_admin=alerta)

        # Act
        result = svc.ejecutar(
            idaccidente=accidente_activo, incluir_vecinos=True, idusuario=2
        )

        # Assert — fail-open
        assert result.get("alerta") is True
        assert any(m["payload"].get("tipo") == "escalamiento_fallido" for m in mock_kafka)
