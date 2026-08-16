"""T046, T024, T032 y T041 — la implementación coincide con el contrato.

Lee **el OpenAPI** y compara contra él, endpoint por endpoint. Es lo único que
detecta una divergencia entre los dos documentos: las pruebas de contrato de
cada user story comparan contra una copia escrita a mano.

Este contrato ganó `meta.alcance` el 2026-08-15: la implementación de FR-008 lo
exigía y el contrato no lo declaraba.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

CONTRATO = (
    Path(__file__).resolve().parents[5]
    / "specs" / "002-tactico" / "Red-Operativa"
    / "informes-tacticos-simples" / "backend" / "contracts"
    / "informes-tacticos-simples.openapi.yaml"
)

#: El contrato declara este campo como condicional en su propia descripción.
CONDICIONALES = {"caso_afectado"}

BASE = "/api/v1/informes/red-operativa"


@pytest.fixture(scope="module")
def contrato() -> dict:
    assert CONTRATO.is_file(), f"no se encuentra el contrato en {CONTRATO}"
    return yaml.safe_load(CONTRATO.read_text(encoding="utf-8"))


@pytest.fixture
def sembrado(todo_sembrado, regiones_sembradas):
    return True


class TestElContratoEstaBienFormado:
    def test_es_yaml_valido_y_declara_cuatro_rutas(self, contrato):
        assert len(contrato["paths"]) == 4

    def test_todas_cuelgan_del_prefijo_del_departamento(self, contrato):
        for ruta in contrato["paths"]:
            assert ruta.startswith("/informes/red-operativa/")

    def test_todas_son_solo_lectura(self, contrato):
        for ruta, metodos in contrato["paths"].items():
            assert set(metodos) == {"get"}, f"'{ruta}' declara {set(metodos)}"

    def test_todas_declaran_los_codigos_de_error(self, contrato):
        for ruta, metodos in contrato["paths"].items():
            assert {"200", "400", "401", "403"} <= set(metodos["get"]["responses"]), ruta

    def test_el_envelope_exige_acotado_a(self, contrato):
        meta = contrato["components"]["schemas"]["RespuestaListado"]["properties"]["meta"]

        assert "acotado_a" in meta["required"]

    def test_y_declara_alcance_sin_exigirlo(self, contrato):
        """Solo lo emite `flota`; obligarlo a todos sería ruido."""
        meta = contrato["components"]["schemas"]["RespuestaListado"]["properties"]["meta"]

        assert "alcance" in meta["properties"]
        assert "alcance" not in meta["required"]

    def test_ninguna_respuesta_declara_posicion_ni_contacto(self, contrato):
        import json

        texto = json.dumps(contrato).lower()

        for prohibida in ("latitud", "longitud", "contactoproveedor"):
            assert prohibida not in texto


@pytest.mark.api
class TestLaImplementacionCoincide:
    def test_las_cuatro_rutas_responden_200(
        self, api_client, admin_auth_headers, contrato, sembrado
    ):
        for ruta in contrato["paths"]:
            respuesta = api_client.get(f"/api/v1{ruta}", **admin_auth_headers)

            assert respuesta.status_code == 200, (
                f"'{ruta}' respondio {respuesta.status_code}"
            )

    def test_los_campos_devueltos_son_los_que_el_contrato_declara(
        self, api_client, admin_auth_headers, contrato, sembrado
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
        self, api_client, admin_auth_headers, contrato, sembrado
    ):
        paginacion = set(contrato["components"]["schemas"]["Paginacion"]["properties"])

        for ruta in contrato["paths"]:
            cuerpo = api_client.get(f"/api/v1{ruta}", **admin_auth_headers).json()

            assert set(cuerpo) == {"data", "meta"}
            assert {"pagination", "filtros", "acotado_a"} <= set(cuerpo["meta"])
            assert set(cuerpo["meta"]["pagination"]) == paginacion

    def test_solo_la_flota_declara_alcance(
        self, api_client, admin_auth_headers, contrato, sembrado
    ):
        for ruta in contrato["paths"]:
            cuerpo = api_client.get(f"/api/v1{ruta}", **admin_auth_headers).json()
            tiene = "alcance" in cuerpo["meta"]

            assert tiene == ruta.endswith("/flota"), ruta

    def test_vacio_es_200_nunca_404(self, api_client, admin_auth_headers, contrato):
        for ruta in contrato["paths"]:
            respuesta = api_client.get(f"/api/v1{ruta}?limit=500", **admin_auth_headers)

            assert respuesta.status_code == 200, ruta

    def test_cada_filtro_declarado_se_acepta(
        self, api_client, admin_auth_headers, contrato, sembrado
    ):
        muestras = {
            "limit": "10", "dir": "asc", "condado": "5701", "tipo_unidad": "Grua",
            "dado_de_alta": "true", "tipo_baja": "Normal",
            "estado_region": "En_Alerta", "detenida_mas_de_dias": "1",
            "resultado": "Aprobada", "region": "5901",
            "desde": "2026-01-01", "hasta": "2026-12-31", "proveedor": "5501",
        }

        for ruta, metodos in contrato["paths"].items():
            for parametro in metodos["get"].get("parameters", []):
                nombre = parametro.get("name") or parametro["$ref"].split("/")[-1].lower()
                valor = muestras.get(nombre)
                if valor is None:
                    continue

                respuesta = api_client.get(
                    f"/api/v1{ruta}?{nombre}={valor}", **admin_auth_headers
                )
                assert respuesta.status_code == 200, (
                    f"'{ruta}' rechaza '{nombre}={valor}', que el contrato declara valido"
                )
