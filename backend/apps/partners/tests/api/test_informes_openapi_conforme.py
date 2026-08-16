"""T022, T030, T038 y T043 — la implementación coincide con el contrato.

Lee **el OpenAPI** y compara contra él, ruta por ruta. Es lo único que detecta
una divergencia entre los dos documentos: las pruebas de cada user story
comparan contra lo que uno recuerda del contrato, no contra el contrato.

También verifica que el contrato **no declare** el secreto de autenticación ni
el teléfono de avisos: si un día apareciera ahí, la implementación tendría
permiso escrito para publicarlo.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from apps.partners.tests.conftest import CUENTA_A, PARTNER_A

CONTRATO = (
    Path(__file__).resolve().parents[5]
    / "specs" / "002-tactico" / "Partners-API"
    / "informes-tacticos-simples" / "backend" / "contracts"
    / "informes-tacticos-simples.openapi.yaml"
)

#: Solo los tres listados de acceso admiten al partner; los dos de gestión no.
DE_GESTION = ("/versiones-contrato", "/alcance-datos")

#: El contrato los declara ausentes cuando el partner no está suspendido.
#: Emitirlos vacíos en un partner activo sugeriría que la pregunta le aplica.
CONDICIONALES = {"fecha_suspension", "motivo_suspension"}

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
            assert ruta.startswith("/informes/partners-api/")

    def test_todas_son_solo_lectura(self, contrato):
        for ruta, metodos in contrato["paths"].items():
            assert set(metodos) == {"get"}, f"'{ruta}' declara {set(metodos)}"

    def test_todas_declaran_los_codigos_de_error(self, contrato):
        for ruta, metodos in contrato["paths"].items():
            assert {"200", "400", "401", "403"} <= set(
                metodos["get"]["responses"]
            ), ruta

    def test_el_envelope_exige_acotado_a(self, contrato):
        meta = contrato["components"]["schemas"]["RespuestaListado"]["properties"]["meta"]

        assert "acotado_a" in meta["required"]

    def test_ninguna_respuesta_declara_el_secreto_ni_el_telefono(self, contrato):
        """El contrato es el permiso escrito: aquí es donde hay que negarlo."""
        texto = json.dumps(contrato).lower()

        for prohibida in ("client_secret", "secret_hash", "telefono_sms"):
            assert prohibida not in texto


class TestLaImplementacionCoincide:
    def test_las_cinco_rutas_responden_200(self, client, gestor_headers, contrato,
                                           todo_sembrado):
        for ruta in contrato["paths"]:
            respuesta = client.get(f"/api/v1{ruta}", **gestor_headers)

            assert respuesta.status_code == 200, (
                f"'{ruta}' respondió {respuesta.status_code}"
            )

    def test_los_campos_devueltos_son_los_que_el_contrato_declara(
        self, client, gestor_headers, contrato, todo_sembrado
    ):
        esquemas = contrato["components"]["schemas"]

        for ruta, metodos in contrato["paths"].items():
            ref = metodos["get"]["responses"]["200"]["content"]["application/json"][
                "schema"
            ]["allOf"][1]["properties"]["data"]["items"]["$ref"]
            declarados = set(esquemas[ref.split("/")[-1]]["properties"])

            cuerpo = client.get(f"/api/v1{ruta}?limit=500", **gestor_headers).json()
            assert cuerpo["data"], f"'{ruta}' sin filas: la comparación no probaría nada"

            for fila in cuerpo["data"]:
                sobrantes = set(fila) - declarados
                faltantes = declarados - set(fila) - CONDICIONALES

                assert not sobrantes, f"'{ruta}' devuelve no declarados: {sobrantes}"
                assert not faltantes, f"'{ruta}' no devuelve declarados: {faltantes}"

    def test_los_campos_condicionales_solo_salen_cuando_aplican(
        self, client, gestor_headers, contrato, todo_sembrado
    ):
        """La condicionalidad que el contrato declara se cumple en los dos
        sentidos: presentes en el suspendido, ausentes en el resto."""
        filas = client.get(
            "/api/v1/informes/partners-api/partners?limit=500", **gestor_headers
        ).json()["data"]

        suspendidos = [f for f in filas if f["estado_acceso"] == "Suspendido"]
        assert suspendidos, "sin partner suspendido esta prueba no probaría nada"

        for fila in filas:
            aplica = fila["estado_acceso"] == "Suspendido"
            assert (CONDICIONALES <= set(fila)) is aplica, fila["nombre_partner"]

        assert suspendidos[0]["motivo_suspension"] == "impago"

    def test_el_envelope_cumple_el_esquema(
        self, client, gestor_headers, contrato, todo_sembrado
    ):
        paginacion = set(contrato["components"]["schemas"]["Paginacion"]["properties"])

        for ruta in contrato["paths"]:
            cuerpo = client.get(f"/api/v1{ruta}", **gestor_headers).json()

            assert set(cuerpo) == {"data", "meta"}
            assert {"pagination", "filtros", "acotado_a"} <= set(cuerpo["meta"])
            assert set(cuerpo["meta"]["pagination"]) == paginacion

    def test_cada_filtro_declarado_se_acepta(
        self, client, gestor_headers, contrato, todo_sembrado
    ):
        """Un filtro declarado y rechazado es una promesa incumplida."""
        muestras = {
            "cursor": "", "limit": "10", "dir": "asc",
            "partner": str(PARTNER_A),
            "estado": {"/informes/partners-api/partners": "Suspendido",
                       "/informes/partners-api/versiones-contrato": "retirada"},
            "plan": "Profesional",
            "entorno": "Sandbox", "activa": "true", "caduca_en_dias": "30",
            "desde": "2026-01-01", "hasta": "2026-12-31",
            "tipo_cambio": "reactivacion",
            "servicio": "4701", "cuenta": str(CUENTA_A), "frecuencia": "mensual",
        }

        for ruta, metodos in contrato["paths"].items():
            for parametro in metodos["get"].get("parameters", []):
                nombre = (
                    parametro.get("name")
                    or parametro["$ref"].split("/")[-1].lower()
                )
                valor = muestras.get(nombre)
                # El mismo nombre significa cosas distintas según la ruta.
                if isinstance(valor, dict):
                    valor = valor.get(ruta)
                if valor is None:
                    continue

                respuesta = client.get(
                    f"/api/v1{ruta}?{nombre}={valor}", **gestor_headers
                )
                assert respuesta.status_code == 200, (
                    f"'{ruta}' rechaza '{nombre}={valor}', que el contrato "
                    f"declara válido"
                )

    def test_las_rutas_de_gestion_niegan_al_partner(
        self, client, partner_a_informes_headers, contrato, todo_sembrado
    ):
        for ruta in contrato["paths"]:
            esperado = 403 if ruta.endswith(DE_GESTION) else 200
            respuesta = client.get(f"/api/v1{ruta}", **partner_a_informes_headers)

            assert respuesta.status_code == esperado, ruta

    def test_sin_autenticar_todas_dan_401(self, client, contrato):
        for ruta in contrato["paths"]:
            assert client.get(f"/api/v1{ruta}").status_code == 401, ruta
