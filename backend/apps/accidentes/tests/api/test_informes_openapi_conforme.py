"""T036 equivalente — la implementación coincide con el contrato.

Lee **el OpenAPI** y compara contra él, ruta por ruta. Es lo único que detecta
una divergencia entre los dos documentos.

Y verifica que el contrato **no declare** coordenadas ni identidad de personas:
si aparecieran ahí, la implementación tendría permiso escrito para publicarlas.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from apps.accidentes.tests.informes_fixtures import (
    CASO_CERRADO,
    CONDADO_CONTRATADO,
    ORIGEN_MANUAL,
    SEVERIDAD_ALTA,
    TECNICO_CAMPO,
    TIPO_REPORTADO,
    UNIDAD,
)

CONTRATO = (
    Path(__file__).resolve().parents[5]
    / "specs" / "002-tactico" / "Emergencias"
    / "informes-tacticos-simples" / "backend" / "contracts"
    / "informes-tacticos-simples.openapi.yaml"
)

pytestmark = pytest.mark.django_db


@pytest.fixture(scope="module")
def contrato() -> dict:
    assert CONTRATO.is_file(), f"no se encuentra el contrato en {CONTRATO}"
    return yaml.safe_load(CONTRATO.read_text(encoding="utf-8"))


class TestElContratoEstaBienFormado:
    def test_es_yaml_valido_y_declara_cinco_rutas(self, contrato):
        assert len(contrato["paths"]) == 5

    def test_todas_cuelgan_del_prefijo_del_departamento(self, contrato):
        for ruta in contrato["paths"]:
            assert ruta.startswith("/informes/emergencias/")

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

    def test_ningun_esquema_declara_coordenadas_ni_identidad(self, contrato):
        """El contrato es el permiso escrito: aquí es donde hay que negarlo.

        Se miran los **nombres de campo** de los esquemas, no el texto libre:
        la descripción del documento nombra esas palabras precisamente para
        declarar la exclusión, y buscarlas ahí haría fallar la prueba por decir
        lo correcto.
        """
        campos = {
            nombre.lower()
            for esquema in contrato["components"]["schemas"].values()
            for nombre in esquema.get("properties", {})
        }

        for prohibida in ("latitud", "longitud", "latitudinicio", "longitudinicio",
                          "conductor", "implicado", "vehiculo_placa",
                          "descripcion"):
            assert prohibida not in campos, prohibida

        assert not any("latitud" in c or "longitud" in c for c in campos)

    def test_el_enum_de_situacion_coincide_con_lo_implementado(self, contrato):
        """⚠️ El contrato declaraba `borrador` y **no se puede dar**.

        `BORRADOR` es un estado formal que vive en el histórico. Un caso en
        borrador es `activo = true` sin hora de fin — idéntico a cualquier otro
        en curso—, así que ofrecerlo devolvería todos los casos activos
        etiquetados como detenidos: la forma correcta con el contenido
        equivocado. FR-002 y FR-008 se contradicen, y gana FR-008.
        """
        from core.repositories.accidentes.informes_casos_repository import (
            SITUACIONES,
        )

        parametros = contrato["paths"]["/informes/emergencias/casos"]["get"][
            "parameters"
        ]
        situacion = next(
            p for p in parametros if p.get("name") == "situacion"
        )

        assert set(situacion["schema"]["enum"]) == set(SITUACIONES)


class TestLaImplementacionCoincide:
    def test_las_cinco_rutas_responden_200(
        self, client, operador_informes_headers, contrato, emergencias_sembradas
    ):
        for ruta in contrato["paths"]:
            respuesta = client.get(f"/api/v1{ruta}", **operador_informes_headers)

            assert respuesta.status_code == 200, (
                f"'{ruta}' respondio {respuesta.status_code}"
            )

    def test_los_campos_devueltos_son_los_que_el_contrato_declara(
        self, client, operador_informes_headers, contrato, emergencias_sembradas
    ):
        esquemas = contrato["components"]["schemas"]

        for ruta, metodos in contrato["paths"].items():
            ref = metodos["get"]["responses"]["200"]["content"]["application/json"][
                "schema"
            ]["allOf"][1]["properties"]["data"]["items"]["$ref"]
            declarados = set(esquemas[ref.split("/")[-1]]["properties"])

            cuerpo = client.get(
                f"/api/v1{ruta}?limit=500", **operador_informes_headers
            ).json()
            assert cuerpo["data"], f"'{ruta}' sin filas: no probaria nada"

            for fila in cuerpo["data"]:
                sobrantes = set(fila) - declarados
                faltantes = declarados - set(fila)

                assert not sobrantes, f"'{ruta}' devuelve no declarados: {sobrantes}"
                assert not faltantes, f"'{ruta}' no devuelve declarados: {faltantes}"

    def test_el_envelope_cumple_el_esquema(
        self, client, operador_informes_headers, contrato, emergencias_sembradas
    ):
        paginacion = set(contrato["components"]["schemas"]["Paginacion"]["properties"])

        for ruta in contrato["paths"]:
            cuerpo = client.get(f"/api/v1{ruta}", **operador_informes_headers).json()

            assert set(cuerpo) == {"data", "meta"}
            assert {"pagination", "filtros", "acotado_a"} <= set(cuerpo["meta"])
            assert set(cuerpo["meta"]["pagination"]) == paginacion

    def test_el_contrato_declara_el_valor_propio_del_eje(self, contrato):
        """`zonas_contratadas` no es `propios`: los accidentes de una zona
        contratada no son del cliente."""
        meta = contrato["components"]["schemas"]["RespuestaListado"][
            "properties"
        ]["meta"]

        assert "zonas_contratadas" in meta["properties"]["acotado_a"]["enum"]

    def test_cada_filtro_declarado_se_acepta(
        self, client, operador_informes_headers, contrato, emergencias_sembradas
    ):
        muestras = {
            "cursor": "", "limit": "10", "dir": "asc",
            "desde": "2026-01-01", "hasta": "2026-12-31",
            "severidad": str(SEVERIDAD_ALTA),
            "condado": str(CONDADO_CONTRATADO),
            "tipo_reportado": str(TIPO_REPORTADO),
            "situacion": "cerrado",
            "origen": str(ORIGEN_MANUAL), "unidad": str(UNIDAD),
            "caso": CASO_CERRADO, "en_transito": "false",
            "sincronizado": "true", "autor": str(TECNICO_CAMPO),
            "tipo": "observacion",
            "resultado": "Atendido", "sin_observaciones": "false",
            "con_calificacion": "true",
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
                    f"/api/v1{ruta}?{nombre}={valor}", **operador_informes_headers
                )
                assert respuesta.status_code == 200, (
                    f"'{ruta}' rechaza '{nombre}={valor}', que el contrato "
                    f"declara valido"
                )

    def test_sin_autenticar_todas_dan_401(self, client, contrato):
        for ruta in contrato["paths"]:
            assert client.get(f"/api/v1{ruta}").status_code == 401, ruta

    def test_solo_casos_admite_al_cliente(
        self, client, cliente_informes_headers, contrato, emergencias_sembradas
    ):
        for ruta in contrato["paths"]:
            esperado = 200 if ruta.endswith("/casos") else 403
            respuesta = client.get(f"/api/v1{ruta}", **cliente_informes_headers)

            assert respuesta.status_code == esperado, ruta
