"""Contrato de la promocion a produccion (CU-O49, RF-PON-007 / RF-PON-008).

El proceso es semiautomatico A PROPOSITO (SRS L382): el partner pide y una
persona aprueba. Los dos endpoints tienen actores distintos y esa separacion
es lo que mas se comprueba aqui — que el partner no pueda aprobarse solo.
"""

from __future__ import annotations

import pytest

from conftest import PINOT_STORE

pytestmark = [pytest.mark.django_db, pytest.mark.api]

# `partner_auth_headers` vincula el usuario 51 al cliente 1.
ID_CLIENTE_DEL_PARTNER = 1
ID_PARTNER = 906


def _credencial_sandbox(idpartner=ID_PARTNER, idcredencial=9060, activo=True):
    PINOT_STORE["Dim_CredencialAPI"].append(
        {
            "idcredencial": idcredencial,
            "idpartner": idpartner,
            "idcliente": ID_CLIENTE_DEL_PARTNER,
            "client_secret_hash": "$2b$12$hash",
            "nombre_credencial": "pruebas",
            "entorno": "Sandbox",
            "activo": activo,
            "fecha_creacion": 1,
            "fecha_expiracion": 253402300799000,
            "fecha_actualizacion": 1,
        }
    )


@pytest.fixture
def partner_en_pruebas(mock_pinot, mock_kafka):
    """Partner con plan y credencial de pruebas activa: la ruta valida."""
    PINOT_STORE["Dim_Partner"].append(
        {
            "idpartner": ID_PARTNER,
            "idcliente": ID_CLIENTE_DEL_PARTNER,
            "nombrepartner": "Demo Promocion",
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
    _credencial_sandbox()
    PINOT_STORE["Fact_HistorialAccesoPartner"].append(
        {
            "idhistorial": 9060,
            "idpartner": ID_PARTNER,
            "idcredencial": 9060,
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


def _solicitar(api_client, headers, nombre="produccion-siniestros"):
    return api_client.post(
        f"/api/v1/partners/{ID_PARTNER}/solicitud-produccion",
        {"nombre_credencial": nombre},
        format="json",
        **headers,
    )


def _resolver(api_client, headers, decision, motivo=None):
    cuerpo = {"decision": decision}
    if motivo is not None:
        cuerpo["motivo"] = motivo
    return api_client.post(
        f"/api/v1/partners/{ID_PARTNER}/solicitud-produccion/resolucion",
        cuerpo,
        format="json",
        **headers,
    )


class TestSolicitudContract:
    def test_solicitar_when_en_pruebas_returns_202(
        self, api_client, partner_en_pruebas, partner_auth_headers
    ):
        """202 y no 201: la activacion exige intervencion humana posterior."""
        # Act
        response = _solicitar(api_client, partner_auth_headers)

        # Assert
        assert response.status_code == 202
        assert response.json()["data"]["estado"] == "Pendiente de aprobación"

    def test_solicitar_no_emite_credencial_de_produccion(
        self, api_client, partner_en_pruebas, partner_auth_headers
    ):
        """Pedir no es obtener: sin aprobacion no hay credencial productiva."""
        # Act
        _solicitar(api_client, partner_auth_headers)

        # Assert
        produccion = [
            c
            for c in PINOT_STORE["Dim_CredencialAPI"]
            if c["idpartner"] == ID_PARTNER and c["entorno"] == "Producción"
        ]
        assert produccion == []

    def test_solicitar_when_sin_nombre_returns_400(
        self, api_client, partner_en_pruebas, partner_auth_headers
    ):
        # Act
        response = _solicitar(api_client, partner_auth_headers, nombre="")

        # Assert
        assert response.status_code == 400

    def test_solicitar_when_partner_ajeno_returns_403(
        self, api_client, partner_en_pruebas, partner_ajeno_auth_headers
    ):
        # Act
        response = _solicitar(api_client, partner_ajeno_auth_headers)

        # Assert
        assert response.status_code == 403

    def test_solicitar_when_sin_token_returns_401(self, api_client, partner_en_pruebas):
        # Act
        response = api_client.post(
            f"/api/v1/partners/{ID_PARTNER}/solicitud-produccion",
            {"nombre_credencial": "x"},
            format="json",
        )

        # Assert
        assert response.status_code == 401

    def test_solicitar_when_nunca_paso_por_pruebas_returns_409(
        self, api_client, mock_pinot, mock_kafka, partner_auth_headers
    ):
        """RN-PON-004 — no hay atajo desde «Registrado» a produccion."""
        # Arrange — partner con plan pero sin credencial de pruebas
        PINOT_STORE["Dim_Partner"].append(
            {
                "idpartner": ID_PARTNER,
                "idcliente": ID_CLIENTE_DEL_PARTNER,
                "nombrepartner": "Sin pruebas",
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

        # Act
        response = _solicitar(api_client, partner_auth_headers)

        # Assert
        assert response.status_code == 409
        assert response.json()["code"] == "ruta_invalida"


class TestResolucionContract:
    def test_aprobar_when_pendiente_returns_200_sin_secreto_para_el_admin(
        self, api_client, partner_en_pruebas, partner_auth_headers, administrador_auth_headers
    ):
        """BE-DELTA-02 / RN-PON-005 — la respuesta de quien **aprueba** no
        puede llevar el `client_secret`: obligaría al Administrador a
        transmitirselo al partner por un canal inseguro. El partner lo emite
        desde su portal."""
        # Arrange
        assert _solicitar(api_client, partner_auth_headers).status_code == 202

        # Act
        response = _resolver(api_client, administrador_auth_headers, "aprobar")

        # Assert
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["estado"] == "Producción activa"
        assert "credencial" not in data
        assert "client_secret" not in response.content.decode()

    def test_rechazar_when_sin_motivo_returns_422(
        self, api_client, partner_en_pruebas, partner_auth_headers, administrador_auth_headers
    ):
        """RN-PON-007 — sin motivo el rechazo seria inaccionable."""
        # Arrange
        _solicitar(api_client, partner_auth_headers)

        # Act
        response = _resolver(api_client, administrador_auth_headers, "rechazar")

        # Assert
        assert response.status_code == 422
        assert response.json()["code"] == "motivo_requerido"

    def test_rechazar_when_con_motivo_returns_200_y_vuelve_a_pruebas(
        self, api_client, partner_en_pruebas, partner_auth_headers, administrador_auth_headers
    ):
        # Arrange
        _solicitar(api_client, partner_auth_headers)

        # Act
        response = _resolver(
            api_client, administrador_auth_headers, "rechazar", motivo="Faltan pruebas de carga"
        )

        # Assert — vuelve a «Pruebas activo», NO a «Registrado»
        assert response.status_code == 200
        assert response.json()["data"]["estado"] == "Pruebas activo"

    def test_resolver_when_sin_solicitud_pendiente_returns_409(
        self, api_client, partner_en_pruebas, administrador_auth_headers
    ):
        # Act — nadie solicito nada
        response = _resolver(api_client, administrador_auth_headers, "aprobar")

        # Assert
        assert response.status_code == 409
        assert response.json()["code"] == "sin_solicitud_pendiente"

    def test_resolver_when_decision_invalida_returns_400(
        self, api_client, partner_en_pruebas, partner_auth_headers, administrador_auth_headers
    ):
        # Arrange
        _solicitar(api_client, partner_auth_headers)

        # Act
        response = _resolver(api_client, administrador_auth_headers, "quiza")

        # Assert
        assert response.status_code == 400


class TestSoloElAdministradorResuelve:
    """RF-PON-008 — la separacion de actores es el control, no una formalidad.

    Si el propio partner pudiera resolver su solicitud, la aprobacion humana
    dejaria de existir como control.
    """

    def test_resolver_when_partner_returns_403(
        self, api_client, partner_en_pruebas, partner_auth_headers
    ):
        # Arrange
        _solicitar(api_client, partner_auth_headers)

        # Act — el partner intenta aprobarse a si mismo
        response = _resolver(api_client, partner_auth_headers, "aprobar")

        # Assert
        assert response.status_code == 403

    def test_resolver_when_desarrollador_apis_returns_403(
        self, api_client, partner_en_pruebas, partner_auth_headers, devapis_auth_headers
    ):
        """Gestiona planes y catalogo, pero la promocion la firma un Administrador."""
        # Arrange
        _solicitar(api_client, partner_auth_headers)

        # Act
        response = _resolver(api_client, devapis_auth_headers, "aprobar")

        # Assert
        assert response.status_code == 403

    def test_resolver_when_sin_token_returns_401(
        self, api_client, partner_en_pruebas, partner_auth_headers
    ):
        # Arrange
        _solicitar(api_client, partner_auth_headers)

        # Act
        response = api_client.post(
            f"/api/v1/partners/{ID_PARTNER}/solicitud-produccion/resolucion",
            {"decision": "aprobar"},
            format="json",
        )

        # Assert
        assert response.status_code == 401
