"""Avisos del onboarding (research.md Decision 11).

Lo que de verdad hay que probar aqui es el comportamiento fail-open: que un
buzon caido no tumbe una promocion ya aprobada. Un test que solo comprobara
«se envio el correo» dejaria sin cubrir justo el caso que importa.
"""

from __future__ import annotations

import pytest

from apps.partners.services.partner_notificacion_service import (
    PartnerNotificacionService,
)
from core.notificaciones.email_sender import EmailSendError

pytestmark = [pytest.mark.unit]

PARTNER = {
    "idpartner": 7,
    "idcliente": 100,
    "nombrepartner": "Aseguradora Norte",
    "contacto_tecnico_nombre": "Ana Torres",
    "contacto_tecnico_gmail": "ana@norte.com",
}


class _SenderEspia:
    def __init__(self, excepcion: Exception | None = None):
        self.excepcion = excepcion
        self.enviados: list[dict] = []

    def send(self, **kwargs):
        self.enviados.append(kwargs)
        if self.excepcion:
            raise self.excepcion


class _Roles:
    def __init__(self, ids=(1, 2), excepcion=None):
        self._ids = ids
        self._excepcion = excepcion

    def list_user_ids_for_role(self, rol):
        if self._excepcion:
            raise self._excepcion
        return list(self._ids)


class _Usuarios:
    def __init__(self, usuarios=None):
        self._usuarios = usuarios or {
            1: {"idusuario": 1, "gmail": "admin1@tsi.com", "activo": True},
            2: {"idusuario": 2, "gmail": "admin2@tsi.com", "activo": True},
        }

    def find_by_id(self, uid):
        return self._usuarios.get(uid)


def _servicio(sender=None, roles=None, usuarios=None):
    return PartnerNotificacionService(
        sender=sender or _SenderEspia(),
        role_repo=roles or _Roles(),
        user_repo=usuarios or _Usuarios(),
    )


class TestAvisosAlContactoTecnico:
    def test_notificar_aprobacion_va_al_contacto_tecnico(self):
        # Arrange
        sender = _SenderEspia()

        # Act
        enviados = _servicio(sender).notificar_aprobacion(
            partner=PARTNER, nombre_credencial="produccion-siniestros"
        )

        # Assert
        assert enviados == 1
        assert sender.enviados[0]["gmail"] == "ana@norte.com"

    def test_notificar_rechazo_incluye_el_motivo(self):
        """RN-PON-007 — sin el motivo en el cuerpo, el aviso es inaccionable."""
        # Arrange
        sender = _SenderEspia()

        # Act
        _servicio(sender).notificar_rechazo(
            partner=PARTNER, motivo="Faltan pruebas de carga"
        )

        # Assert
        assert "Faltan pruebas de carga" in sender.enviados[0]["body"]

    def test_ningun_aviso_lleva_el_secreto(self):
        """El correo no es un canal seguro: el secreto solo se muestra en el portal."""
        # Arrange
        sender = _SenderEspia()
        servicio = _servicio(sender)

        # Act
        servicio.notificar_aprobacion(partner=PARTNER, nombre_credencial="prod")
        servicio.notificar_credencial_emitida(
            partner=PARTNER, nombre_credencial="prod", entorno="Sandbox"
        )

        # Assert
        for enviado in sender.enviados:
            cuerpo = enviado["body"].lower()
            assert "client_secret" not in cuerpo
            assert "secreto:" not in cuerpo

    def test_notificar_proximo_vencimiento_dice_cuantos_dias_quedan(self):
        # Arrange
        sender = _SenderEspia()

        # Act
        _servicio(sender).notificar_proximo_vencimiento(
            partner=PARTNER, nombre_credencial="pruebas", dias_restantes=10
        )

        # Assert
        assert "10 días" in sender.enviados[0]["subject"]

    def test_notificar_vencimiento_envia_al_contacto(self):
        # Arrange
        sender = _SenderEspia()

        # Act
        enviados = _servicio(sender).notificar_vencimiento(
            partner=PARTNER, nombre_credencial="pruebas"
        )

        # Assert
        assert enviados == 1


