"""RNF-PON-002 — el secreto no se escapa por ningun canal (escenario G).

Automatiza lo que el quickstart dejaba como revision manual. Una revision
manual detecta la fuga el dia que alguien la busca; este test la detecta el
dia que alguien la introduce.

Se vigilan los tres canales por los que un secreto se escapa de verdad:
los logs, el evento publicado y la auditoria.
"""

from __future__ import annotations

import json
import logging

import pytest

from apps.partners.services.audit_partner_service import AuditPartnerService
from apps.partners.services.emitir_credencial_service import EmitirCredencialService
from conftest import PINOT_STORE

pytestmark = [pytest.mark.django_db, pytest.mark.service]

ID_PARTNER = 950
ID_CLIENTE = 950


@pytest.fixture
def partner_con_plan(mock_pinot, mock_kafka):
    PINOT_STORE["Dim_Partner"].append(
        {
            "idpartner": ID_PARTNER,
            "idcliente": ID_CLIENTE,
            "nombrepartner": "Demo Fuga",
            "contacto_tecnico_nombre": "Ana",
            "contacto_tecnico_gmail": "ana@demo.com",
            "planapi": "Profesional",
            "limitellamadasmes": 10000,
            "limitellamadasminuto": 120,
            "sandbox_activado": 0,
            "sandbox_expiracion": 0,
            "fecha_suspension": "",
            "motivo_suspension": "",
            "activo": True,
            "fecha_actualizacion": 1,
        }
    )
    return ID_PARTNER


class TestElSecretoNoApareceEnLosLogs:
    def test_emitir_no_escribe_el_secreto_en_ningun_log(
        self, partner_con_plan, mock_pinot, mock_kafka, caplog
    ):
        """Se capturan TODOS los logs, no solo los del modulo.

        Acotar la captura a `tsi.partners` dejaria pasar una fuga desde el
        cliente de Pinot o desde el writer de Kafka, que es justo donde el
        secreto pasa mas cerca de una llamada a logging.
        """
        # Arrange
        caplog.set_level(logging.DEBUG)

        # Act
        credencial = EmitirCredencialService().emitir(
            idpartner=ID_PARTNER,
            nombre_credencial="plataforma-siniestros",
            ejecutado_por="Partner",
        )

        # Assert
        assert credencial["client_secret"]  # se emitio de verdad
        assert credencial["client_secret"] not in caplog.text


class TestElSecretoNoApareceEnLoPersistido:
    def test_emitir_no_publica_el_secreto_en_ninguna_tabla(
        self, partner_con_plan, mock_pinot, mock_kafka
    ):
        # Act
        credencial = EmitirCredencialService().emitir(
            idpartner=ID_PARTNER, nombre_credencial="sistema-b", ejecutado_por="Partner"
        )

        # Assert — se revisa TODO el almacen, no solo la tabla esperada
        todo = json.dumps(
            {k: v for k, v in PINOT_STORE.items() if v}, default=str
        )
        assert credencial["client_secret"] not in todo

    def test_solo_se_persiste_el_hash_y_verifica(
        self, partner_con_plan, mock_pinot, mock_kafka
    ):
        """El hash debe ser util (verifica) y no reversible (no es el secreto)."""
        # Arrange
        from apps.partners.services.secreto_service import SecretoService

        # Act
        credencial = EmitirCredencialService().emitir(
            idpartner=ID_PARTNER, nombre_credencial="sistema-c", ejecutado_por="Partner"
        )
        fila = next(
            c
            for c in PINOT_STORE["Dim_CredencialAPI"]
            if c["idcredencial"] == credencial["idcredencial"]
        )

        # Assert
        assert fila["client_secret_hash"] != credencial["client_secret"]
        assert SecretoService().verificar(
            credencial["client_secret"], fila["client_secret_hash"]
        )


class TestLaAuditoriaSaneaAunqueLeDenElSecreto:
    def test_auditar_con_client_secret_lo_redacta(self, caplog):
        """La garantia no es «no se lo pases»: es que aunque se lo pasen, no sale."""
        # Arrange
        caplog.set_level(logging.INFO)

        # Act
        entrada = AuditPartnerService().registrar_accion(
            accion="emision_credencial",
            idpartner=1,
            idusuario=51,
            campos={"client_secret": "SECRETO-FILTRADO", "nombre_credencial": "x"},
        )

        # Assert
        assert entrada["campos"]["client_secret"] == "***"
        assert "SECRETO-FILTRADO" not in caplog.text
        assert entrada["campos"]["nombre_credencial"] == "x"

    def test_auditar_redacta_tambien_en_estructuras_anidadas(self):
        """`**credencial` dentro de un dict anidado es el descuido tipico."""
        # Act
        entrada = AuditPartnerService().registrar_accion(
            accion="emision_credencial",
            idpartner=1,
            idusuario=51,
            campos={"credencial": {"client_secret": "OTRO-SECRETO", "entorno": "Sandbox"}},
        )

        # Assert
        assert entrada["campos"]["credencial"]["client_secret"] == "***"
        assert entrada["campos"]["credencial"]["entorno"] == "Sandbox"

    def test_auditar_redacta_el_hash_tambien(self):
        """El hash no es publico: revelarlo permite atacarlo sin limite de tasa."""
        # Act
        entrada = AuditPartnerService().registrar_accion(
            accion="emision_credencial",
            idpartner=1,
            idusuario=51,
            campos={"client_secret_hash": "$2b$12$loquesea"},
        )

        # Assert
        assert entrada["campos"]["client_secret_hash"] == "***"
