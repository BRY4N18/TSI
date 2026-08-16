"""T036 — la implementación coincide con el contrato.

Lee **el OpenAPI** y compara contra él, ruta por ruta. Es lo único que detecta
una divergencia entre los dos documentos: las pruebas de cada user story
comparan contra lo que uno recuerda del contrato, no contra el contrato.

También verifica que el contrato **no declare** el texto del mensaje ni la
descripción del reporte: si un día aparecieran ahí, la implementación tendría
permiso escrito para publicarlos.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from apps.soporte_cliente.tests.conftest import CUENTA_CLIENTE

CONTRATO = (
    Path(__file__).resolve().parents[5]
    / "specs" / "002-tactico" / "Soporte-Cliente"
    / "informes-tacticos-simples" / "backend" / "contracts"
    / "informes-tacticos-simples.openapi.yaml"
)

pytestmark = pytest.mark.django_db


@pytest.fixture(scope="module")
def contrato() -> dict:
    assert CONTRATO.is_file(), f"no se encuentra el contrato en {CONTRATO}"
    return yaml.safe_load(CONTRATO.read_text(encoding="utf-8"))


class TestElContratoEstaBienFormado:
    def test_es_yaml_valido_y_declara_dos_rutas(self, contrato):
        assert len(contrato["paths"]) == 2

    def test_todas_cuelgan_del_prefijo_del_departamento(self, contrato):
        for ruta in contrato["paths"]:
            assert ruta.startswith("/informes/soporte-cliente/")

    def test_todas_son_solo_lectura(self, contrato):
        for ruta, metodos in contrato["paths"].items():
            assert set(metodos) == {"get"}, f"'{ruta}' declara {set(metodos)}"

    def test_todas_declaran_los_codigos_de_error(self, contrato):
        for ruta, metodos in contrato["paths"].items():
            assert {"200", "400", "401", "403"} <= set(
                metodos["get"]["responses"]
            ), ruta

    def test_el_envelope_exige_acotado_a(self, contrato):
        meta = contrato["components"]["schemas"]["RespuestaListado"][
            "properties"
        ]["meta"]

        assert "acotado_a" in meta["required"]

    def test_el_enum_de_situacion_coincide_con_el_dominio(self, contrato):
        """El contrato declaraba **cuatro** valores y el dominio tiene cinco.

        `cumplido` lo escribe `resolver_ticket_service` al resolver dentro de
        plazo. Con el enum corto, el filtro documentado rechazaria un valor
        legitimo y seria imposible listar los tickets resueltos a tiempo.

        Esta prueba cierra el lazo: si el dominio gana un sexto valor y el
        contrato no, falla aqui en vez de aparecer como un `400` inexplicable.
        """
        from apps.soporte_cliente import domain_constants as dc

        del_dominio = {
            v for k, v in vars(dc).items()
            if k.startswith("SLA_") and isinstance(v, str)
        }
        declarado = set(
            contrato["components"]["schemas"]["Ticket"]["properties"][
                "situacion_compromiso"
            ]["enum"]
        )

        assert declarado == del_dominio

    def test_el_enum_de_estado_coincide_con_los_estados_del_ticket(self, contrato):
        """El contrato declaraba `estado` como texto libre y el backend **sí** lo
        valida contra las constantes del dominio.

        Sin el enum declarado, el frontend no puede ofrecer un desplegable con
        los valores buenos sin copiarlos de un sitio que nadie comprueba — y un
        `400` evitable acaba llegando al usuario.
        """
        from apps.soporte_cliente import informes_views

        parametros = contrato["paths"]["/informes/soporte-cliente/tickets"]["get"][
            "parameters"
        ]
        estado = next(p for p in parametros if p.get("name") == "estado")

        assert set(estado["schema"]["enum"]) == set(informes_views.ESTADOS_TICKET)

    def test_ninguna_respuesta_declara_el_texto_interno(self, contrato):
        texto = json.dumps(contrato).lower()

        for prohibida in ("mensaje", "es_nota_interna", "descripcion"):
            assert f'"{prohibida}"' not in texto


class TestLaImplementacionCoincide:
    def test_las_dos_rutas_responden_200(
        self, client, agente_informes_headers, contrato, todo_sembrado
    ):
        for ruta in contrato["paths"]:
            respuesta = client.get(f"/api/v1{ruta}", **agente_informes_headers)

            assert respuesta.status_code == 200, (
                f"'{ruta}' respondio {respuesta.status_code}"
            )

    def test_los_campos_devueltos_son_los_que_el_contrato_declara(
        self, client, agente_informes_headers, contrato, todo_sembrado
    ):
        esquemas = contrato["components"]["schemas"]

        for ruta, metodos in contrato["paths"].items():
            ref = metodos["get"]["responses"]["200"]["content"]["application/json"][
                "schema"
            ]["allOf"][1]["properties"]["data"]["items"]["$ref"]
            declarados = set(esquemas[ref.split("/")[-1]]["properties"])

            cuerpo = client.get(
                f"/api/v1{ruta}?limit=500", **agente_informes_headers
            ).json()
            assert cuerpo["data"], f"'{ruta}' sin filas: no probaria nada"

            for fila in cuerpo["data"]:
                sobrantes = set(fila) - declarados
                faltantes = declarados - set(fila)

                assert not sobrantes, f"'{ruta}' devuelve no declarados: {sobrantes}"
                assert not faltantes, f"'{ruta}' no devuelve declarados: {faltantes}"

    def test_el_envelope_cumple_el_esquema(
        self, client, agente_informes_headers, contrato, todo_sembrado
    ):
        paginacion = set(contrato["components"]["schemas"]["Paginacion"]["properties"])

        for ruta in contrato["paths"]:
            cuerpo = client.get(f"/api/v1{ruta}", **agente_informes_headers).json()

            assert set(cuerpo) == {"data", "meta"}
            assert {"pagination", "filtros", "acotado_a"} <= set(cuerpo["meta"])
            assert set(cuerpo["meta"]["pagination"]) == paginacion

    def test_cada_filtro_declarado_se_acepta(
        self, client, agente_informes_headers, contrato, todo_sembrado
    ):
        muestras = {
            "cursor": "", "limit": "10", "dir": "asc",
            "cuenta": str(CUENTA_CLIENTE),
            "estado": "Abierto", "situacion_compromiso": "en curso",
            "prioridad": "Media", "tipo_incidencia": "Consulta",
            "agente": "6504", "con_factura": "true",
            "desde": "2026-01-01", "hasta": "2026-12-31",
            "tipo_escalado": "manual",
        }

        for ruta, metodos in contrato["paths"].items():
            for parametro in metodos["get"].get("parameters", []):
                nombre = (
                    parametro.get("name")
                    or parametro["$ref"].split("/")[-1].lower()
                )
                valor = muestras.get(nombre)
                if valor is None:
                    continue

                respuesta = client.get(
                    f"/api/v1{ruta}?{nombre}={valor}", **agente_informes_headers
                )
                assert respuesta.status_code == 200, (
                    f"'{ruta}' rechaza '{nombre}={valor}', que el contrato "
                    f"declara valido"
                )

    def test_sin_autenticar_las_dos_dan_401(self, client, contrato):
        for ruta in contrato["paths"]:
            assert client.get(f"/api/v1{ruta}").status_code == 401, ruta
