"""T044 — contrato y control de acceso de los dos listados de OT17."""

from __future__ import annotations

import pytest

BASE = "/api/v1/informes/cuentas-clientes"

ENDPOINTS = ["cuentas-por-estado", "transferencias-propiedad"]

CAMPOS = {
    "cuentas-por-estado": {
        "razon_social",
        "tipo",
        "estado",
        "estado_onboarding",
        "fecha_inicio_contrato",
        "propietario",
    },
    "transferencias-propiedad": {
        "razon_social",
        "propietario_anterior",
        "propietario_nuevo",
        "fecha",
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
        self, api_client, admin_auth_headers, informe, transferencias_sembradas
    ):
        cuerpo = api_client.get(f"{BASE}/{informe}", **admin_auth_headers).json()

        assert cuerpo["data"], "sin filas esta prueba no probaria nada"
        for fila in cuerpo["data"]:
            assert set(fila) == CAMPOS[informe]

    @pytest.mark.parametrize("informe", ENDPOINTS)
    def test_no_expone_identificadores(
        self, api_client, admin_auth_headers, informe, transferencias_sembradas
    ):
        cuerpo = api_client.get(f"{BASE}/{informe}", **admin_auth_headers).json()

        for fila in cuerpo["data"]:
            assert "idcliente" not in fila
            assert "admin_local_id" not in fila
            assert "idusuarioanterior" not in fila


@pytest.mark.api
class TestFiltroDeEstado:
    def test_acepta_los_estados_canonicos_del_sistema(
        self, api_client, admin_auth_headers, cuentas_sembradas
    ):
        # El OpenAPI declaraba `[Activo, Pendiente, Suspendido, Baja]`, pero
        # `Suspendido` no existe y la baja se llama `Dado de baja`. Validar
        # contra ese enum habria rechazado con 400 un filtro correcto.
        respuesta = api_client.get(
            f"{BASE}/cuentas-por-estado?estado=Dado de baja", **admin_auth_headers
        )

        assert respuesta.status_code == 200
        assert len(respuesta.json()["data"]) == 1

    def test_un_estado_inexistente_es_400_nombrando_los_validos(
        self, api_client, admin_auth_headers
    ):
        cuerpo = api_client.get(
            f"{BASE}/cuentas-por-estado?estado=Vigente", **admin_auth_headers
        ).json()

        assert cuerpo["error"] == "bad_request"
        assert "Activo" in cuerpo["detail"]

    def test_el_filtro_aplicado_viaja_en_meta(
        self, api_client, admin_auth_headers, cuentas_sembradas
    ):
        cuerpo = api_client.get(
            f"{BASE}/cuentas-por-estado?estado=Activo", **admin_auth_headers
        ).json()

        assert cuerpo["meta"]["filtros"]["estado"] == "Activo"


@pytest.mark.api
@pytest.mark.parametrize("informe", ENDPOINTS)
class TestControlDeAcceso:
    def test_operador_recibe_403(self, api_client, operator_auth_headers, informe):
        assert api_client.get(f"{BASE}/{informe}", **operator_auth_headers).status_code == 403

    def test_cliente_recibe_403(self, api_client, cliente_auth_headers, informe):
        assert api_client.get(f"{BASE}/{informe}", **cliente_auth_headers).status_code == 403

    def test_director_tecnologico_recibe_403(
        self, api_client, director_tecnologico_auth_headers, informe
    ):
        respuesta = api_client.get(f"{BASE}/{informe}", **director_tecnologico_auth_headers)

        assert respuesta.status_code == 403

    def test_sin_token_es_401(self, api_client, mock_pinot, informe):
        assert api_client.get(f"{BASE}/{informe}").status_code == 401

    def test_administrador_accede(self, api_client, admin_auth_headers, informe):
        assert api_client.get(f"{BASE}/{informe}", **admin_auth_headers).status_code == 200
