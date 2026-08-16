"""US3 — Versiones del contrato y alcance de datos (L4, L5).

**T035 es la prueba de mayor consecuencia de este módulo.** Un cliente sin
alcance configurado no tiene acceso ilimitado: tiene un alcance que nadie
acordó todavía. Devolver una lista vacía de zonas invita a leerla como «todas».
"""

from __future__ import annotations

import pytest

from apps.partners.domain_constants import VERSION_RETIRADA, VERSION_VIGENTE
from apps.partners.tests.conftest import CUENTA_A, CUENTA_SIN_ALCANCE

pytestmark = pytest.mark.django_db

URL_VERSIONES = "/api/v1/informes/partners-api/versiones-contrato"
URL_ALCANCE = "/api/v1/informes/partners-api/alcance-datos"


def _data(resp):
    assert resp.status_code == 200, resp.content
    return resp.json()["data"]


# ── T035 — sin alcance configurado ≠ acceso ilimitado ───────────────────────


def test_sin_alcance_configurado_las_zonas_llegan_ausentes_no_vacias(
    client, todo_sembrado, gestor_headers
):
    filas = _data(
        client.get(f"{URL_ALCANCE}?cuenta={CUENTA_SIN_ALCANCE}", **gestor_headers)
    )

    assert len(filas) == 1
    zonas = filas[0]["zonas_geograficas"]
    # `None` dice «no se ha configurado». `[]` o `""` se leen como «ninguna
    # restricción», que es justo la lectura contraria.
    assert zonas is None
    assert zonas != []
    assert zonas != ""


def test_con_alcance_configurado_las_zonas_llegan_tal_cual(
    client, todo_sembrado, gestor_headers
):
    filas = _data(client.get(f"{URL_ALCANCE}?cuenta={CUENTA_A}", **gestor_headers))

    assert filas[0]["zonas_geograficas"] == "Norte,Centro"
    assert filas[0]["frecuencia_reportes"] == "mensual"


def test_el_alcance_no_expone_el_telefono_de_avisos(
    client, todo_sembrado, gestor_headers
):
    """`telefono_sms` es dato de contacto, no alcance contratado."""
    resp = client.get(URL_ALCANCE, **gestor_headers)

    assert "NO-DEBE-SALIR" not in resp.content.decode("utf-8")
    for fila in _data(resp):
        assert "telefono_sms" not in fila


# ── T036 — las versiones retiradas siguen apareciendo ───────────────────────


def test_las_versiones_retiradas_se_incluyen(client, todo_sembrado, gestor_headers):
    """Una versión retirada sigue explicando por qué una integración dejó de
    funcionar: omitirla deja sin respuesta justo esa pregunta."""
    filas = _data(client.get(URL_VERSIONES, **gestor_headers))
    estados = {f["estado"] for f in filas}

    assert VERSION_RETIRADA in estados
    assert VERSION_VIGENTE in estados


def test_la_version_vigente_no_tiene_fecha_de_retiro(
    client, todo_sembrado, gestor_headers
):
    """`0` es el centinela de «no retirada», no la época de 1970."""
    por_estado = {f["estado"]: f for f in _data(client.get(URL_VERSIONES, **gestor_headers))}

    assert por_estado[VERSION_VIGENTE]["fecha_retiro"] is None
    retirada = por_estado[VERSION_RETIRADA]["fecha_retiro"]
    assert retirada is not None
    assert not retirada.startswith("1970")


# ── T037 — estos dos listados son materia de gestor ─────────────────────────


@pytest.mark.parametrize("url", [URL_VERSIONES, URL_ALCANCE])
def test_un_partner_no_accede_a_los_listados_de_gestion(
    client, todo_sembrado, partner_a_informes_headers, url
):
    """El alcance describe lo que cada CLIENTE contrató, no lo que el partner
    consume: no es materia de quien consume la plataforma."""
    resp = client.get(url, **partner_a_informes_headers)
    assert resp.status_code == 403, resp.content


@pytest.mark.parametrize("url", [URL_VERSIONES, URL_ALCANCE])
def test_sin_autenticar_da_401(client, todo_sembrado, url):
    assert client.get(url).status_code == 401


@pytest.mark.parametrize("url", [URL_VERSIONES, URL_ALCANCE])
def test_el_alcance_declarado_es_todos(client, todo_sembrado, gestor_headers, url):
    cuerpo = client.get(url, **gestor_headers).json()
    assert cuerpo["meta"]["acotado_a"] == "todos"
