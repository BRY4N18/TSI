"""US3 — Evidencia levantada en campo (L3 y L4).

**El contraste es la prueba.** Verificar solo un registro hecho en línea no
distinguiría una implementación correcta de otra que sella la hora de subida en
los dos campos: en línea las dos horas coinciden, y el error sería invisible.

Por eso cada comprobación mira **los dos casos a la vez**: la evidencia
capturada sin conexión debe traer dos horas **distintas**, y la tomada en línea,
dos horas **iguales**.

Y la asimetría del modelo tiene su propia prueba: la fotografía toma la hora de
registro de una columna propia y la nota de la marca genérica de modificación.
Tomar la columna equivocada solo se vería en los registros sin conexión.
"""

from __future__ import annotations

import pytest

from apps.accidentes.tests.informes_fixtures import CASO_CERRADO, TECNICO_CAMPO

pytestmark = pytest.mark.django_db

URL_FOTOS = "/api/v1/informes/emergencias/evidencia-fotos"
URL_NOTAS = "/api/v1/informes/emergencias/notas-campo"


def _data(resp):
    assert resp.status_code == 200, resp.content
    return resp.json()["data"]


# ── La hora de captura no se sustituye por la de subida ─────────────────────


@pytest.mark.parametrize("url", [URL_FOTOS, URL_NOTAS])
def test_la_evidencia_sin_conexion_trae_dos_horas_distintas(
    client, emergencias_sembradas, operador_informes_headers, url
):
    """Es donde un error de columna se vería."""
    filas = _data(client.get(f"{url}?limit=500", **operador_informes_headers))
    offline = [
        f for f in filas
        if f["sincronizado"] and f["hora_captura"] != f["hora_registro"]
    ]

    assert offline, "sin un registro sin conexion la prueba no probaria nada"
    assert offline[0]["hora_captura"] < offline[0]["hora_registro"]


@pytest.mark.parametrize("url", [URL_FOTOS, URL_NOTAS])
def test_la_evidencia_en_linea_trae_las_dos_horas_iguales(
    client, emergencias_sembradas, operador_informes_headers, url
):
    """El otro lado del contraste: aquí coinciden, y eso es correcto."""
    filas = _data(client.get(f"{url}?limit=500", **operador_informes_headers))
    en_linea = [
        f for f in filas
        if f["sincronizado"] and f["hora_captura"] == f["hora_registro"]
    ]

    assert en_linea


@pytest.mark.parametrize("url", [URL_FOTOS, URL_NOTAS])
def test_las_dos_horas_conviven_en_cada_fila(
    client, emergencias_sembradas, operador_informes_headers, url
):
    """La de subida se devuelve **aparte**, no en lugar de la de captura."""
    for fila in _data(client.get(f"{url}?limit=500", **operador_informes_headers)):
        assert "hora_captura" in fila
        assert "hora_registro" in fila
        assert fila["hora_captura"] is not None


def test_las_dos_tablas_toman_la_hora_de_registro_de_columnas_distintas():
    """⚠️ Asimetría del modelo: la nota **no tiene** columna de sincronización.

    Deuda anotada. Mientras siga así, cualquier consulta sobre sincronización de
    notas depende de una columna genérica que una actualización futura pisaría.
    """
    from core.repositories.accidentes import informes_evidencia_repository as repo

    assert "fecha_sincronizacion" in repo.COLUMNAS_FOTO
    assert "fecha_sincronizacion" not in repo.COLUMNAS_NOTA
    assert "fecha_actualizacion" in repo.COLUMNAS_NOTA


# ── Evidencia sin sincronizar: la que hay que ir a recuperar ────────────────


@pytest.mark.parametrize("url", [URL_FOTOS, URL_NOTAS])
def test_la_evidencia_sin_sincronizar_es_listable(
    client, emergencias_sembradas, operador_informes_headers, url
):
    """Es la única forma de detectar evidencia que se levantó y nunca llegó."""
    filas = _data(
        client.get(f"{url}?sincronizado=false&limit=500", **operador_informes_headers)
    )

    assert filas
    assert all(f["sincronizado"] is False for f in filas)


@pytest.mark.parametrize("url", [URL_FOTOS, URL_NOTAS])
def test_la_sin_sincronizar_conserva_su_hora_de_captura(
    client, emergencias_sembradas, operador_informes_headers, url
):
    """Nunca llegó, así que no tiene hora de registro — y aun así se sabe
    cuándo se levantó."""
    fila = _data(
        client.get(f"{url}?sincronizado=false&limit=500", **operador_informes_headers)
    )[0]

    assert fila["hora_captura"] is not None


# ── Atribución: la evidencia de cada unidad no se mezcla ────────────────────


@pytest.mark.parametrize("url", [URL_FOTOS, URL_NOTAS])
def test_cada_evidencia_se_atribuye_a_quien_la_levanto(
    client, emergencias_sembradas, operador_informes_headers, url
):
    filas = _data(
        client.get(f"{url}?caso={CASO_CERRADO}&limit=500",
                   **operador_informes_headers)
    )
    autores = {f["autor"] for f in filas}

    assert len(autores) >= 1
    assert None not in autores


@pytest.mark.parametrize("url", [URL_FOTOS, URL_NOTAS])
def test_filtrar_por_autor(
    client, emergencias_sembradas, operador_informes_headers, url
):
    todas = _data(client.get(f"{url}?limit=500", **operador_informes_headers))
    filas = _data(
        client.get(f"{url}?autor={TECNICO_CAMPO}&limit=500",
                   **operador_informes_headers)
    )

    assert filas
    assert len(filas) < len(todas), "el filtro no descarta nada: no prueba nada"
    assert {f["autor"] for f in filas} == {"Nadia Cortés"}


def test_dos_autores_sobre_el_mismo_caso_no_se_mezclan(
    client, emergencias_sembradas, operador_informes_headers
):
    filas = _data(
        client.get(f"{URL_NOTAS}?caso={CASO_CERRADO}&limit=500",
                   **operador_informes_headers)
    )
    por_autor = {f["autor"]: f["nota"] for f in filas}

    assert por_autor["Nadia Cortés"] == "Vía despejada al llegar"
    assert por_autor["Hugo Lemos"] == "Confirmado por central"


# ── Filtro por tipo, solo en notas ──────────────────────────────────────────


def test_filtrar_notas_por_tipo(
    client, emergencias_sembradas, operador_informes_headers
):
    filas = _data(
        client.get(f"{URL_NOTAS}?tipo=seguimiento&limit=500",
                   **operador_informes_headers)
    )

    assert filas
    assert {f["tipo"] for f in filas} == {"seguimiento"}


# ── Permisos ────────────────────────────────────────────────────────────────


@pytest.mark.parametrize("url", [URL_FOTOS, URL_NOTAS])
@pytest.mark.parametrize(
    "fixture", ["cliente_informes_headers", "partner_informes_headers"]
)
def test_los_reportadores_reciben_403(
    client, emergencias_sembradas, request, url, fixture
):
    headers = request.getfixturevalue(fixture)
    resp = client.get(url, **headers)

    assert resp.status_code == 403, resp.content
    assert "data" not in resp.json()


@pytest.mark.parametrize("url", [URL_FOTOS, URL_NOTAS])
def test_sin_autenticar_es_401(client, emergencias_sembradas, url):
    assert client.get(url).status_code == 401
