"""T033 y T035 — contrato y control de acceso de los dos listados de OT04.

Incluye el rechazo de `desde`/`hasta` con `400` (FR-012): son listados de estado
actual. Lo que sí aceptan es `dias_minimo`, que no es un rango sino un umbral de
antigüedad — la distinción importa, porque un consumidor podría razonablemente
esperar que «los últimos 7 días» se pidiera con un rango.
"""

from __future__ import annotations

import pytest

BASE = "/api/v1/informes/cuentas-clientes"

ENDPOINTS = ["solicitudes-alta-pendientes", "onboarding-incompleto"]

CAMPOS = {
    "solicitudes-alta-pendientes": {
        "razon_social",
        "tipo",
        "fecha_solicitud",
        "dias_transcurridos",
    },
    "onboarding-incompleto": {
        "razon_social",
        "etapa",
        "fecha_ultima_actualizacion",
        "dias_detenido",
    },
}


@pytest.mark.api
class TestEnvelope:
    @pytest.mark.parametrize("informe", ENDPOINTS)
    def test_responde_200_con_el_envelope(self, api_client, admin_auth_headers, informe):
        respuesta = api_client.get(f"{BASE}/{informe}", **admin_auth_headers)

        assert respuesta.status_code == 200
        cuerpo = respuesta.json()
        assert set(cuerpo) == {"data", "meta"}
        assert set(cuerpo["meta"]["pagination"]) == {"cursor", "limit", "has_next"}

    @pytest.mark.parametrize("informe", ENDPOINTS)
    def test_los_campos_son_exactamente_los_del_contrato(
        self, api_client, admin_auth_headers, informe, onboarding_sembrado
    ):
        cuerpo = api_client.get(f"{BASE}/{informe}", **admin_auth_headers).json()

        assert cuerpo["data"], "sin filas esta prueba no probaria nada"
        for fila in cuerpo["data"]:
            assert set(fila) == CAMPOS[informe]

    def test_ninguno_expone_identificadores(
        self, api_client, admin_auth_headers, onboarding_sembrado
    ):
        for informe in ENDPOINTS:
            cuerpo = api_client.get(f"{BASE}/{informe}", **admin_auth_headers).json()
            for fila in cuerpo["data"]:
                assert "idcliente" not in fila and "id_cliente" not in fila
                assert "id_onboarding" not in fila


@pytest.mark.api
class TestFiltros:
    def test_dias_minimo_se_refleja_en_meta(
        self, api_client, admin_auth_headers, solicitudes_pendientes_sembradas
    ):
        cuerpo = api_client.get(
            f"{BASE}/solicitudes-alta-pendientes?dias_minimo=7", **admin_auth_headers
        ).json()

        # Normalizado a entero, no el texto que vino en la URL.
        assert cuerpo["meta"]["filtros"]["dias_minimo"] == 7

    def test_dias_minimo_negativo_es_400(self, api_client, admin_auth_headers):
        respuesta = api_client.get(
            f"{BASE}/solicitudes-alta-pendientes?dias_minimo=-1", **admin_auth_headers
        )

        assert respuesta.status_code == 400

    def test_dias_minimo_no_numerico_es_400(self, api_client, admin_auth_headers):
        respuesta = api_client.get(
            f"{BASE}/solicitudes-alta-pendientes?dias_minimo=muchos", **admin_auth_headers
        )

        assert respuesta.status_code == 400

    def test_una_etapa_inexistente_es_400_nombrando_las_validas(
        self, api_client, admin_auth_headers, onboarding_sembrado
    ):
        cuerpo = api_client.get(
            f"{BASE}/onboarding-incompleto?etapa=inventada", **admin_auth_headers
        ).json()

        assert cuerpo["error"] == "bad_request"
        assert "verificacion_documental" in cuerpo["detail"], (
            "sin la lista de validas, quien recibe el 400 no puede corregir"
        )

    def test_tipo_acepta_el_valor_real_del_sistema(
        self, api_client, admin_auth_headers, solicitudes_pendientes_sembradas
    ):
        # El OpenAPI declaraba `enum: [aseguradora, municipio, proveedor]`, que
        # no son los valores reales. Validar contra ese enum rechazaria con 400
        # un filtro correcto.
        respuesta = api_client.get(
            f"{BASE}/solicitudes-alta-pendientes?tipo=Corporativo", **admin_auth_headers
        )

        assert respuesta.status_code == 200
        assert len(respuesta.json()["data"]) == 2


@pytest.mark.api
@pytest.mark.parametrize("informe", ENDPOINTS)
class TestSinRango:
    """T035 — FR-012: son listados de estado actual."""

    def test_desde_es_400(self, api_client, admin_auth_headers, informe):
        respuesta = api_client.get(
            f"{BASE}/{informe}?desde=2026-01-01", **admin_auth_headers
        )

        assert respuesta.status_code == 400

    def test_hasta_es_400(self, api_client, admin_auth_headers, informe):
        respuesta = api_client.get(
            f"{BASE}/{informe}?hasta=2026-01-31", **admin_auth_headers
        )

        assert respuesta.status_code == 400

    def test_dias_minimo_si_se_admite(self, api_client, admin_auth_headers, informe):
        # Es un umbral de antigüedad, no un rango: la distinción es la razón de
        # que uno se acepte y el otro no.
        respuesta = api_client.get(f"{BASE}/{informe}?dias_minimo=3", **admin_auth_headers)

        assert respuesta.status_code == 200


@pytest.mark.api
@pytest.mark.parametrize("informe", ENDPOINTS)
class TestControlDeAcceso:
    def test_operador_recibe_403(self, api_client, operator_auth_headers, informe):
        assert api_client.get(f"{BASE}/{informe}", **operator_auth_headers).status_code == 403

    def test_director_tecnologico_recibe_403(
        self, api_client, director_tecnologico_auth_headers, informe
    ):
        # Su autoridad alcanza **solo** a accesos técnicos (§5.1 del SRS).
        respuesta = api_client.get(f"{BASE}/{informe}", **director_tecnologico_auth_headers)

        assert respuesta.status_code == 403

    def test_sin_token_es_401(self, api_client, mock_pinot, informe):
        assert api_client.get(f"{BASE}/{informe}").status_code == 401

    def test_administrador_accede(self, api_client, admin_auth_headers, informe):
        assert api_client.get(f"{BASE}/{informe}", **admin_auth_headers).status_code == 200
