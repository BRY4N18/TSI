"""RF-PON-004 y RF-PON-005 — emision de credenciales nombradas (CU-O49).

Incluye los tests de SEGURIDAD del modulo: el secreto se entrega una sola vez,
nunca se persiste en claro y nunca viaja al evento Kafka.
"""

from __future__ import annotations

import json

import pytest

from apps.partners.domain_constants import (
    CAMBIO_ACTIVACION_SANDBOX,
    ENTORNO_PRODUCCION,
    ENTORNO_SANDBOX,
    ESTADO_PRUEBAS_ACTIVO,
    NUNCA_EXPIRA,
    SIN_PLAN,
)
from apps.partners.services.emitir_credencial_service import (
    EmitirCredencialError,
    EmitirCredencialService,
)
from apps.partners.services.secreto_service import SecretoService
from conftest import PINOT_STORE

pytestmark = [pytest.mark.django_db, pytest.mark.service]

ID_PARTNER = 903
ID_CLIENTE = 903


def _partner(*, planapi: str = "Profesional", activo: bool = True) -> None:
    PINOT_STORE["Dim_Partner"].append(
        {
            "idpartner": ID_PARTNER,
            "idcliente": ID_CLIENTE,
            "nombrepartner": "Demo",
            "contacto_tecnico_nombre": "Ana",
            "contacto_tecnico_gmail": "ana@demo.com",
            "planapi": planapi,
            "limitellamadasmes": 10000,
            "limitellamadasminuto": 120,
            "sandbox_activado": 0,
            "sandbox_expiracion": 0,
            "fecha_suspension": "",
            "motivo_suspension": "",
            "activo": activo,
            "fecha_actualizacion": 1,
        }
    )


class TestEmisionExitosa:
    def test_emitir_when_partner_con_plan_devuelve_secreto_una_vez(self, mock_pinot, mock_kafka):
        # Arrange
        _partner()

        # Act
        cred = EmitirCredencialService().emitir(
            idpartner=ID_PARTNER,
            nombre_credencial="plataforma-siniestros",
            ejecutado_por="Partner",
        )

        # Assert
        assert cred["estado"] == ESTADO_PRUEBAS_ACTIVO
        assert cred["nombre_credencial"] == "plataforma-siniestros"
        assert cred["entorno"] == ENTORNO_SANDBOX
        assert cred["client_secret"]  # se entrega en claro, esta unica vez
        assert "client_secret_hash" not in cred  # el hash no se expone

    def test_emitir_when_exitosa_persiste_solo_el_hash(self, mock_pinot, mock_kafka):
        """RNF-PON-002 — el secreto en claro NO se persiste."""
        # Arrange
        _partner()

        # Act
        cred = EmitirCredencialService().emitir(
            idpartner=ID_PARTNER, nombre_credencial="sistema-a", ejecutado_por="Partner"
        )

        # Assert — la fila almacenada lleva hash, no el secreto
        fila = PINOT_STORE["Dim_CredencialAPI"][-1]
        assert fila["client_secret_hash"] != cred["client_secret"]
        assert fila["client_secret_hash"].startswith("$2b$")
        # y el hash verifica contra el secreto entregado
        assert SecretoService().verificar(cred["client_secret"], fila["client_secret_hash"])

    def test_emitir_when_exitosa_el_secreto_no_viaja_al_evento_kafka(
        self, mock_pinot, mock_kafka
    ):
        """El evento publicado no puede contener el secreto en claro.

        Es facil de violar por accidente al depurar, asi que se comprueba sobre
        el payload serializado completo.
        """
        # Arrange
        _partner()

        # Act
        cred = EmitirCredencialService().emitir(
            idpartner=ID_PARTNER, nombre_credencial="sistema-b", ejecutado_por="Partner"
        )

        # Assert — el secreto no aparece en NINGUN evento publicado
        todo_lo_publicado = json.dumps(
            [PINOT_STORE["Dim_CredencialAPI"], PINOT_STORE["Fact_HistorialAccesoPartner"]]
        )
        assert cred["client_secret"] not in todo_lo_publicado

    def test_emitir_when_sandbox_tiene_vigencia_finita(self, mock_pinot, mock_kafka):
        # Arrange
        _partner()

        # Act
        cred = EmitirCredencialService().emitir(
            idpartner=ID_PARTNER, nombre_credencial="pruebas", ejecutado_por="Partner"
        )

        # Assert — pruebas caduca; no lleva el centinela de "no expira"
        assert cred["fecha_expiracion"] != NUNCA_EXPIRA
        assert cred["fecha_expiracion"] > 0

    def test_emitir_when_produccion_no_expira_nunca(self, mock_pinot, mock_kafka):
        """RF-PON-008 — el centinela esta en el FUTURO para que ningun job la alcance."""
        # Arrange
        _partner()

        # Act
        cred = EmitirCredencialService().emitir(
            idpartner=ID_PARTNER,
            nombre_credencial="produccion",
            entorno=ENTORNO_PRODUCCION,
            ejecutado_por="Administrador",
        )

        # Assert
        assert cred["fecha_expiracion"] == NUNCA_EXPIRA

    def test_emitir_when_varias_nombradas_conviven_en_el_mismo_entorno(
        self, mock_pinot, mock_kafka
    ):
        """RF-PON-005 — una aseguradora integra siniestros y fraude por separado."""
        # Arrange
        _partner()
        servicio = EmitirCredencialService()

        # Act
        servicio.emitir(
            idpartner=ID_PARTNER,
            nombre_credencial="plataforma-siniestros",
            ejecutado_por="Partner",
        )
        servicio.emitir(
            idpartner=ID_PARTNER, nombre_credencial="deteccion-fraude", ejecutado_por="Partner"
        )

        # Assert
        activas = [
            c
            for c in PINOT_STORE["Dim_CredencialAPI"]
            if c["idpartner"] == ID_PARTNER and c["activo"]
        ]
        assert {c["nombre_credencial"] for c in activas} == {
            "plataforma-siniestros",
            "deteccion-fraude",
        }

    def test_emitir_when_primera_activacion_guarda_snapshot_en_partner(
        self, mock_pinot, mock_kafka
    ):
        # Arrange
        _partner()

        # Act
        EmitirCredencialService().emitir(
            idpartner=ID_PARTNER, nombre_credencial="primera", ejecutado_por="Partner"
        )

        # Assert
        partner = next(
            p for p in PINOT_STORE["Dim_Partner"] if p["idpartner"] == ID_PARTNER
        )
        assert partner["sandbox_activado"] > 0

    def test_emitir_when_exitosa_escribe_bitacora_con_idcredencial(self, mock_pinot, mock_kafka):
        # Arrange
        _partner()

        # Act
        cred = EmitirCredencialService().emitir(
            idpartner=ID_PARTNER, nombre_credencial="x", ejecutado_por="Partner"
        )

        # Assert — el evento apunta a la credencial concreta, no al centinela -1
        evento = PINOT_STORE["Fact_HistorialAccesoPartner"][-1]
        assert evento["tipo_cambio"] == CAMBIO_ACTIVACION_SANDBOX
        assert evento["idcredencial"] == cred["idcredencial"]


