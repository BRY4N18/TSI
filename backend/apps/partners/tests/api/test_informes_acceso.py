"""US1 — Partners y credenciales (L1, L2).

**T016 no es una prueba de contrato más.** El `client_secret_hash` es del mismo
orden que el medio de cobro de Suscripciones: con él, cualquiera que lea la
respuesta se autentica como el partner. Y lo que verifica va más allá de la
respuesta — **que el repositorio enumere las columnas que devuelve**.

Una lista negra pasaría esta prueba hoy y fallaría el día que alguien añada una
columna sensible a la tabla: falla abierta y en silencio. Por eso se comprueban
las dos cosas, la respuesta y la forma de la consulta.
"""

from __future__ import annotations

import re

import pytest

from apps.partners.domain_constants import ENTORNO_PRODUCCION, ENTORNO_SANDBOX
from apps.partners.tests.conftest import (
    PARTNER_A,
    PARTNER_B,
    SECRETO,
)

pytestmark = pytest.mark.django_db

URL_PARTNERS = "/api/v1/informes/partners-api/partners"
URL_CREDENCIALES = "/api/v1/informes/partners-api/credenciales"


def _data(resp):
    assert resp.status_code == 200, resp.content
    return resp.json()["data"]


# ── T016 — el secreto no sale, ni por la respuesta ni por la consulta ────────


def test_credenciales_no_exponen_el_secreto_en_la_respuesta(
    client, todo_sembrado, gestor_headers
):
    resp = client.get(URL_CREDENCIALES, **gestor_headers)
    cuerpo = resp.content.decode("utf-8")

    assert resp.status_code == 200, cuerpo
    assert SECRETO not in cuerpo
    for fila in _data(resp):
        assert "client_secret_hash" not in fila
        assert "secret" not in " ".join(fila.keys()).lower()


def test_el_repositorio_enumera_las_columnas_en_vez_de_pedirlas_todas():
    """La lista blanca es lo que hace que la prueba anterior siga valiendo.

    Con `SELECT *`, añadir mañana una columna sensible a `Dim_CredencialAPI` la
    publicaría sin que ninguna prueba se entere.
    """
    from core.repositories.partners import informes_acceso_repository as repo

    fuente = open(repo.__file__, encoding="utf-8").read()
    consultas = re.findall(r'"(SELECT [^"]+)"', fuente)

    assert consultas, "no se encontró ninguna consulta literal"
    for consulta in consultas:
        assert "SELECT *" not in consulta, consulta

    assert "client_secret_hash" not in repo.COLUMNAS_CREDENCIAL


# ── T017 — lo que este listado no puede decir ────────────────────────────────


def test_el_listado_de_credenciales_no_inventa_el_motivo_de_la_inactividad(
    client, todo_sembrado, gestor_headers
):
    """`activo=False` en la credencial **no dice por qué**.

    Puede ser una revocación decidida por el partner o una desactivación en
    cascada por suspensión. La fila de `Dim_CredencialAPI` es idéntica en ambos
    casos: quien quiera el motivo tiene que ir a la bitácora (US2).
    """
    for fila in _data(client.get(URL_CREDENCIALES, **gestor_headers)):
        assert "motivo" not in fila
        assert "motivo_desactivacion" not in fila
        assert "revocada" not in fila


# ── T018 — pruebas y producción coexisten ────────────────────────────────────


def test_las_credenciales_de_pruebas_y_produccion_coexisten(
    client, todo_sembrado, gestor_headers
):
    """Activar producción no elimina el acceso de pruebas."""
    filas = _data(
        client.get(f"{URL_CREDENCIALES}?partner={PARTNER_A}", **gestor_headers)
    )
    entornos = {f["entorno"] for f in filas}

    assert entornos == {ENTORNO_SANDBOX, ENTORNO_PRODUCCION}


def test_filtrar_por_entorno_devuelve_solo_ese_entorno(
    client, todo_sembrado, gestor_headers
):
    filas = _data(
        client.get(
            f"{URL_CREDENCIALES}?entorno={ENTORNO_PRODUCCION}", **gestor_headers
        )
    )
    assert filas
    assert {f["entorno"] for f in filas} == {ENTORNO_PRODUCCION}


# ── T019 / T020 — acotamiento ────────────────────────────────────────────────


def test_un_partner_solo_ve_lo_suyo(
    client, todo_sembrado, partner_a_informes_headers
):
    """Con dos cuentas pobladas, esta prueba distingue acotar de no acotar."""
    resp = client.get(URL_PARTNERS, **partner_a_informes_headers)
    cuerpo = resp.json()

    nombres = {f["nombre_partner"] for f in cuerpo["data"]}
    assert "Silva Integraciones" in nombres
    assert "Andina Conecta" not in nombres
    assert cuerpo["meta"]["acotado_a"] == "propios"


def test_el_gestor_ve_las_dos_cuentas(client, todo_sembrado, gestor_headers):
    resp = client.get(URL_PARTNERS, **gestor_headers)
    cuerpo = resp.json()

    nombres = {f["nombre_partner"] for f in cuerpo["data"]}
    assert {"Silva Integraciones", "Andina Conecta"} <= nombres
    assert cuerpo["meta"]["acotado_a"] == "todos"


def test_pedir_un_partner_ajeno_da_403(
    client, todo_sembrado, partner_a_informes_headers
):
    resp = client.get(
        f"{URL_PARTNERS}?partner={PARTNER_B}", **partner_a_informes_headers
    )
    assert resp.status_code == 403, resp.content


def test_un_partner_suspendido_conserva_el_acceso_a_sus_listados(
    client, todo_sembrado, partner_a_informes_headers
):
    """Suspender el consumo de la API no retira la consulta de la bitácora.

    El partner suspendido es precisamente quien más necesita ver por qué.
    """
    filas = _data(client.get(URL_PARTNERS, **partner_a_informes_headers))
    assert "Silva Legacy" in {f["nombre_partner"] for f in filas}


# ── T021 — un estado nuevo del dominio no debe producir un 400 engañoso ──────


def test_el_filtro_de_estado_se_valida_contra_las_constantes_del_dominio():
    """Copiar los estados crearía una segunda fuente de verdad.

    El día que el dominio añada un estado, un filtro con la lista copiada lo
    rechazaría con «no es válido» — cuando sí lo es.
    """
    from apps.partners import domain_constants
    from apps.partners.views import informes_views

    del_dominio = {
        v for k, v in vars(domain_constants).items()
        if k.startswith("ESTADO_") and isinstance(v, str)
        and not k.startswith("ESTADO_ACCESO_")
    }
    assert set(informes_views.ESTADOS_PARTNER) == del_dominio


def test_un_estado_desconocido_da_400(client, todo_sembrado, gestor_headers):
    resp = client.get(f"{URL_PARTNERS}?estado=Inventado", **gestor_headers)
    assert resp.status_code == 400, resp.content
