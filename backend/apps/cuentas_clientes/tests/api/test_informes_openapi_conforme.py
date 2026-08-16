"""T050 — la implementación coincide con el contrato, endpoint por endpoint.

Las pruebas de contrato de cada user story comprueban campos escritos a mano en
el propio fichero de prueba. Ésta lee **el OpenAPI** y compara contra él, que es
lo único que detecta una divergencia entre los dos documentos: si alguien cambia
el contrato sin tocar el código —o al revés—, las otras pruebas siguen en verde
porque su copia de la verdad no ha cambiado.

También hace de guardia sobre el propio fichero: que sea YAML válido y que
declare las ocho rutas. No es hipotético — este contrato **estaba mal formado**
hasta el 2026-08-15: una descripción sin comillas contenía `data: []`, y ninguna
herramienta lo había cargado nunca.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

CONTRATO = (
    Path(__file__).resolve().parents[5]
    / "specs"
    / "002-tactico"
    / "Cuentas-Clientes"
    / "informes-tacticos-simples"
    / "backend"
    / "contracts"
    / "informes-tacticos-simples.openapi.yaml"
)


@pytest.fixture(scope="module")
def contrato() -> dict:
    assert CONTRATO.is_file(), f"no se encuentra el contrato en {CONTRATO}"
    return yaml.safe_load(CONTRATO.read_text(encoding="utf-8"))


class TestElContratoEstaBienFormado:
    def test_es_yaml_valido_y_declara_ocho_rutas(self, contrato):
        assert len(contrato["paths"]) == 8

    def test_todas_cuelgan_del_prefijo_del_departamento(self, contrato):
        for ruta in contrato["paths"]:
            assert ruta.startswith("/informes/cuentas-clientes/")

    def test_todas_son_solo_lectura(self, contrato):
        # Un listado no muta nada: solo `GET` (contrato común §2).
        for ruta, metodos in contrato["paths"].items():
            assert set(metodos) == {"get"}, f"'{ruta}' declara {set(metodos)}"

    def test_todas_declaran_los_tres_codigos_de_error(self, contrato):
        for ruta, metodos in contrato["paths"].items():
            respuestas = set(metodos["get"]["responses"])
            assert {"200", "400", "401", "403"} <= respuestas, ruta


@pytest.mark.api
class TestLaImplementacionCoincide:
    @pytest.fixture
    def todo_sembrado(
        self,
        sesiones_sembradas,
        credenciales_temporales_sembradas,
        accesos_tecnicos_sembrados,
        onboarding_sembrado,
        transferencias_sembradas,
        usuario_multirol,
    ):
        return True

    def test_las_ocho_rutas_del_contrato_existen_y_responden_200(
        self, api_client, admin_auth_headers, director_tecnologico_auth_headers, contrato
    ):
        for ruta in contrato["paths"]:
            # `accesos-tecnicos` es el único con permiso distinto; se prueba con
            # el Administrador, que también accede a los ocho.
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
                assert set(fila) == declarados, (
                    f"'{ruta}' devuelve {set(fila)} y el contrato declara {declarados}"
                )

    def test_el_envelope_cumple_el_esquema_declarado(
        self, api_client, admin_auth_headers, contrato
    ):
        paginacion = set(contrato["components"]["schemas"]["Paginacion"]["properties"])

        for ruta in contrato["paths"]:
            cuerpo = api_client.get(f"/api/v1{ruta}", **admin_auth_headers).json()

            assert set(cuerpo) == {"data", "meta"}
            assert set(cuerpo["meta"]) == {"pagination", "filtros"}
            assert set(cuerpo["meta"]["pagination"]) == paginacion

    def test_cada_filtro_declarado_se_acepta(
        self, api_client, admin_auth_headers, contrato, todo_sembrado
    ):
        """Ningún parámetro del contrato responde 400 con un valor válido."""
        muestras = {
            "cursor": None,  # se prueba aparte: necesita un cursor real
            "limit": "10",
            "dir": "asc",
            "rol": "Administrador",
            "activo": "true",
            "idusuario": "1",
            "tipo": "Corporativo",
            "dias_minimo": "0",
            "etapa": "verificacion_documental",
            "estado": "Activo",
            "idcliente": "8001",
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
