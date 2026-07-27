"""T103 — Escalamiento O34 sin candidatas notifica Administrador (CA-DES-011)."""

from unittest.mock import MagicMock

import pytest

from apps.despacho.services.alerta_admin_service import AlertaAdminService
from apps.despacho.services.escalamiento_zona_service import EscalamientoZonaService
from core.notificaciones.email_sender import EmailSendError


@pytest.mark.service
class TestEscalamientoZonaAlertaAdmin:
    def test_escalar_when_no_candidatas_creates_nota_and_notifies_admin(
        self, mock_pinot, mock_kafka, accidente_activo
    ):
        # Arrange
        mock_sender = MagicMock()
        alerta = AlertaAdminService(sender=mock_sender)
        svc = EscalamientoZonaService(alerta_admin=alerta)

        # Act
        result = svc.escalar(idaccidente=accidente_activo, idusuario=2)

        # Assert
        assert result["alerta_registrada"] is True
        notas = [
            m
            for m in mock_kafka
            if "NotaAccidente" in m["topic"] or m["payload"].get("tipo") == "escalamiento"
        ]
        assert any(m["payload"].get("tipo") == "escalamiento" for m in notas)
        mock_sender.send.assert_called()
        call_kwargs = mock_sender.send.call_args.kwargs
        assert call_kwargs["gmail"] == "admin@tsi.com"
        assert accidente_activo in call_kwargs["subject"]
        assert call_kwargs["event"] == "despacho_alerta_sin_unidades"

    def test_escalar_when_smtp_fails_still_registers_alerta(
        self, mock_pinot, mock_kafka, accidente_activo
    ):
        # Arrange
        mock_sender = MagicMock()
        mock_sender.send.side_effect = EmailSendError("smtp down")
        alerta = AlertaAdminService(sender=mock_sender)
        svc = EscalamientoZonaService(alerta_admin=alerta)

        # Act
        result = svc.escalar(idaccidente=accidente_activo, idusuario=2)

        # Assert — fail-open: nota/alerta no se interrumpe por SMTP
        assert result["alerta_registrada"] is True
        mock_sender.send.assert_called()
