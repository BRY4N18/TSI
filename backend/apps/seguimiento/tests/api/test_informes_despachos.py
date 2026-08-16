"""US2 — Despachos (L2).

«En tránsito» se deriva de las **horas del propio despacho** —despachado, sin
llegada y sin retiro—, no del histórico de estados. Y `0` es el centinela de
«aún no ha ocurrido»: una guarda por nulidad sería siempre cierta y **ningún**
despacho saldría como en tránsito.
"""

from __future__ import annotations

import pytest

from apps.accidentes.tests.informes_fixtures import (
    CASO_ABIERTO,
    CASO_CERRADO,
    ORIGEN_MANUAL,
    UNIDAD,
)

pytestmark = pytest.mark.django_db

URL = "/api/v1/informes/emergencias/despachos"


def _data(resp):
    assert resp.status_code == 200, resp.content
    return resp.json()["data"]


# ── Lo que cada entrada muestra ─────────────────────────────────────────────


def test_cada_despacho_muestra_caso_unidad_origen_y_sus_horas(
    client, emergencias_sembradas, operador_informes_headers
):
    filas = _data(client.get(f"{URL}?limit=500", **operador_informes_headers))
    completo = next(f for f in filas if f["fecha_llegada"] is not None)

    assert completo["numero_caso"]
    assert completo["unidad"] == "Ambulancia 01"
    assert completo["origen_despacho"] in (
        "Asignación automática", "Asignación manual"
    )
    assert completo["fecha_despacho"]
    assert completo["fecha_retiro"]


def test_no_expone_la_posicion_de_la_unidad_ni_el_contacto_del_proveedor(
    client, emergencias_sembradas, operador_informes_headers
):
    """Misma exclusión que Red Operativa ya aplica sobre esta tabla."""
    resp = client.get(f"{URL}?limit=500", **operador_informes_headers)
    cuerpo = resp.content.decode("utf-8")

    assert "NO-DEBE-SALIR" not in cuerpo
    for fila in _data(resp):
        assert "latitud" not in fila
        assert "longitud" not in fila


# ── Misiones en tránsito ────────────────────────────────────────────────────


def test_una_mision_en_transito_es_un_despacho_sin_llegada_ni_retiro(
    client, emergencias_sembradas, operador_informes_headers
):
    filas = _data(client.get(f"{URL}?en_transito=true", **operador_informes_headers))

    assert len(filas) == 1
    transito = filas[0]
    assert transito["numero_caso"] == CASO_ABIERTO
    assert transito["fecha_llegada"] is None
    assert transito["fecha_retiro"] is None
    assert transito["en_transito"] is True


def test_las_horas_ausentes_no_se_presentan_como_1970(
    client, emergencias_sembradas, operador_informes_headers
):
    """`0` es «aún no ha ocurrido», no la época."""
    filas = _data(client.get(f"{URL}?en_transito=true", **operador_informes_headers))

    for clave in ("fecha_llegada", "fecha_retiro"):
        assert filas[0][clave] is None


def test_filtrar_por_no_en_transito_devuelve_el_complemento(
    client, emergencias_sembradas, operador_informes_headers
):
    todos = _data(client.get(f"{URL}?limit=500", **operador_informes_headers))
    en_transito = _data(
        client.get(f"{URL}?en_transito=true&limit=500", **operador_informes_headers)
    )
    fuera = _data(
        client.get(f"{URL}?en_transito=false&limit=500", **operador_informes_headers)
    )

    assert len(en_transito) + len(fuera) == len(todos)
    assert all(f["en_transito"] is False for f in fuera)


def test_el_campo_y_el_filtro_coinciden(
    client, emergencias_sembradas, operador_informes_headers
):
    """Si divergieran, el listado se contradiría dentro de la misma página."""
    todos = _data(client.get(f"{URL}?limit=500", **operador_informes_headers))
    del_filtro = {
        f["numero_caso"]
        for f in _data(
            client.get(f"{URL}?en_transito=true&limit=500",
                       **operador_informes_headers)
        )
    }
    del_campo = {f["numero_caso"] for f in todos if f["en_transito"]}

    assert del_filtro == del_campo


# ── Retiro forzado ──────────────────────────────────────────────────────────


def test_el_retiro_forzado_se_distingue_del_normal(
    client, emergencias_sembradas, operador_informes_headers
):
    """Es la traza de que la central retiró a la unidad, en vez de que la unidad
    terminara su parte."""
    filas = _data(client.get(f"{URL}?limit=500", **operador_informes_headers))
    forzados = [f for f in filas if f["retiro_forzado"]]
    normales = [f for f in filas if not f["retiro_forzado"]]

    assert forzados
    assert normales
    assert all(f["fecha_retiro"] for f in forzados)


# ── Varios despachos sobre un mismo caso ────────────────────────────────────


def test_varios_despachos_sobre_un_caso_aparecen_todos(
    client, emergencias_sembradas, operador_informes_headers
):
    """Un caso puede acumular intentos de varios orígenes; ocultarlos daría a
    entender que la asignación se resolvió a la primera."""
    filas = _data(
        client.get(f"{URL}?caso={CASO_CERRADO}&limit=500",
                   **operador_informes_headers)
    )

    assert len(filas) == 2
    assert len({f["origen_despacho"] for f in filas}) == 2


def test_filtrar_por_origen(
    client, emergencias_sembradas, operador_informes_headers
):
    filas = _data(
        client.get(f"{URL}?origen={ORIGEN_MANUAL}&limit=500",
                   **operador_informes_headers)
    )

    assert filas
    assert {f["origen_despacho"] for f in filas} == {"Asignación manual"}


def test_filtrar_por_unidad(
    client, emergencias_sembradas, operador_informes_headers
):
    filas = _data(
        client.get(f"{URL}?unidad={UNIDAD}&limit=500", **operador_informes_headers)
    )
    assert len(filas) == 3


# ── Rango opcional y permisos ───────────────────────────────────────────────


def test_sin_rango_devuelve_el_historico_completo(
    client, emergencias_sembradas, operador_informes_headers
):
    cuerpo = client.get(f"{URL}?limit=500", **operador_informes_headers).json()

    assert len(cuerpo["data"]) == 3
    assert "desde" not in cuerpo["meta"]["filtros"]


def test_con_rango_se_acota(
    client, emergencias_sembradas, operador_informes_headers
):
    filas = _data(
        client.get(f"{URL}?desde=2026-08-11&hasta=2026-08-11&limit=500",
                   **operador_informes_headers)
    )
    assert len(filas) == 1


@pytest.mark.parametrize(
    "fixture", ["cliente_informes_headers", "partner_informes_headers"]
)
def test_los_reportadores_reciben_403(
    client, emergencias_sembradas, request, fixture
):
    """Este listado es interno: describe cómo se resuelve la asignación."""
    headers = request.getfixturevalue(fixture)
    resp = client.get(URL, **headers)

    assert resp.status_code == 403, resp.content
    assert "data" not in resp.json()


def test_sin_autenticar_es_401(client, emergencias_sembradas):
    assert client.get(URL).status_code == 401


def test_la_autoridad_del_departamento_entra(
    client, emergencias_sembradas, director_operaciones_headers
):
    assert client.get(URL, **director_operaciones_headers).status_code == 200
