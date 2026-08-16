"""T022 — contrato del listado de cartera.

Envelope con `acotado_a`, `data: []` con `200` sin filas, `400` con `estado`
inválido nombrando los tres válidos, y `400` con rango de fechas.
"""

from __future__ import annotations

import pytest

RUTA = "/api/v1/informes/ventas-crm/prospectos"

#: Los campos que el contrato declara. `motivo_perdida` es **condicional**: el
#: propio OpenAPI dice «presente solo cuando el estado es `perdido`».
CAMPOS_SIEMPRE = {
    "empresa",
    "nombre_contacto",
    "cargo",
    "tipo_organizacion",
    "canal_origen",
    "etapa_actual",
    "ejecutivo",
    "estado",
    "valor_estimado",
    "fecha_registro",
}


@pytest.mark.api
class TestEnvelope:
    def test_responde_200_con_las_tres_claves_de_meta(
        self, api_client, admin_auth_headers, dos_carteras
    ):
        respuesta = api_client.get(RUTA, **admin_auth_headers)

        assert respuesta.status_code == 200
        cuerpo = respuesta.json()
        assert set(cuerpo) == {"data", "meta"}
        assert set(cuerpo["meta"]) == {"pagination", "filtros", "acotado_a"}

    def test_pagination_conserva_su_forma(self, api_client, admin_auth_headers, dos_carteras):
        cuerpo = api_client.get(RUTA, **admin_auth_headers).json()

        assert set(cuerpo["meta"]["pagination"]) == {"cursor", "limit", "has_next"}

    def test_los_campos_son_los_del_contrato(
        self, api_client, admin_auth_headers, dos_carteras
    ):
        cuerpo = api_client.get(RUTA, **admin_auth_headers).json()

        assert cuerpo["data"], "sin filas esta prueba no probaria nada"
        for fila in cuerpo["data"]:
            esperados = set(CAMPOS_SIEMPRE)
            if fila["estado"] == "perdido":
                esperados.add("motivo_perdida")
            assert set(fila) == esperados


@pytest.mark.api
class TestListadoVacio:
    def test_es_200_con_data_vacia_nunca_404(self, api_client, admin_auth_headers):
        respuesta = api_client.get(f"{RUTA}?etapa=NoExiste", **admin_auth_headers)

        assert respuesta.status_code == 200
        assert respuesta.json()["data"] == []

    def test_y_sigue_declarando_su_alcance(self, api_client, gerente_a_headers):
        # Es el caso que `acotado_a` existe para desambiguar.
        cuerpo = api_client.get(f"{RUTA}?etapa=NoExiste", **gerente_a_headers).json()

        assert cuerpo["meta"]["acotado_a"] == "propios"


@pytest.mark.api
class TestFiltroEstado:
    @pytest.mark.parametrize("estado", ["activo", "perdido", "convertido"])
    def test_los_tres_valores_se_aceptan(
        self, api_client, admin_auth_headers, dos_carteras, estado
    ):
        respuesta = api_client.get(f"{RUTA}?estado={estado}", **admin_auth_headers)

        assert respuesta.status_code == 200

    def test_un_valor_invalido_es_400(self, api_client, admin_auth_headers):
        respuesta = api_client.get(f"{RUTA}?estado=inactivo", **admin_auth_headers)

        assert respuesta.status_code == 400

    def test_el_error_nombra_los_tres_validos(self, api_client, admin_auth_headers):
        cuerpo = api_client.get(f"{RUTA}?estado=inactivo", **admin_auth_headers).json()

        assert cuerpo["error"] == "bad_request"
        for valido in ("activo", "perdido", "convertido"):
            assert valido in cuerpo["detail"]

    def test_el_filtro_aplicado_viaja_en_meta(
        self, api_client, admin_auth_headers, dos_carteras
    ):
        cuerpo = api_client.get(f"{RUTA}?estado=perdido", **admin_auth_headers).json()

        assert cuerpo["meta"]["filtros"]["estado"] == "perdido"


@pytest.mark.api
class TestEsListadoDeEstadoActual:
    @pytest.mark.parametrize("param", ["desde=2026-01-01", "hasta=2026-12-31"])
    def test_rechaza_el_rango_con_400(self, api_client, admin_auth_headers, param):
        respuesta = api_client.get(f"{RUTA}?{param}", **admin_auth_headers)

        assert respuesta.status_code == 400

    def test_granularidad_tambien(self, api_client, admin_auth_headers):
        assert api_client.get(f"{RUTA}?granularidad=mes", **admin_auth_headers).status_code == 400


@pytest.mark.api
class TestControlDeAcceso:
    def test_sin_token_es_401(self, api_client, mock_pinot):
        assert api_client.get(RUTA).status_code == 401

    @pytest.mark.parametrize("fixture", ["operator_auth_headers", "cliente_auth_headers"])
    def test_rol_no_autorizado_es_403(self, api_client, request, fixture):
        headers = request.getfixturevalue(fixture)

        assert api_client.get(RUTA, **headers).status_code == 403

    def test_administrador_accede(self, api_client, admin_auth_headers):
        assert api_client.get(RUTA, **admin_auth_headers).status_code == 200

    def test_gerente_accede(self, api_client, gerente_a_headers):
        assert api_client.get(RUTA, **gerente_a_headers).status_code == 200

    def test_director_de_marketing_accede(self, api_client, director_marketing_headers):
        assert api_client.get(RUTA, **director_marketing_headers).status_code == 200
