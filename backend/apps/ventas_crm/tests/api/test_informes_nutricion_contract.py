"""T040 — contrato de los dos listados de nutrición."""

from __future__ import annotations

import pytest

BASE = "/api/v1/informes/ventas-crm"

CAMPOS = {
    "demos-activas": {
        "empresa",
        "nombre_contacto",
        "ejecutivo",
        "expiracion",
        "dias_restantes",
    },
    "notificaciones-enviadas": {
        "empresa",
        "ejecutivo_notificado",
        "regla_disparada",
        "canal",
        "fecha",
    },
}


@pytest.fixture
def sembrado(demos_formato_mixto, notificaciones_sembradas, reloj_congelado):
    return True


@pytest.mark.api
@pytest.mark.parametrize("informe", list(CAMPOS))
class TestEnvelope:
    def test_responde_200_con_las_tres_claves_de_meta(
        self, api_client, admin_auth_headers, informe, sembrado
    ):
        respuesta = api_client.get(f"{BASE}/{informe}", **admin_auth_headers)

        assert respuesta.status_code == 200
        cuerpo = respuesta.json()
        assert set(cuerpo) == {"data", "meta"}
        assert set(cuerpo["meta"]) == {"pagination", "filtros", "acotado_a"}

    def test_pagination_conserva_su_forma(
        self, api_client, admin_auth_headers, informe, sembrado
    ):
        cuerpo = api_client.get(f"{BASE}/{informe}", **admin_auth_headers).json()

        assert set(cuerpo["meta"]["pagination"]) == {"cursor", "limit", "has_next"}

    def test_los_campos_son_los_del_contrato(
        self, api_client, admin_auth_headers, informe, sembrado
    ):
        cuerpo = api_client.get(f"{BASE}/{informe}", **admin_auth_headers).json()

        assert cuerpo["data"], "sin filas esta prueba no probaria nada"
        for fila in cuerpo["data"]:
            assert set(fila) == CAMPOS[informe]

    def test_no_expone_identificadores(
        self, api_client, admin_auth_headers, informe, sembrado
    ):
        cuerpo = api_client.get(f"{BASE}/{informe}", **admin_auth_headers).json()

        for fila in cuerpo["data"]:
            assert "idprospecto" not in fila
            assert "id_prospecto" not in fila
            assert "idnotificacion" not in fila
            assert "idusuario" not in fila

    def test_vacio_es_200_nunca_404(self, api_client, admin_auth_headers, informe):
        # Sin datos sembrados: la consulta es válida y el resultado vacío.
        respuesta = api_client.get(f"{BASE}/{informe}", **admin_auth_headers)

        assert respuesta.status_code == 200
        assert respuesta.json()["data"] == []


@pytest.mark.api
@pytest.mark.parametrize("informe", list(CAMPOS))
class TestControlDeAcceso:
    def test_sin_token_es_401(self, api_client, mock_pinot, informe):
        assert api_client.get(f"{BASE}/{informe}").status_code == 401

    def test_administrador_accede(self, api_client, admin_auth_headers, informe):
        assert api_client.get(f"{BASE}/{informe}", **admin_auth_headers).status_code == 200

    def test_director_de_marketing_accede(
        self, api_client, director_marketing_headers, informe
    ):
        respuesta = api_client.get(f"{BASE}/{informe}", **director_marketing_headers)

        assert respuesta.status_code == 200

    def test_gerente_accede_acotado(self, api_client, gerente_a_headers, informe):
        # A diferencia de `reasignaciones`, estos dos sí son herramienta suya:
        # su valor es actuar antes de que la oportunidad se enfríe.
        respuesta = api_client.get(f"{BASE}/{informe}", **gerente_a_headers)

        assert respuesta.status_code == 200
        assert respuesta.json()["meta"]["acotado_a"] == "propios"

    @pytest.mark.parametrize("fixture", ["operator_auth_headers", "cliente_auth_headers"])
    def test_rol_ajeno_es_403(self, api_client, request, informe, fixture):
        headers = request.getfixturevalue(fixture)

        assert api_client.get(f"{BASE}/{informe}", **headers).status_code == 403


@pytest.mark.api
class TestDemosEsEstadoActual:
    @pytest.mark.parametrize("param", ["desde=2026-01-01", "hasta=2026-12-31"])
    def test_rechaza_el_rango(self, api_client, admin_auth_headers, param):
        respuesta = api_client.get(f"{BASE}/demos-activas?{param}", **admin_auth_headers)

        assert respuesta.status_code == 400


@pytest.mark.api
class TestNotificacionesEsHechosDelPeriodo:
    def test_acepta_rango(self, api_client, admin_auth_headers):
        respuesta = api_client.get(
            f"{BASE}/notificaciones-enviadas?desde=2026-08-01&hasta=2026-08-31",
            **admin_auth_headers,
        )

        assert respuesta.status_code == 200

    def test_los_extremos_viajan_en_meta(
        self, api_client, admin_auth_headers, notificaciones_sembradas
    ):
        cuerpo = api_client.get(
            f"{BASE}/notificaciones-enviadas?desde=2026-08-01", **admin_auth_headers
        ).json()

        assert cuerpo["meta"]["filtros"]["desde"] == "2026-08-01"

    def test_rango_invertido_es_400(self, api_client, admin_auth_headers):
        respuesta = api_client.get(
            f"{BASE}/notificaciones-enviadas?desde=2026-08-31&hasta=2026-08-01",
            **admin_auth_headers,
        )

        assert respuesta.status_code == 400
