"""T021 — contrato de los cuatro endpoints de OT18.

Verifica la forma declarada en `contracts/informes-tacticos-simples.openapi.yaml`:
el envelope, los campos de cada fila y —lo que mas importa— que un listado sin
filas responde `200` con `data: []` y **nunca 404** (SC-007). La ausencia de
resultados es una respuesta valida a una consulta valida, no un recurso que no
existe.
"""

from __future__ import annotations

import pytest

BASE = "/api/v1/informes/cuentas-clientes"

ENDPOINTS = [
    "usuarios-por-rol",
    "sesiones-activas",
    "credenciales-temporales",
    "accesos-tecnicos",
]

#: Campos que el OpenAPI declara para cada listado. La comprobacion es de
#: **igualdad**, no de inclusion: un campo de mas es tan defecto como uno de
#: menos, porque es exactamente asi como se filtra una columna sensible.
CAMPOS = {
    "usuarios-por-rol": {"nombre", "gmail", "activo", "roles"},
    "sesiones-activas": {"usuario", "navegador", "fecha_inicio"},
    "credenciales-temporales": {"usuario", "gmail", "fecha_solicitud_cambio"},
    "accesos-tecnicos": {"usuario", "usuario_servidor", "roles_servidor", "roles_negocio"},
}


@pytest.mark.api
class TestEnvelope:
    @pytest.mark.parametrize("informe", ENDPOINTS)
    def test_responde_200_con_el_envelope(self, api_client, admin_auth_headers, informe):
        respuesta = api_client.get(f"{BASE}/{informe}", **admin_auth_headers)

        assert respuesta.status_code == 200
        cuerpo = respuesta.json()
        assert set(cuerpo) == {"data", "meta"}
        assert set(cuerpo["meta"]) == {"pagination", "filtros"}
        assert set(cuerpo["meta"]["pagination"]) == {"cursor", "limit", "has_next"}
        assert cuerpo["meta"]["pagination"]["limit"] == 50

    @pytest.mark.parametrize("informe", ENDPOINTS)
    def test_data_es_una_lista(self, api_client, admin_auth_headers, informe):
        cuerpo = api_client.get(f"{BASE}/{informe}", **admin_auth_headers).json()

        assert isinstance(cuerpo["data"], list)

    @pytest.mark.parametrize("informe", ENDPOINTS)
    def test_los_campos_son_exactamente_los_del_contrato(
        self, api_client, admin_auth_headers, informe
    ):
        cuerpo = api_client.get(f"{BASE}/{informe}", **admin_auth_headers).json()

        for fila in cuerpo["data"]:
            assert set(fila) == CAMPOS[informe], (
                f"'{informe}' devolvio campos que el contrato no declara: "
                f"{set(fila) - CAMPOS[informe]}"
            )


@pytest.mark.api
class TestListadoVacio:
    """SC-007 — vacio es `200 data: []`, nunca 404."""

    def test_sin_filas_responde_200_y_lista_vacia(self, api_client, admin_auth_headers):
        # `idusuario` inexistente: la consulta es valida, el resultado vacio.
        respuesta = api_client.get(
            f"{BASE}/sesiones-activas?idusuario=999999", **admin_auth_headers
        )

        assert respuesta.status_code == 200
        cuerpo = respuesta.json()
        assert cuerpo["data"] == []
        assert cuerpo["meta"]["pagination"]["has_next"] is False
        assert cuerpo["meta"]["pagination"]["cursor"] is None


