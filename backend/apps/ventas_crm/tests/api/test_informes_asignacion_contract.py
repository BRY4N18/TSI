"""T030 — contrato y control de acceso de `reasignaciones`.

El control de acceso aquí es **distinto al de los otros tres**: un gerente no
accede, ni siquiera acotado a lo suyo. El reparto de cartera es una decisión
*sobre* él, no una herramienta *suya*, y dársela acotada le mostraría de quién
recibió o a quién perdió prospectos —información de jefatura— disfrazada de
listado propio.
"""

from __future__ import annotations

import pytest

RUTA = "/api/v1/informes/ventas-crm/reasignaciones"

CAMPOS = {
    "empresa",
    "ejecutivo_anterior",
    "ejecutivo_nuevo",
    "tipo_asignacion",
    "motivo",
    "fecha",
}


@pytest.mark.api
class TestEnvelope:
    def test_responde_200_con_las_tres_claves_de_meta(
        self, api_client, admin_auth_headers, asignaciones_sembradas
    ):
        respuesta = api_client.get(RUTA, **admin_auth_headers)

        assert respuesta.status_code == 200
        cuerpo = respuesta.json()
        assert set(cuerpo["meta"]) == {"pagination", "filtros", "acotado_a"}

    def test_declara_alcance_total_siempre(
        self, api_client, admin_auth_headers, asignaciones_sembradas
    ):
        # Aquí solo llega el rol amplio y no hay eje de titularidad.
        cuerpo = api_client.get(RUTA, **admin_auth_headers).json()

        assert cuerpo["meta"]["acotado_a"] == "todos"

    def test_los_campos_son_los_del_contrato(
        self, api_client, admin_auth_headers, asignaciones_sembradas
    ):
        cuerpo = api_client.get(RUTA, **admin_auth_headers).json()

        assert cuerpo["data"], "sin filas esta prueba no probaria nada"
        for fila in cuerpo["data"]:
            assert set(fila) == CAMPOS

    def test_no_expone_identificadores(
        self, api_client, admin_auth_headers, asignaciones_sembradas
    ):
        cuerpo = api_client.get(RUTA, **admin_auth_headers).json()

        for fila in cuerpo["data"]:
            assert "idasignacion" not in fila
            assert "idprospecto" not in fila

    def test_vacio_es_200_nunca_404(self, api_client, admin_auth_headers):
        respuesta = api_client.get(f"{RUTA}?idprospecto=999999", **admin_auth_headers)

        assert respuesta.status_code == 200
        assert respuesta.json()["data"] == []


@pytest.mark.api
class TestFiltros:
    def test_un_tipo_inexistente_es_400_nombrando_los_validos(
        self, api_client, admin_auth_headers, asignaciones_sembradas
    ):
        cuerpo = api_client.get(
            f"{RUTA}?tipo_asignacion=inventado", **admin_auth_headers
        ).json()

        assert cuerpo["error"] == "bad_request"
        assert "manual" in cuerpo["detail"]

    def test_un_tipo_valido_acota(
        self, api_client, admin_auth_headers, asignaciones_sembradas
    ):
        cuerpo = api_client.get(
            f"{RUTA}?tipo_asignacion=manual", **admin_auth_headers
        ).json()

        assert all(f["tipo_asignacion"] == "manual" for f in cuerpo["data"])

    def test_idprospecto_no_numerico_es_400(self, api_client, admin_auth_headers):
        respuesta = api_client.get(f"{RUTA}?idprospecto=abc", **admin_auth_headers)

        assert respuesta.status_code == 400


@pytest.mark.api
class TestControlDeAcceso:
    def test_sin_token_es_401(self, api_client, mock_pinot):
        assert api_client.get(RUTA).status_code == 401

    def test_administrador_accede(self, api_client, admin_auth_headers):
        assert api_client.get(RUTA, **admin_auth_headers).status_code == 200

    def test_director_de_marketing_accede(self, api_client, director_marketing_headers):
        assert api_client.get(RUTA, **director_marketing_headers).status_code == 200

    @pytest.mark.parametrize("fixture", ["gerente_a_headers", "gerente_b_headers"])
    def test_un_gerente_recibe_403(self, api_client, request, fixture):
        """No accede ni siquiera acotado a lo suyo."""
        headers = request.getfixturevalue(fixture)

        assert api_client.get(RUTA, **headers).status_code == 403

    def test_el_403_del_gerente_no_filtra_filas(
        self, api_client, gerente_a_headers, asignaciones_sembradas
    ):
        respuesta = api_client.get(RUTA, **gerente_a_headers)

        assert respuesta.status_code == 403
        assert "Alfa Seguros" not in respuesta.content.decode()

    @pytest.mark.parametrize("fixture", ["operator_auth_headers", "cliente_auth_headers"])
    def test_rol_ajeno_recibe_403(self, api_client, request, fixture):
        headers = request.getfixturevalue(fixture)

        assert api_client.get(RUTA, **headers).status_code == 403
