"""RF-PON-007 y RF-PON-008 — promocion a produccion (CU-O49)."""

from __future__ import annotations

import pytest

from apps.partners.domain_constants import (
    CAMBIO_ACTIVACION_SANDBOX,
    CAMBIO_RECHAZO_PRODUCCION,
    CAMBIO_SOLICITUD_PRODUCCION,
    ENTORNO_PRODUCCION,
    ENTORNO_SANDBOX,
    ESTADO_PENDIENTE_APROBACION,
    ESTADO_PRODUCCION_ACTIVA,
    ESTADO_PRUEBAS_ACTIVO,
    NUNCA_EXPIRA,
)
from apps.partners.services.emitir_credencial_service import EmitirCredencialService
from apps.partners.services.promocion_produccion_service import (
    PromocionProduccionError,
    PromocionProduccionService,
)
from conftest import PINOT_STORE

pytestmark = [pytest.mark.django_db, pytest.mark.service]

ID_PARTNER = 906


def _partner_con_plan() -> None:
    PINOT_STORE["Dim_Partner"].append(
        {
            "idpartner": ID_PARTNER,
            "idcliente": 906,
            "nombrepartner": "Demo",
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


def _con_sandbox() -> None:
    """Partner que ya paso por el entorno de pruebas."""
    _partner_con_plan()
    EmitirCredencialService().emitir(
        idpartner=ID_PARTNER, nombre_credencial="pruebas", ejecutado_por="Partner"
    )


class TestSolicitud:
    def test_solicitar_when_pruebas_activo_returns_pendiente_sin_emitir(
        self, mock_pinot, mock_kafka
    ):
        """RF-PON-007 — la solicitud NO emite credencial."""
        # Arrange
        _con_sandbox()
        creds_antes = len(PINOT_STORE["Dim_CredencialAPI"])

        # Act
        resultado = PromocionProduccionService().solicitar(
            idpartner=ID_PARTNER, nombre_credencial="produccion-siniestros"
        )

        # Assert
        assert resultado["estado"] == ESTADO_PENDIENTE_APROBACION
        assert len(PINOT_STORE["Dim_CredencialAPI"]) == creds_antes
        assert PINOT_STORE["Fact_HistorialAccesoPartner"][-1]["tipo_cambio"] == (
            CAMBIO_SOLICITUD_PRODUCCION
        )

    def test_solicitar_when_sin_pasar_por_pruebas_raises_ruta_invalida(
        self, mock_pinot, mock_kafka
    ):
        """RN-PON-004 — ruta obligatoria, sin atajos."""
        # Arrange — con plan pero SIN credencial de pruebas
        _partner_con_plan()

        # Act / Assert
        with pytest.raises(PromocionProduccionError) as exc:
            PromocionProduccionService().solicitar(
                idpartner=ID_PARTNER, nombre_credencial="prod"
            )
        assert exc.value.code == "ruta_invalida"

    def test_solicitar_when_nombre_vacio_raises(self, mock_pinot, mock_kafka):
        # Arrange
        _con_sandbox()

        # Act / Assert
        with pytest.raises(PromocionProduccionError) as exc:
            PromocionProduccionService().solicitar(idpartner=ID_PARTNER, nombre_credencial="")
        assert exc.value.code == "validation_error"


class TestAprobacion:
    def test_aprobar_when_pendiente_emite_produccion(self, mock_pinot, mock_kafka):
        # Arrange
        _con_sandbox()
        servicio = PromocionProduccionService()
        servicio.solicitar(idpartner=ID_PARTNER, nombre_credencial="produccion-siniestros")

        # Act
        resultado = servicio.resolver(idpartner=ID_PARTNER, decision="aprobar")

        # Assert
        assert resultado["estado"] == ESTADO_PRODUCCION_ACTIVA
        cred = resultado["credencial"]
        assert cred["entorno"] == ENTORNO_PRODUCCION
        assert cred["client_secret"]  # una sola vez
        assert cred["fecha_expiracion"] == NUNCA_EXPIRA

    def test_aprobar_when_exitosa_la_credencial_de_pruebas_sigue_activa(
        self, mock_pinot, mock_kafka
    ):
        """RN-PON-008 — pruebas y produccion COEXISTEN."""
        # Arrange
        _con_sandbox()
        servicio = PromocionProduccionService()
        servicio.solicitar(idpartner=ID_PARTNER, nombre_credencial="prod")

        # Act
        servicio.resolver(idpartner=ID_PARTNER, decision="aprobar")

        # Assert
        sandbox = [
            c
            for c in PINOT_STORE["Dim_CredencialAPI"]
            if c["idpartner"] == ID_PARTNER and c["entorno"] == ENTORNO_SANDBOX
        ]
        assert sandbox and all(c["activo"] for c in sandbox)


class TestRechazo:
    def test_rechazar_when_con_motivo_vuelve_a_pruebas_activo(self, mock_pinot, mock_kafka):
        """RN-PON-007 — vuelve a «Pruebas activo», NO a «Registrado».

        Su acceso de pruebas sigue vivo porque es donde debe corregir lo que
        motivo el rechazo.
        """
        # Arrange
        _con_sandbox()
        servicio = PromocionProduccionService()
        servicio.solicitar(idpartner=ID_PARTNER, nombre_credencial="prod")

        # Act
        resultado = servicio.resolver(
            idpartner=ID_PARTNER, decision="rechazar", motivo="Falta validar el manejo de errores"
        )

        # Assert
        assert resultado["estado"] == ESTADO_PRUEBAS_ACTIVO
        assert resultado["motivo"] == "Falta validar el manejo de errores"
        evento = PINOT_STORE["Fact_HistorialAccesoPartner"][-1]
        assert evento["tipo_cambio"] == CAMBIO_RECHAZO_PRODUCCION
        assert evento["estado_nuevo"] == ESTADO_PRUEBAS_ACTIVO
        # Y su credencial de pruebas sigue operativa
        assert any(
            c["entorno"] == ENTORNO_SANDBOX and c["activo"]
            for c in PINOT_STORE["Dim_CredencialAPI"]
        )

    def test_rechazar_when_sin_motivo_raises(self, mock_pinot, mock_kafka):
        # Arrange
        _con_sandbox()
        servicio = PromocionProduccionService()
        servicio.solicitar(idpartner=ID_PARTNER, nombre_credencial="prod")

        # Act / Assert
        with pytest.raises(PromocionProduccionError) as exc:
            servicio.resolver(idpartner=ID_PARTNER, decision="rechazar", motivo="  ")
        assert exc.value.code == "motivo_requerido"

    def test_rechazar_permite_reintentar_sin_tope(self, mock_pinot, mock_kafka):
        """RN-PON-007 — no existe un tope de reintentos."""
        # Arrange
        _con_sandbox()
        servicio = PromocionProduccionService()

        # Act — tres ciclos completos de solicitud y rechazo
        for i in range(3):
            servicio.solicitar(idpartner=ID_PARTNER, nombre_credencial="prod")
            servicio.resolver(
                idpartner=ID_PARTNER, decision="rechazar", motivo=f"intento {i}"
            )

        # Y a la cuarta se aprueba
        servicio.solicitar(idpartner=ID_PARTNER, nombre_credencial="prod")
        resultado = servicio.resolver(idpartner=ID_PARTNER, decision="aprobar")

        # Assert
        assert resultado["estado"] == ESTADO_PRODUCCION_ACTIVA
        rechazos = [
            e
            for e in PINOT_STORE["Fact_HistorialAccesoPartner"]
            if e["tipo_cambio"] == CAMBIO_RECHAZO_PRODUCCION
        ]
        assert len(rechazos) == 3  # todos quedaron en la bitacora


class TestResolucionInvalida:
    def test_resolver_when_sin_solicitud_pendiente_raises(self, mock_pinot, mock_kafka):
        # Arrange
        _con_sandbox()

        # Act / Assert
        with pytest.raises(PromocionProduccionError) as exc:
            PromocionProduccionService().resolver(idpartner=ID_PARTNER, decision="aprobar")
        assert exc.value.code == "sin_solicitud_pendiente"

    def test_resolver_when_decision_invalida_raises(self, mock_pinot, mock_kafka):
        # Arrange
        _con_sandbox()
        PromocionProduccionService().solicitar(idpartner=ID_PARTNER, nombre_credencial="p")

        # Act / Assert
        with pytest.raises(PromocionProduccionError) as exc:
            PromocionProduccionService().resolver(idpartner=ID_PARTNER, decision="quizas")
        assert exc.value.code == "validation_error"