@pytest.mark.api
class TestContenido:
    """Los listados devuelven filas de verdad, no un vacio que pasa las pruebas.

    Es la comprobacion que faltaria si solo se verificara la forma: un filtro
    escrito contra un valor que no existe responde `200 data: []` y satisface
    todas las pruebas de envelope de arriba (ver la correccion de L6 y L7 en
    `informes_acceso_repository`).
    """

    def test_usuarios_por_rol_devuelve_usuarios(self, api_client, admin_auth_headers):
        cuerpo = api_client.get(f"{BASE}/usuarios-por-rol", **admin_auth_headers).json()

        assert len(cuerpo["data"]) > 0
        assert all(isinstance(f["roles"], list) for f in cuerpo["data"])

    def test_sesiones_activas_devuelve_solo_las_abiertas(
        self, api_client, admin_auth_headers, sesiones_sembradas
    ):
        cuerpo = api_client.get(f"{BASE}/sesiones-activas", **admin_auth_headers).json()

        navegadores = [f["navegador"] for f in cuerpo["data"]]
        assert "Firefox" in navegadores and "Chrome" in navegadores
        assert "Safari" not in navegadores, "la sesion cerrada no debe aparecer"

    def test_sesiones_activas_ordena_lo_mas_reciente_primero(
        self, api_client, admin_auth_headers, sesiones_sembradas
    ):
        cuerpo = api_client.get(f"{BASE}/sesiones-activas", **admin_auth_headers).json()
        fechas = [f["fecha_inicio"] for f in cuerpo["data"]]

        assert fechas == sorted(fechas, reverse=True)

    def test_credenciales_temporales_devuelve_solo_las_pendientes(
        self, api_client, admin_auth_headers, credenciales_temporales_sembradas
    ):
        cuerpo = api_client.get(
            f"{BASE}/credenciales-temporales", **admin_auth_headers
        ).json()

        # Las tres sembradas en "Cambio contraseña"; la cuarta, activa, no sale.
        assert len(cuerpo["data"]) == 3
        assert cuerpo["data"][0]["fecha_solicitud_cambio"] == "2026-08-01T00:00:00+00:00"

    def test_credenciales_temporales_ordena_lo_mas_antiguo_primero(
        self, api_client, admin_auth_headers, credenciales_temporales_sembradas
    ):
        # Es una bandeja: lo que lleva más tiempo esperando va primero.
        cuerpo = api_client.get(
            f"{BASE}/credenciales-temporales", **admin_auth_headers
        ).json()
        fechas = [f["fecha_solicitud_cambio"] for f in cuerpo["data"]]

        assert fechas == sorted(fechas)

    def test_accesos_tecnicos_devuelve_solo_las_cuentas_activas(
        self, api_client, admin_auth_headers, accesos_tecnicos_sembrados
    ):
        cuerpo = api_client.get(f"{BASE}/accesos-tecnicos", **admin_auth_headers).json()

        cuentas = {f["usuario_servidor"] for f in cuerpo["data"]}
        assert cuentas == {"admin_infra", "deploy_bot"}
        assert "cuenta_retirada" not in cuentas

    def test_accesos_tecnicos_resuelve_la_cadena_hasta_el_rol_de_negocio(
        self, api_client, admin_auth_headers, accesos_tecnicos_sembrados
    ):
        cuerpo = api_client.get(f"{BASE}/accesos-tecnicos", **admin_auth_headers).json()
        por_cuenta = {f["usuario_servidor"]: f for f in cuerpo["data"]}

        assert por_cuenta["admin_infra"]["roles_servidor"] == ["sysadmin"]
        assert por_cuenta["admin_infra"]["roles_negocio"] == ["Administrador"]

    def test_una_cuenta_sin_mapeo_a_negocio_sigue_apareciendo(
        self, api_client, admin_auth_headers, accesos_tecnicos_sembrados
    ):
        # Es acceso que nadie sabe a qué habilita: esconderlo sería lo contrario
        # de lo que CU-O08 pide vigilar.
        cuerpo = api_client.get(f"{BASE}/accesos-tecnicos", **admin_auth_headers).json()
        por_cuenta = {f["usuario_servidor"]: f for f in cuerpo["data"]}

        assert por_cuenta["deploy_bot"]["roles_servidor"] == ["despliegue"]
        assert por_cuenta["deploy_bot"]["roles_negocio"] == []
