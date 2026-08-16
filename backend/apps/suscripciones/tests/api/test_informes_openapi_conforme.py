"""T045, T033 y T040 — la implementación coincide con el contrato, endpoint por endpoint.

Lee **el OpenAPI** y compara contra él: es lo único que detecta una divergencia
entre los dos documentos. Las pruebas de contrato de cada user story comparan
contra una copia escrita a mano en el propio fichero de prueba, así que un cambio
en el contrato no las movería.

Este contrato también **estaba mal formado** hasta el 2026-08-15 —una descripción
sin comillas contenía `data: []`—, el tercero de la serie con el mismo defecto.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

CONTRATO = (
    Path(__file__).resolve().parents[5]
    / "specs" / "002-tactico" / "Suscripciones-Facturacion"
    / "informes-tacticos-simples" / "backend" / "contracts"
    / "informes-tacticos-simples.openapi.yaml"
)

#: Campos que el contrato declara **condicionales** en su propia descripción.
CONDICIONALES = {
    "motivo_cancelacion", "fecha_cancelacion", "cambio_programado",
    "dias_mora", "resuelta_por", "motivo_rechazo", "fecha_resolucion",
}

BASE = "/api/v1/informes/suscripciones-facturacion"
CATALOGO = ["suscripciones", "solicitudes-cambio-plan"]
FINANZAS = ["facturas", "metodos-pago"]


@pytest.fixture(scope="module")
def contrato() -> dict:
    assert CONTRATO.is_file(), f"no se encuentra el contrato en {CONTRATO}"
    return yaml.safe_load(CONTRATO.read_text(encoding="utf-8"))


class TestElContratoEstaBienFormado:
    def test_es_yaml_valido_y_declara_cuatro_rutas(self, contrato):
        assert len(contrato["paths"]) == 4

    def test_todas_cuelgan_del_prefijo_del_departamento(self, contrato):
        for ruta in contrato["paths"]:
            assert ruta.startswith("/informes/suscripciones-facturacion/")

    def test_todas_son_solo_lectura(self, contrato):
        for ruta, metodos in contrato["paths"].items():
            assert set(metodos) == {"get"}, f"'{ruta}' declara {set(metodos)}"

    def test_todas_declaran_los_codigos_de_error(self, contrato):
        for ruta, metodos in contrato["paths"].items():
            assert {"200", "400", "401", "403"} <= set(metodos["get"]["responses"]), ruta

    def test_el_envelope_exige_acotado_a(self, contrato):
        requeridos = contrato["components"]["schemas"]["RespuestaListado"][
            "properties"
        ]["meta"]["required"]

        assert "acotado_a" in requeridos

    def test_ni_el_contrato_nombra_el_identificador_de_cobro(self, contrato):
        assert "tokenpasarela" not in json.dumps(contrato).lower()


@pytest.mark.api
class TestLaImplementacionCoincide:
    def test_las_cuatro_rutas_responden_200(
        self, api_client, admin_auth_headers, contrato, todo_sembrado
    ):
        for ruta in contrato["paths"]:
            respuesta = api_client.get(f"/api/v1{ruta}", **admin_auth_headers)

            assert respuesta.status_code == 200, (
                f"'{ruta}' respondio {respuesta.status_code}"
            )

    def test_los_campos_devueltos_son_los_que_el_contrato_declara(
        self, api_client, admin_auth_headers, contrato, todo_sembrado
    ):
        esquemas = contrato["components"]["schemas"]

        for ruta, metodos in contrato["paths"].items():
            ref = metodos["get"]["responses"]["200"]["content"]["application/json"][
                "schema"
            ]["allOf"][1]["properties"]["data"]["items"]["$ref"]
            declarados = set(esquemas[ref.split("/")[-1]]["properties"])

            cuerpo = api_client.get(
                f"/api/v1{ruta}?limit=500", **admin_auth_headers
            ).json()
            assert cuerpo["data"], f"'{ruta}' sin filas: la comparacion no probaria nada"

            for fila in cuerpo["data"]:
                sobrantes = set(fila) - declarados
                faltantes = declarados - set(fila) - CONDICIONALES

                assert not sobrantes, f"'{ruta}' devuelve no declarados: {sobrantes}"
                assert not faltantes, f"'{ruta}' no devuelve declarados: {faltantes}"

    def test_el_envelope_cumple_el_esquema(
        self, api_client, admin_auth_headers, contrato, todo_sembrado
    ):
        paginacion = set(contrato["components"]["schemas"]["Paginacion"]["properties"])

        for ruta in contrato["paths"]:
            cuerpo = api_client.get(f"/api/v1{ruta}", **admin_auth_headers).json()

            assert set(cuerpo) == {"data", "meta"}
            assert set(cuerpo["meta"]) == {"pagination", "filtros", "acotado_a"}
            assert set(cuerpo["meta"]["pagination"]) == paginacion

    def test_todas_declaran_su_alcance(
        self, api_client, admin_auth_headers, contrato, todo_sembrado
    ):
        for ruta in contrato["paths"]:
            cuerpo = api_client.get(f"/api/v1{ruta}", **admin_auth_headers).json()

            assert cuerpo["meta"]["acotado_a"] in ("propios", "todos"), ruta

    def test_vacio_es_200_nunca_404(self, api_client, admin_auth_headers, contrato):
        for ruta in contrato["paths"]:
            respuesta = api_client.get(
                f"/api/v1{ruta}?cuenta=999999", **admin_auth_headers
            )

            assert respuesta.status_code == 200, ruta
            assert respuesta.json()["data"] == [], ruta

    def test_cada_filtro_declarado_se_acepta(
        self, api_client, admin_auth_headers, contrato, todo_sembrado
    ):
        muestras = {
            "limit": "10", "dir": "asc", "plan": "7901",
            "vence_en_dias": "30", "con_cambio_programado": "true",
            "cancelada_desde": "2026-01-01", "cancelada_hasta": "2026-12-31",
            "estado_pago": "Pagada", "vencidas": "false",
            "caduca_en_dias": "30", "desde": "2026-01-01", "hasta": "2026-12-31",
            "cuenta": "7701",
        }
        # `estado` significa cosas distintas en dos listados: una suscripción
        # está `Activa` y una solicitud está `Pendiente`. Un solo valor de
        # muestra haría fallar a uno de los dos por un motivo que no es un
        # defecto de la implementación.
        por_ruta = {
            "/informes/suscripciones-facturacion/suscripciones": {"estado": "Activa"},
            "/informes/suscripciones-facturacion/solicitudes-cambio-plan": {
                "estado": "Pendiente"
            },
        }

        for ruta, metodos in contrato["paths"].items():
            del_listado = {**muestras, **por_ruta.get(ruta, {})}
            for parametro in metodos["get"].get("parameters", []):
                nombre = parametro.get("name") or parametro["$ref"].split("/")[-1].lower()
                valor = del_listado.get(nombre)
                if valor is None:
                    continue

                respuesta = api_client.get(
                    f"/api/v1{ruta}?{nombre}={valor}", **admin_auth_headers
                )
                assert respuesta.status_code == 200, (
                    f"'{ruta}' rechaza '{nombre}={valor}', que el contrato declara valido"
                )


@pytest.mark.api
class TestControlDeAccesoPorMateria:
    """§5.1 del SRS: la autoridad de este departamento está **repartida**."""

    @pytest.mark.parametrize("informe", CATALOGO)
    def test_estrategia_accede_a_catalogo(
        self, api_client, director_estrategia_headers, informe
    ):
        respuesta = api_client.get(f"{BASE}/{informe}", **director_estrategia_headers)

        assert respuesta.status_code == 200

    @pytest.mark.parametrize("informe", FINANZAS)
    def test_estrategia_no_accede_a_finanzas(
        self, api_client, director_estrategia_headers, informe
    ):
        respuesta = api_client.get(f"{BASE}/{informe}", **director_estrategia_headers)

        assert respuesta.status_code == 403

    @pytest.mark.parametrize("informe", FINANZAS)
    def test_financiero_accede_a_finanzas(
        self, api_client, director_financiero_headers, informe
    ):
        respuesta = api_client.get(f"{BASE}/{informe}", **director_financiero_headers)

        assert respuesta.status_code == 200

    @pytest.mark.parametrize("informe", CATALOGO)
    def test_financiero_no_accede_a_catalogo(
        self, api_client, director_financiero_headers, informe
    ):
        respuesta = api_client.get(f"{BASE}/{informe}", **director_financiero_headers)

        assert respuesta.status_code == 403

    @pytest.mark.parametrize("informe", CATALOGO + FINANZAS)
    def test_sin_token_es_401(self, api_client, mock_pinot, informe):
        assert api_client.get(f"{BASE}/{informe}").status_code == 401

    @pytest.mark.parametrize("informe", CATALOGO + FINANZAS)
    def test_rol_ajeno_es_403(self, api_client, operator_auth_headers, informe):
        assert api_client.get(f"{BASE}/{informe}", **operator_auth_headers).status_code == 403

    @pytest.mark.parametrize("informe", CATALOGO + FINANZAS)
    def test_el_cliente_accede_acotado(
        self, api_client, cliente_a_headers, informe, todo_sembrado
    ):
        respuesta = api_client.get(f"{BASE}/{informe}", **cliente_a_headers)

        assert respuesta.status_code == 200
        assert respuesta.json()["meta"]["acotado_a"] == "propios"
