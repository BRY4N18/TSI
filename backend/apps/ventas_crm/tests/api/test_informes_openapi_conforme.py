"""T045 — la implementación coincide con el contrato, endpoint por endpoint.

Lee **el OpenAPI** y compara contra él. Es lo único que detecta una divergencia
entre los dos documentos: si alguien cambia el contrato sin tocar el código —o al
revés—, las pruebas de contrato de cada user story siguen en verde, porque su
copia de la verdad está escrita en el propio fichero de prueba.

También hace de guardia sobre el fichero. No es hipotético: este contrato
**estaba mal formado** hasta el 2026-08-15 —una descripción sin comillas
contenía `data: []`—, exactamente el mismo defecto que el del módulo piloto.
Ninguna herramienta lo había cargado nunca.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

CONTRATO = (
    Path(__file__).resolve().parents[5]
    / "specs"
    / "002-tactico"
    / "Ventas-CRM"
    / "informes-tacticos-simples"
    / "backend"
    / "contracts"
    / "informes-tacticos-simples.openapi.yaml"
)

#: Campos que el contrato declara **condicionales** en su propia descripción.
CONDICIONALES = {"motivo_perdida"}


@pytest.fixture(scope="module")
def contrato() -> dict:
    assert CONTRATO.is_file(), f"no se encuentra el contrato en {CONTRATO}"
    return yaml.safe_load(CONTRATO.read_text(encoding="utf-8"))


@pytest.fixture
def todo_sembrado(
    dos_carteras, asignaciones_sembradas, notificaciones_sembradas,
    demos_formato_mixto, reloj_congelado,
):
    return True


class TestElContratoEstaBienFormado:
    def test_es_yaml_valido_y_declara_cuatro_rutas(self, contrato):
        assert len(contrato["paths"]) == 4

    def test_todas_cuelgan_del_prefijo_del_departamento(self, contrato):
        for ruta in contrato["paths"]:
            assert ruta.startswith("/informes/ventas-crm/")

    def test_todas_son_solo_lectura(self, contrato):
        for ruta, metodos in contrato["paths"].items():
            assert set(metodos) == {"get"}, f"'{ruta}' declara {set(metodos)}"

    def test_todas_declaran_los_codigos_de_error(self, contrato):
        for ruta, metodos in contrato["paths"].items():
            respuestas = set(metodos["get"]["responses"])
            assert {"200", "400", "401", "403"} <= respuestas, ruta

    def test_el_envelope_exige_acotado_a(self, contrato):
        """Es la ampliación que este módulo aporta al contrato común."""
        requeridos = contrato["components"]["schemas"]["RespuestaListado"]["properties"][
            "meta"
        ]["required"]

        assert "acotado_a" in requeridos

    def test_acotado_a_solo_admite_dos_valores(self, contrato):
        esquema = contrato["components"]["schemas"]["RespuestaListado"]["properties"][
            "meta"
        ]["properties"]["acotado_a"]

        assert set(esquema["enum"]) == {"propios", "todos"}


@pytest.mark.api
class TestLaImplementacionCoincide:
    def test_las_cuatro_rutas_existen_y_responden_200(
        self, api_client, admin_auth_headers, contrato, todo_sembrado
    ):
        for ruta in contrato["paths"]:
            respuesta = api_client.get(f"/api/v1{ruta}", **admin_auth_headers)

            assert respuesta.status_code == 200, f"'{ruta}' respondio {respuesta.status_code}"

    def test_los_campos_devueltos_son_los_que_el_contrato_declara(
        self, api_client, admin_auth_headers, contrato, todo_sembrado
    ):
        esquemas = contrato["components"]["schemas"]

        for ruta, metodos in contrato["paths"].items():
            ref = metodos["get"]["responses"]["200"]["content"]["application/json"][
                "schema"
            ]["allOf"][1]["properties"]["data"]["items"]["$ref"]
            declarados = set(esquemas[ref.split("/")[-1]]["properties"])

            cuerpo = api_client.get(f"/api/v1{ruta}", **admin_auth_headers).json()
            assert cuerpo["data"], f"'{ruta}' sin filas: la comparacion no probaria nada"

            for fila in cuerpo["data"]:
                sobrantes = set(fila) - declarados
                faltantes = declarados - set(fila) - CONDICIONALES

                assert not sobrantes, f"'{ruta}' devuelve campos no declarados: {sobrantes}"
                assert not faltantes, f"'{ruta}' no devuelve campos declarados: {faltantes}"

    def test_todas_declaran_su_alcance(
        self, api_client, admin_auth_headers, contrato, todo_sembrado
    ):
        for ruta in contrato["paths"]:
            cuerpo = api_client.get(f"/api/v1{ruta}", **admin_auth_headers).json()

            assert cuerpo["meta"]["acotado_a"] in ("propios", "todos"), ruta

    def test_el_envelope_cumple_el_esquema_declarado(
        self, api_client, admin_auth_headers, contrato, todo_sembrado
    ):
        paginacion = set(contrato["components"]["schemas"]["Paginacion"]["properties"])

        for ruta in contrato["paths"]:
            cuerpo = api_client.get(f"/api/v1{ruta}", **admin_auth_headers).json()

            assert set(cuerpo) == {"data", "meta"}
            assert set(cuerpo["meta"]) == {"pagination", "filtros", "acotado_a"}
            assert set(cuerpo["meta"]["pagination"]) == paginacion

    def test_cada_filtro_declarado_se_acepta(
        self, api_client, admin_auth_headers, contrato, todo_sembrado
    ):
        """Ningún parámetro del contrato responde 400 con un valor válido."""
        muestras = {
            "limit": "10",
            "dir": "asc",
            "canal": "Web",
            "tipo_organizacion": "Privado",
            "etapa": "Contactado",
            "estado": "activo",
            "idprospecto": "8101",
            "tipo_asignacion": "manual",
            "regla": "visita repetida a precios",
            "desde": "2026-01-01",
            "hasta": "2026-12-31",
        }

        for ruta, metodos in contrato["paths"].items():
            for parametro in metodos["get"]["parameters"]:
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
