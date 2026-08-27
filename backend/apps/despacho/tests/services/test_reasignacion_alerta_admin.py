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

    def test_alerta_envia_html_y_conserva_texto_plano(
        self, mock_pinot, mock_kafka, accidente_activo
    ):
        """El correo sale como multipart: HTML maquetado + texto plano.

        El texto plano no es decorativo — es lo que llega a quien tiene el
        HTML desactivado. Si algún día el HTML sustituyera al texto en vez de
        acompañarlo, este test lo caza.
        """
        # Arrange
        mock_sender = MagicMock()
        alerta = AlertaAdminService(sender=mock_sender)
        svc = ReasignacionDespachoService(alerta_admin=alerta)

        # Act
        svc.ejecutar(idaccidente=accidente_activo, incluir_vecinos=True, idusuario=2)

        # Assert
        kwargs = mock_sender.send.call_args.kwargs
        html = kwargs["html_body"]
        assert html is not None
        # El id del caso y el enlace a la consola son lo único accionable del
        # correo; si falta cualquiera de los dos, el aviso no sirve de nada.
        assert accidente_activo in html
        assert f"/despacho/monitoreo/{accidente_activo}" in html
        # Bulletproof: sin hojas externas ni CSS moderno que el correo ignora.
        assert "<link" not in html
        assert "clip-path" not in html
        # El texto plano sigue ahí y sigue nombrando el caso.
        assert accidente_activo in kwargs["body"]

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