class TestFailOpen:
    def test_smtp_caido_no_propaga_la_excepcion(self):
        """Una promocion aprobada no puede deshacerse porque el correo falle:
        el estado autoritativo esta en la bitacora, no en el buzon."""
        # Arrange
        sender = _SenderEspia(EmailSendError("SMTP no configurado"))

        # Act — no lanza
        enviados = _servicio(sender).notificar_aprobacion(
            partner=PARTNER, nombre_credencial="prod"
        )

        # Assert
        assert enviados == 0

    def test_error_inesperado_tampoco_propaga(self):
        # Arrange
        sender = _SenderEspia(RuntimeError("fallo raro del transporte"))

        # Act / Assert — no lanza
        assert _servicio(sender).notificar_rechazo(partner=PARTNER, motivo="x") == 0

    def test_partner_sin_contacto_tecnico_no_revienta(self):
        """El campo es obligatorio en el esquema, pero un dato historico podria
        no tenerlo; el aviso se omite en vez de abortar la operacion."""
        # Arrange
        sender = _SenderEspia()

        # Act
        enviados = _servicio(sender).notificar_aprobacion(
            partner={**PARTNER, "contacto_tecnico_gmail": ""}, nombre_credencial="prod"
        )

        # Assert
        assert enviados == 0
        assert sender.enviados == []


class TestAvisoALosAdministradores:
    def test_solicitud_pendiente_avisa_a_todos_los_administradores(self):
        """RF-PON-007 — la aprobacion es humana: alguien tiene que enterarse."""
        # Arrange
        sender = _SenderEspia()

        # Act
        enviados = _servicio(sender).notificar_solicitud_pendiente(
            partner=PARTNER, nombre_credencial="produccion-siniestros"
        )

        # Assert
        assert enviados == 2
        assert {e["gmail"] for e in sender.enviados} == {
            "admin1@tsi.com",
            "admin2@tsi.com",
        }

    def test_el_aviso_identifica_al_partner_y_su_contacto(self):
        # Arrange
        sender = _SenderEspia()

        # Act
        _servicio(sender).notificar_solicitud_pendiente(
            partner=PARTNER, nombre_credencial="produccion-siniestros"
        )

        # Assert
        cuerpo = sender.enviados[0]["body"]
        assert "Aseguradora Norte" in cuerpo
        assert "ana@norte.com" in cuerpo

    def test_administrador_sin_gmail_se_omite(self):
        # Arrange
        sender = _SenderEspia()
        usuarios = _Usuarios(
            {
                1: {"idusuario": 1, "gmail": "admin1@tsi.com", "activo": True},
                2: {"idusuario": 2, "gmail": "", "activo": True},
            }
        )

        # Act
        enviados = _servicio(sender, usuarios=usuarios).notificar_solicitud_pendiente(
            partner=PARTNER, nombre_credencial="x"
        )

        # Assert
        assert enviados == 1

    def test_administrador_inactivo_no_recibe(self):
        # Arrange
        sender = _SenderEspia()
        usuarios = _Usuarios(
            {
                1: {"idusuario": 1, "gmail": "admin1@tsi.com", "activo": True},
                2: {"idusuario": 2, "gmail": "baja@tsi.com", "activo": False},
            }
        )

        # Act
        enviados = _servicio(sender, usuarios=usuarios).notificar_solicitud_pendiente(
            partner=PARTNER, nombre_credencial="x"
        )

        # Assert
        assert enviados == 1

    def test_fallo_resolviendo_administradores_no_propaga(self):
        # Arrange
        roles = _Roles(excepcion=RuntimeError("Pinot caido"))

        # Act — no lanza
        enviados = _servicio(roles=roles).notificar_solicitud_pendiente(
            partner=PARTNER, nombre_credencial="x"
        )

        # Assert
        assert enviados == 0
