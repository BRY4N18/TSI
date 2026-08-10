"""RF-PON-001 y RF-PON-002 — registro del partner (CU-O48)."""

from __future__ import annotations

import json

import pytest

from apps.partners.domain_constants import (
    CAMBIO_REGISTRO,
    ESTADO_REGISTRADO,
    SIN_CUPO,
    SIN_PLAN,
    SIN_SUSPENSION,
)
from apps.partners.services.registro_partner_service import (
    RegistroPartnerError,
    RegistroPartnerService,
)
from conftest import PINOT_STORE

pytestmark = [pytest.mark.django_db, pytest.mark.service]

LIMITES = json.dumps(
    {"unidades_max": 5, "usuarios_max": 3, "api_calls_mes": 1000, "api_calls_minuto": 30}
)


@pytest.fixture
def cliente_con_suscripcion(mock_pinot, mock_kafka):
    """Cliente 1 con suscripcion activa sobre el plan 1."""
    PINOT_STORE["Dim_Cliente"].append({"idcliente": 1, "nombre": "Aseguradora Demo"})
    PINOT_STORE["Dim_Plan"].append(
        {"idplan": 1, "nombre": "Básico", "limites": LIMITES, "activo": True}
    )
    PINOT_STORE["Fact_Suscripcion"].append(
        {
            "id_suscripcion": 1,
            "idcliente": 1,
            "idplan": 1,
            "estado": "Activa",
            "activo": True,
            "fecha_inicio": 1,
        }
    )
    return 1


class TestRegistroExitoso:
    def test_registrar_when_cliente_valido_crea_partner_sin_plan(self, cliente_con_suscripcion):
        # Arrange
        servicio = RegistroPartnerService()

        # Act
        partner = servicio.registrar(
            idcliente=1,
            nombrepartner="Aseguradora Demo",
            contacto_tecnico_nombre="Ana Torres",
            contacto_tecnico_gmail="ana@demo.com",
            ejecutado_por="Administrador",
        )

        # Assert — RF-PON-001: nace SIN plan ni cupo
        assert partner["estado"] == ESTADO_REGISTRADO
        assert partner["activo"] is True
        assert partner["planapi"] == SIN_PLAN
        assert partner["limitellamadasmes"] == SIN_CUPO
        assert partner["limitellamadasminuto"] == SIN_CUPO

    def test_registrar_when_valido_usa_centinelas_no_none(self, cliente_con_suscripcion):
        """Pinot no almacena NULL: publicar None romperia las guardas del modulo."""
        # Arrange
        servicio = RegistroPartnerService()

        # Act
        partner = servicio.registrar(
            idcliente=1,
            nombrepartner="Demo",
            contacto_tecnico_nombre="Ana",
            contacto_tecnico_gmail="ana@demo.com",
            ejecutado_por="Administrador",
        )

        # Assert — ningun campo se publica como None
        assert None not in partner.values()
        assert partner["fecha_suspension"] == SIN_SUSPENSION
        assert partner["motivo_suspension"] == SIN_SUSPENSION

    def test_registrar_when_valido_escribe_bitacora(self, cliente_con_suscripcion):
        # Arrange
        servicio = RegistroPartnerService()

        # Act
        servicio.registrar(
            idcliente=1,
            nombrepartner="Demo",
            contacto_tecnico_nombre="Ana",
            contacto_tecnico_gmail="ana@demo.com",
            ejecutado_por="Administrador",
        )

        # Assert
        eventos = PINOT_STORE["Fact_HistorialAccesoPartner"]
        assert len(eventos) == 1
        assert eventos[0]["tipo_cambio"] == CAMBIO_REGISTRO
        assert eventos[0]["estado_nuevo"] == ESTADO_REGISTRADO


class TestRegistroRechazado:
    def test_registrar_when_cliente_inexistente_raises_not_found(self, mock_pinot, mock_kafka):
        # Arrange
        servicio = RegistroPartnerService()

        # Act / Assert
        with pytest.raises(RegistroPartnerError) as exc:
            servicio.registrar(
                idcliente=9999,
                nombrepartner="Fantasma",
                contacto_tecnico_nombre="Nadie",
                contacto_tecnico_gmail="nadie@demo.com",
                ejecutado_por="Administrador",
            )
        assert exc.value.code == "not_found"
        # Y no escribio nada
        assert PINOT_STORE["Dim_Partner"] == []

    def test_registrar_when_sin_suscripcion_vigente_raises(self, mock_pinot, mock_kafka):
        """RN-PON-011 — el cupo se deriva de la suscripcion; sin ella no hay alta."""
        # Arrange
        PINOT_STORE["Dim_Cliente"].append({"idcliente": 7, "nombre": "Sin plan"})
        servicio = RegistroPartnerService()

        # Act / Assert
        with pytest.raises(RegistroPartnerError) as exc:
            servicio.registrar(
                idcliente=7,
                nombrepartner="Sin plan",
                contacto_tecnico_nombre="Ana",
                contacto_tecnico_gmail="ana@demo.com",
                ejecutado_por="Administrador",
            )
        assert exc.value.code == "sin_suscripcion"
        assert PINOT_STORE["Dim_Partner"] == []

    def test_registrar_when_segundo_partner_raises_duplicado_con_id_existente(
        self, cliente_con_suscripcion
    ):
        """RN-PON-002 — relacion 1:1 estricta cliente <-> partner."""
        # Arrange
        servicio = RegistroPartnerService()
        primero = servicio.registrar(
            idcliente=1,
            nombrepartner="Primero",
            contacto_tecnico_nombre="Ana",
            contacto_tecnico_gmail="ana@demo.com",
            ejecutado_por="Administrador",
        )
        filas_antes = len(PINOT_STORE["Dim_Partner"])

        # Act / Assert
        with pytest.raises(RegistroPartnerError) as exc:
            servicio.registrar(
                idcliente=1,
                nombrepartner="Segundo",
                contacto_tecnico_nombre="Luis",
                contacto_tecnico_gmail="luis@demo.com",
                ejecutado_por="Administrador",
            )
        assert exc.value.code == "partner_duplicado"
        # La respuesta indica cual es el existente, para poder actuar sobre el
        assert exc.value.extra["idpartner_existente"] == primero["idpartner"]
        # Y no se escribio un segundo partner
        assert len(PINOT_STORE["Dim_Partner"]) == filas_antes

    def test_registrar_when_gmail_invalido_raises_validation(self, cliente_con_suscripcion):
        # Arrange
        servicio = RegistroPartnerService()

        # Act / Assert
        with pytest.raises(RegistroPartnerError) as exc:
            servicio.registrar(
                idcliente=1,
                nombrepartner="Demo",
                contacto_tecnico_nombre="Ana",
                contacto_tecnico_gmail="no-es-un-correo",
                ejecutado_por="Administrador",
            )
        assert exc.value.code == "validation_error"
