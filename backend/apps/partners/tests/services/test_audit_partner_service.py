"""RNF-PON-004 — auditoria estructurada por accion.

El saneado se prueba aparte, en `test_no_fuga_secreto.py`; aqui se comprueba
que el rastro contiene lo que un operador necesita para reconstruir quien
hizo que.
"""

from __future__ import annotations

import logging

import pytest

from apps.partners.services.audit_partner_service import (
    REDACTADO,
    AuditPartnerService,
)

pytestmark = [pytest.mark.unit]


class TestContenidoDelRastro:
    def test_registrar_accion_incluye_actor_objeto_y_momento(self):
        # Act
        entrada = AuditPartnerService().registrar_accion(
            accion="registro_partner", idpartner=7, idusuario=51, campos={"a": 1}
        )

        # Assert
        assert entrada["accion"] == "registro_partner"
        assert entrada["idpartner"] == 7
        assert entrada["idusuario"] == 51
        assert entrada["resultado"] == "exito"
        assert entrada["timestamp"]

    def test_registrar_accion_emite_un_log(self, caplog):
        # Arrange
        caplog.set_level(logging.INFO, logger="tsi.partners.audit")

        # Act
        AuditPartnerService().registrar_accion(
            accion="registro_partner", idpartner=7, idusuario=51
        )

        # Assert
        assert "partner_audit" in caplog.text

    def test_registrar_accion_when_actor_desconocido_no_falla(self):
        """Un token sin `idusuario` resoluble no puede tumbar la operacion:
        se audita como desconocido, que es informacion util de por si."""
        # Act
        entrada = AuditPartnerService().registrar_accion(
            accion="registro_partner", idpartner=7, idusuario=None
        )

        # Assert
        assert entrada["idusuario"] is None


class TestAtajosPorCasoDeUso:
    def test_log_emision_credencial_no_admite_el_secreto_en_su_firma(self):
        """La firma solo pide identificadores: no hay por donde colar el secreto."""
        # Act
        entrada = AuditPartnerService().log_emision_credencial(
            idpartner=7, idusuario=51, idcredencial=99,
            nombre_credencial="siniestros", entorno="Sandbox",
        )

        # Assert
        assert entrada["campos"] == {
            "idcredencial": 99,
            "nombre_credencial": "siniestros",
            "entorno": "Sandbox",
        }

    def test_log_asignacion_plan_registra_el_cupo_derivado(self):
        # Act
        entrada = AuditPartnerService().log_asignacion_plan(
            idpartner=7, idusuario=51, plan="Profesional", limite_mes=10000
        )

        # Assert
        assert entrada["campos"]["planapi"] == "Profesional"
        assert entrada["campos"]["limitellamadasmes"] == 10000

    def test_log_promocion_when_rechazo_marca_el_resultado(self):
        """Aprobar y rechazar son ambos exitos operativos pero desenlaces
        distintos: el rastro debe distinguirlos sin leer el motivo."""
        # Act
        aprobado = AuditPartnerService().log_promocion(
            idpartner=7, idusuario=51, decision="aprobar"
        )
        rechazado = AuditPartnerService().log_promocion(
            idpartner=7, idusuario=51, decision="rechazar", motivo="faltan pruebas"
        )

        # Assert
        assert aprobado["resultado"] == "exito"
        assert rechazado["resultado"] == "rechazado"
        assert rechazado["campos"]["motivo"] == "faltan pruebas"

    def test_log_denegacion_registra_el_intento(self):
        """Un 403 es informacion de seguridad: importa quien lo intento."""
        # Act
        entrada = AuditPartnerService().log_denegacion(
            idpartner=7, idusuario=99, motivo="El partner no pertenece al cliente"
        )

        # Assert
        assert entrada["resultado"] == "denegado"
        assert entrada["idusuario"] == 99


class TestSaneado:
    def test_es_sensible_reconoce_las_variantes(self):
        """Se compara por subcadena para no depender de una lista exhaustiva."""
        # Act / Assert
        assert AuditPartnerService._es_sensible("client_secret") is True
        assert AuditPartnerService._es_sensible("CLIENT_SECRET_HASH") is True
        assert AuditPartnerService._es_sensible("nuevo_password") is True
        assert AuditPartnerService._es_sensible("refresh_token") is True
        assert AuditPartnerService._es_sensible("nombre_credencial") is False
        assert AuditPartnerService._es_sensible("entorno") is False

    def test_sanear_recorre_listas(self):
        # Act
        saneado = AuditPartnerService._sanear(
            [{"client_secret": "x"}, {"entorno": "Sandbox"}]
        )

        # Assert
        assert saneado[0]["client_secret"] == REDACTADO
        assert saneado[1]["entorno"] == "Sandbox"

    def test_sanear_no_altera_los_valores_inocuos(self):
        # Act
        saneado = AuditPartnerService._sanear({"idpartner": 7, "activo": True})

        # Assert
        assert saneado == {"idpartner": 7, "activo": True}
