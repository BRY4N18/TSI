"""US4 — Cierres de caso (L5).

**Una calificación ausente nunca se presenta como cero.** En una escala, cero es
el peor valor posible: presentar «no se calificó» como «se calificó con la nota
mínima» invertiría el significado, y un promedio que incluyera esos ceros
hundiría la media sin que nadie lo note. La conclusión —«la atención es mala»—
sería la contraria de lo que dicen los datos.
"""

from __future__ import annotations

import pytest

from apps.accidentes.tests.informes_fixtures import (
    CASO_AJENO,
    CASO_CERRADO,
    CASO_SIN_UBICACION,
)

pytestmark = pytest.mark.django_db

URL = "/api/v1/informes/emergencias/cierres"


def _data(resp):
    assert resp.status_code == 200, resp.content
    return resp.json()["data"]


def _por_caso(resp):
    return {f["numero_caso"]: f for f in _data(resp)}


# ── La calificación ausente ─────────────────────────────────────────────────


def test_una_calificacion_ausente_llega_ausente_y_no_como_cero(
    client, emergencias_sembradas, operador_informes_headers
):
    fila = _por_caso(
        client.get(f"{URL}?limit=500", **operador_informes_headers)
    )[CASO_AJENO]

    assert fila["calificacion"] is None
    assert fila["calificacion"] != 0


def test_una_calificacion_puesta_llega_tal_cual(
    client, emergencias_sembradas, operador_informes_headers
):
    fila = _por_caso(
        client.get(f"{URL}?limit=500", **operador_informes_headers)
    )[CASO_CERRADO]

    assert fila["calificacion"] == 5


def test_filtrar_por_con_calificacion_separa_los_dos_grupos(
    client, emergencias_sembradas, operador_informes_headers
):
    """`> 0` y no una guarda por nulidad: Pinot no tiene NULL, así que
    `IS NOT NULL` devolvería **todas** las filas como calificadas."""
    con = _data(
        client.get(f"{URL}?con_calificacion=true&limit=500",
                   **operador_informes_headers)
    )
    sin = _data(
        client.get(f"{URL}?con_calificacion=false&limit=500",
                   **operador_informes_headers)
    )

    assert con and sin
    assert all(f["calificacion"] is not None for f in con)
    assert all(f["calificacion"] is None for f in sin)
    assert not ({f["numero_caso"] for f in con} & {f["numero_caso"] for f in sin})


# ── Las observaciones ───────────────────────────────────────────────────────


def test_un_cierre_sin_observaciones_las_trae_ausentes_no_vacias(
    client, emergencias_sembradas, operador_informes_headers
):
    """«No escribió nada» y «escribió la cadena vacía» no son la misma
    afirmación sobre la calidad del cierre."""
    fila = _por_caso(
        client.get(f"{URL}?limit=500", **operador_informes_headers)
    )[CASO_SIN_UBICACION]

    assert fila["observaciones_finales"] is None
    assert fila["observaciones_finales"] != ""


def test_filtrar_por_sin_observaciones(
    client, emergencias_sembradas, operador_informes_headers
):
    filas = _data(
        client.get(f"{URL}?sin_observaciones=true&limit=500",
                   **operador_informes_headers)
    )

    assert filas
    assert all(f["observaciones_finales"] is None for f in filas)


def test_cada_cierre_muestra_caso_resultado_calificacion_y_observaciones(
    client, emergencias_sembradas, operador_informes_headers
):
    fila = _por_caso(
        client.get(f"{URL}?limit=500", **operador_informes_headers)
    )[CASO_CERRADO]

    assert fila["numero_caso"] == CASO_CERRADO
    assert fila["resultado_atencion"] == "Atendido"
    assert fila["observaciones_finales"] == "Traslado al hospital regional"


def test_filtrar_por_resultado(
    client, emergencias_sembradas, operador_informes_headers
):
    filas = _data(
        client.get(f"{URL}?resultado=Falsa alarma&limit=500",
                   **operador_informes_headers)
    )

    assert filas
    assert {f["resultado_atencion"] for f in filas} == {"Falsa alarma"}


# ── Es de estado actual: rechaza el rango ───────────────────────────────────


def test_un_rango_de_fechas_da_400(
    client, emergencias_sembradas, operador_informes_headers
):
    """⚠️ La tabla **no tiene fecha propia**: la hora de fin vive en el caso.

    Filtrar cierres por fecha exigiría cruzar con `Fact_Accidente`, y eso lo
    haría compuesto. Se rechaza en vez de aceptarlo y aplicarlo a otra cosa.
    """
    resp = client.get(f"{URL}?desde=2026-01-01", **operador_informes_headers)
    assert resp.status_code == 400, resp.content


def test_la_tabla_no_tiene_ninguna_columna_temporal_consultada():
    """La verificación que research D7 dejó pendiente, resuelta."""
    from core.repositories.accidentes import informes_cierres_repository as repo

    assert not any(
        c.startswith("fecha") or c.startswith("hora") for c in repo.COLUMNAS_CIERRE
    )


# ── Permisos ────────────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "fixture", ["cliente_informes_headers", "partner_informes_headers"]
)
def test_los_reportadores_reciben_403(
    client, emergencias_sembradas, request, fixture
):
    headers = request.getfixturevalue(fixture)
    resp = client.get(URL, **headers)

    assert resp.status_code == 403, resp.content
    assert "data" not in resp.json()


def test_sin_autenticar_es_401(client, emergencias_sembradas):
    assert client.get(URL).status_code == 401


def test_sin_resultados_es_200_con_data_vacia(
    client, emergencias_sembradas, operador_informes_headers
):
    resp = client.get(f"{URL}?resultado=Inexistente", **operador_informes_headers)

    assert resp.status_code == 200
    assert resp.json()["data"] == []
