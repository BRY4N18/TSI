"""BE-DELTA-02 — el partner emite su credencial de producción (FR-UI-027).

Antes, `POST /credenciales` con `entorno=Producción` devolvía 403 **sin
excepción**, y la credencial productiva nacía al aprobar la promoción: su
secreto acababa en manos del Administrador, que no tiene canal seguro para
entregárselo al partner. Eso empujaba el secreto a un correo o un chat, que es
justo lo que RN-PON-005 intenta evitar.

Lo que cambia es DÓNDE se comprueba la autorización, no la regla: RN-PON-004
sigue exigiendo la aprobación previa, y este archivo lo verifica.
"""

from __future__ import annotations

import pytest

from conftest import PINOT_STORE

pytestmark = [pytest.mark.django_db, pytest.mark.api]

ID_CLIENTE_DEL_PARTNER = 1
ID_PARTNER = 981


def _partner(estado_produccion: bool):
    PINOT_STORE["Dim_Partner"].append(
        {
            "idpartner": ID_PARTNER,
            "idcliente": ID_CLIENTE_DEL_PARTNER,
            "nombrepartner": "Demo Producción",
            "contacto_tecnico_nombre": "Ana",
            "contacto_tecnico_gmail": "ana@demo.com",
            "planapi": "Profesional",
            "limitellamadasmes": 10000,
            "limitellamadasminuto": 120,
            "sandbox_activado": 1,
            "sandbox_expiracion": 253402300799000,
            "fecha_suspension": "",
            "motivo_suspension": "",
            "activo": True,
            "fecha_actualizacion": 1,
        }
    )
    # Credencial de pruebas activa: la ruta valida pasa por el sandbox.
    PINOT_STORE["Dim_CredencialAPI"].append(
        {
            "idcredencial": 9810,
            "idpartner": ID_PARTNER,
            "idcliente": ID_CLIENTE_DEL_PARTNER,
            "client_secret_hash": "$2b$12$hash",
            "nombre_credencial": "pruebas",
            "entorno": "Sandbox",
            "activo": True,
            "fecha_creacion": 1,
            "fecha_expiracion": 253402300799000,
            "fecha_actualizacion": 1,
        }
    )
    if estado_produccion:
        # La aprobación ya ocurrió: existe credencial de producción activa.
        PINOT_STORE["Dim_CredencialAPI"].append(
            {
                "idcredencial": 9811,
                "idpartner": ID_PARTNER,
                "idcliente": ID_CLIENTE_DEL_PARTNER,
                "client_secret_hash": "$2b$12$hash",
                "nombre_credencial": "produccion-inicial",
                "entorno": "Producción",
                "activo": True,
                "fecha_creacion": 2,
                "fecha_expiracion": 253402300799000,
                "fecha_actualizacion": 2,
            }
        )
        PINOT_STORE["Fact_HistorialAccesoPartner"].append(
            {
                "idhistorial": 9811,
                "idpartner": ID_PARTNER,
                "idcredencial": 9811,
                "tipo_cambio": "activacion_produccion",
                "ejecutado_por": "Administrador",
                "motivo": "",
                "estado_anterior": "Pendiente de aprobación",
                "estado_nuevo": "Producción activa",
                "fecha_cambio": 20,
                "fecha_actualizacion": 20,
            }
        )
    else:
        PINOT_STORE["Fact_HistorialAccesoPartner"].append(
            {
                "idhistorial": 9810,
                "idpartner": ID_PARTNER,
                "idcredencial": 9810,
                "tipo_cambio": "activacion_sandbox",
                "ejecutado_por": "Partner",
                "motivo": "",
                "estado_anterior": "Plan asignado",
                "estado_nuevo": "Pruebas activo",
                "fecha_cambio": 10,
                "fecha_actualizacion": 10,
            }
        )
    return ID_PARTNER


def _emitir(api_client, headers, nombre="produccion-siniestros"):
    return api_client.post(
        f"/api/v1/partners/{ID_PARTNER}/credenciales",
        {"nombre_credencial": nombre, "entorno": "Producción"},
        format="json",
        **headers,
    )


class TestSinAprobacionSigueProhibido:
    def test_emitir_produccion_sin_aprobacion_returns_403(
        self, api_client, mock_pinot, mock_kafka, partner_auth_headers
    ):
        """RN-PON-004 intacta: no hay atajo a producción sin aprobación."""
        # Arrange — el partner está en «Pruebas activo»
        _partner(estado_produccion=False)

        # Act
        response = _emitir(api_client, partner_auth_headers)

        # Assert
        assert response.status_code == 403
        assert response.json()["code"] == "produccion_requiere_aprobacion"

    def test_emitir_produccion_sin_aprobacion_no_escribe_nada(
        self, api_client, mock_pinot, mock_kafka, partner_auth_headers
    ):
        # Arrange
        _partner(estado_produccion=False)
        antes = len(PINOT_STORE["Dim_CredencialAPI"])

        # Act
        _emitir(api_client, partner_auth_headers)

        # Assert
        assert len(PINOT_STORE["Dim_CredencialAPI"]) == antes


class TestConAprobacionElPartnerEmite:
    def test_emitir_produccion_tras_aprobacion_returns_201(
        self, api_client, mock_pinot, mock_kafka, partner_auth_headers
    ):
        # Arrange — la promoción ya fue aprobada
        _partner(estado_produccion=True)

        # Act
        response = _emitir(api_client, partner_auth_headers, nombre="produccion-nueva")

        # Assert
        assert response.status_code == 201
        assert response.json()["data"]["entorno"] == "Producción"

    def test_el_secreto_lo_recibe_el_partner_que_emite(
        self, api_client, mock_pinot, mock_kafka, partner_auth_headers
    ):
        """El punto de todo el delta: lo ve su dueño, no un tercero."""
        # Arrange
        _partner(estado_produccion=True)

        # Act
        data = _emitir(api_client, partner_auth_headers, nombre="produccion-nueva").json()["data"]

        # Assert
        assert data["client_secret"]
        assert "client_secret_hash" not in data

    def test_la_credencial_de_pruebas_sigue_activa(
        self, api_client, mock_pinot, mock_kafka, partner_auth_headers
    ):
        """RN-PON-008 — los entornos coexisten."""
        # Arrange
        _partner(estado_produccion=True)

        # Act
        _emitir(api_client, partner_auth_headers, nombre="produccion-nueva")

        # Assert
        sandbox = [
            c
            for c in PINOT_STORE["Dim_CredencialAPI"]
            if c["idpartner"] == ID_PARTNER and c["entorno"] == "Sandbox" and c["activo"]
        ]
        assert len(sandbox) == 1


class TestPropiedad:
    def test_un_partner_ajeno_no_emite_en_produccion(
        self, api_client, mock_pinot, mock_kafka, partner_ajeno_auth_headers
    ):
        """El delta no relaja el control de propiedad."""
        # Arrange
        _partner(estado_produccion=True)

        # Act
        response = _emitir(api_client, partner_ajeno_auth_headers)

        # Assert
        assert response.status_code == 403