class TestEmisionRechazada:
    def test_emitir_when_sin_plan_raises_y_no_escribe_nada(self, mock_pinot, mock_kafka):
        """RF-PON-004 — la guarda compara contra el CENTINELA, no contra None.

        Con el centinela implicito de Pinot ('null') esta condicion habria sido
        siempre falsa y un partner sin plan podria emitir credenciales.
        """
        # Arrange
        _partner(planapi=SIN_PLAN)

        # Act / Assert
        with pytest.raises(EmitirCredencialError) as exc:
            EmitirCredencialService().emitir(
                idpartner=ID_PARTNER, nombre_credencial="x", ejecutado_por="Partner"
            )
        assert exc.value.code == "sin_plan"
        assert PINOT_STORE["Dim_CredencialAPI"] == []
        assert PINOT_STORE["Fact_HistorialAccesoPartner"] == []

    def test_emitir_when_nombre_duplicado_entre_activas_raises(self, mock_pinot, mock_kafka):
        # Arrange
        _partner()
        servicio = EmitirCredencialService()
        servicio.emitir(idpartner=ID_PARTNER, nombre_credencial="repe", ejecutado_por="Partner")

        # Act / Assert
        with pytest.raises(EmitirCredencialError) as exc:
            servicio.emitir(
                idpartner=ID_PARTNER, nombre_credencial="repe", ejecutado_por="Partner"
            )
        assert exc.value.code == "nombre_duplicado"

    def test_emitir_when_nombre_liberado_puede_reutilizarse(self, mock_pinot, mock_kafka):
        """RN-PON-014 — la unicidad es solo entre ACTIVAS."""
        # Arrange
        _partner()
        servicio = EmitirCredencialService()
        primera = servicio.emitir(
            idpartner=ID_PARTNER, nombre_credencial="rotable", ejecutado_por="Partner"
        )
        # se revoca (desactiva), liberando el nombre
        for c in PINOT_STORE["Dim_CredencialAPI"]:
            if c["idcredencial"] == primera["idcredencial"]:
                c["activo"] = False

        # Act
        segunda = servicio.emitir(
            idpartner=ID_PARTNER, nombre_credencial="rotable", ejecutado_por="Partner"
        )

        # Assert
        assert segunda["nombre_credencial"] == "rotable"
        assert segunda["idcredencial"] != primera["idcredencial"]

    def test_emitir_when_nombre_vacio_raises_validation(self, mock_pinot, mock_kafka):
        # Arrange
        _partner()

        # Act / Assert
        with pytest.raises(EmitirCredencialError) as exc:
            EmitirCredencialService().emitir(
                idpartner=ID_PARTNER, nombre_credencial="   ", ejecutado_por="Partner"
            )
        assert exc.value.code == "validation_error"

    def test_emitir_when_partner_suspendido_raises(self, mock_pinot, mock_kafka):
        # Arrange
        _partner(activo=False)

        # Act / Assert
        with pytest.raises(EmitirCredencialError) as exc:
            EmitirCredencialService().emitir(
                idpartner=ID_PARTNER, nombre_credencial="x", ejecutado_por="Partner"
            )
        assert exc.value.code == "partner_suspendido"


class TestSecretoIrrecuperable:
    def test_secretos_generados_son_distintos_entre_si(self, mock_pinot, mock_kafka):
        # Arrange
        _partner()
        servicio = EmitirCredencialService()

        # Act
        a = servicio.emitir(idpartner=ID_PARTNER, nombre_credencial="a", ejecutado_por="Partner")
        b = servicio.emitir(idpartner=ID_PARTNER, nombre_credencial="b", ejecutado_por="Partner")

        # Assert
        assert a["client_secret"] != b["client_secret"]

    def test_secreto_tiene_entropia_suficiente(self, mock_pinot, mock_kafka):
        """RNF-PON-002 — >= 32 bytes de entropia (token_urlsafe da ~43 chars)."""
        # Arrange
        _partner()

        # Act
        cred = EmitirCredencialService().emitir(
            idpartner=ID_PARTNER, nombre_credencial="x", ejecutado_por="Partner"
        )

        # Assert
        assert len(cred["client_secret"]) >= 40
