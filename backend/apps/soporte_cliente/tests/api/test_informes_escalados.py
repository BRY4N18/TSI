"""US2 — Escalados (L2).

**T028 comprueba una ausencia, no un filtro.** No basta con que el texto de los
mensajes no aparezca en la respuesta: la columna **no debe consultarse**. Un
filtro correcto sigue siendo un filtro que alguien puede olvidar al añadir un
campo dentro de seis meses, y el fallo sería silencioso — la respuesta
conservaría la forma esperada, solo que con notas internas dentro.

**T026 comprueba que las dos señales de autoría coinciden.** Si se
contradijeran, el dato estaría corrupto; decidir por el tipo de acción lo
ocultaría.
"""

from __future__ import annotations

import re

import pytest

from apps.soporte_cliente.tests.conftest import CUENTA_PARTNER, NOTA_INTERNA

pytestmark = pytest.mark.django_db

URL = "/api/v1/informes/soporte-cliente/escalados"


def _data(resp):
    assert resp.status_code == 200, resp.content
    return resp.json()["data"]


# ── T028 — el texto no se consulta ──────────────────────────────────────────


def test_ningun_texto_de_mensaje_aparece_en_la_respuesta(
    client, todo_sembrado, agente_informes_headers
):
    resp = client.get(f"{URL}?limit=500", **agente_informes_headers)
    cuerpo = resp.content.decode("utf-8")

    assert resp.status_code == 200, cuerpo
    assert NOTA_INTERNA not in cuerpo
    assert "NOTA-INTERNA" not in cuerpo
    for fila in _data(resp):
        assert "mensaje" not in fila
        assert "es_nota_interna" not in fila


def test_el_repositorio_no_consulta_la_columna_del_mensaje():
    """La protección real: no se lee y luego se descarta, **no se lee**."""
    from core.repositories.soporte import informes_escalados_repository as repo

    fuente = open(repo.__file__, encoding="utf-8").read()
    consultas = re.findall(r'"(SELECT [^"]+)"', fuente)

    assert consultas
    for consulta in consultas:
        assert "SELECT *" not in consulta, consulta

    assert "mensaje" not in repo.COLUMNAS_ESCALADO
    assert "es_nota_interna" not in repo.COLUMNAS_ESCALADO


# ── T026 — las dos señales de autoría coinciden ─────────────────────────────


def test_ningun_automatico_tiene_autor_y_ningun_manual_carece_de_el(
    client, todo_sembrado, agente_informes_headers
):
    filas = _data(client.get(f"{URL}?limit=500", **agente_informes_headers))

    assert filas
    for fila in filas:
        if fila["tipo_escalado"] == "automatico":
            assert fila["autor"] is None, fila
        else:
            assert fila["autor"] is not None, fila


def test_el_escalado_automatico_no_se_atribuye_a_la_persona_que_lo_recibio(
    client, todo_sembrado, agente_informes_headers
):
    """El supervisor que lo recibe es destinatario, no autor.

    Atribuírselo fue el defecto que la corrección anterior resolvió.
    """
    filas = _data(client.get(f"{URL}?tipo_escalado=automatico",
                             **agente_informes_headers))

    assert filas
    for fila in filas:
        assert fila["autor"] is None
        assert fila["tipo_escalado"] == "automatico"


def test_el_escalado_manual_identifica_a_la_persona(
    client, todo_sembrado, agente_informes_headers
):
    filas = _data(client.get(f"{URL}?tipo_escalado=manual",
                             **agente_informes_headers))

    assert filas
    assert all(f["autor"] == "Bruno Salas" for f in filas)


def test_cada_entrada_trae_ticket_estados_y_fecha(
    client, todo_sembrado, agente_informes_headers
):
    fila = _data(client.get(f"{URL}?tipo_escalado=manual",
                            **agente_informes_headers))[0]

    assert fila["numero_ticket"]
    assert fila["cuenta"]
    assert fila["estado_nuevo"] == "Escalado"
    assert fila["estado_anterior"]
    assert fila["fecha"]


# ── T027 — un aviso de plazo no es un escalado ──────────────────────────────


def test_un_aviso_de_plazo_proximo_no_aparece(
    client, todo_sembrado, agente_informes_headers
):
    """El ticket no cambió de agente ni de nivel: contarlo inflaría el recuento
    de escalados con acciones que no derivaron nada."""
    filas = _data(client.get(f"{URL}?limit=500", **agente_informes_headers))

    # El único cambio del ticket 6702 fue un aviso y un cierre automático.
    assert all(f["estado_nuevo"] == "Escalado" for f in filas)
    assert "Cerrado" not in {f["estado_nuevo"] for f in filas}


def test_solo_aparecen_los_dos_tipos_que_son_escalados(
    client, todo_sembrado, agente_informes_headers
):
    filas = _data(client.get(f"{URL}?limit=500", **agente_informes_headers))

    assert filas
    assert {f["tipo_escalado"] for f in filas} <= {"manual", "automatico"}
    # Seis acciones sembradas, tres escalados.
    assert len(filas) == 3


def test_un_tipo_desconocido_da_400(client, todo_sembrado, agente_informes_headers):
    resp = client.get(f"{URL}?tipo_escalado=aviso", **agente_informes_headers)
    assert resp.status_code == 400, resp.content


# ── T029 — un reportador no accede ──────────────────────────────────────────


@pytest.mark.parametrize(
    "fixture", ["cliente_informes_headers", "partner_informes_headers"]
)
def test_un_reportador_recibe_403(client, todo_sembrado, request, fixture):
    """Un escalado es proceso interno del equipo de atención (FR-008)."""
    headers = request.getfixturevalue(fixture)
    resp = client.get(URL, **headers)

    assert resp.status_code == 403, resp.content
    assert "data" not in resp.json()


def test_sin_autenticar_es_401(client, todo_sembrado):
    assert client.get(URL).status_code == 401


@pytest.mark.parametrize(
    "fixture", ["agente_informes_headers", "gerente_exito_headers",
                "mixto_informes_headers"]
)
def test_los_roles_de_atencion_entran(client, todo_sembrado, request, fixture):
    headers = request.getfixturevalue(fixture)
    assert client.get(URL, **headers).status_code == 200


# ── T030 — el rango es opcional ─────────────────────────────────────────────


def test_sin_rango_devuelve_el_historico_completo(
    client, todo_sembrado, agente_informes_headers
):
    cuerpo = client.get(f"{URL}?limit=500", **agente_informes_headers).json()

    assert len(cuerpo["data"]) == 3
    assert "desde" not in cuerpo["meta"]["filtros"]
    assert "hasta" not in cuerpo["meta"]["filtros"]


def test_con_rango_se_acota(client, todo_sembrado, agente_informes_headers):
    """El escalado de hace 200 días queda fuera de un rango corto."""
    filas = _data(
        client.get(f"{URL}?desde=2026-08-01&hasta=2026-08-11",
                   **agente_informes_headers)
    )

    assert len(filas) == 2


def test_un_rango_invertido_da_400(client, todo_sembrado, agente_informes_headers):
    resp = client.get(
        f"{URL}?desde=2026-08-11&hasta=2026-08-01", **agente_informes_headers
    )
    assert resp.status_code == 400, resp.content


def test_filtrar_por_cuenta(client, todo_sembrado, agente_informes_headers):
    filas = _data(
        client.get(f"{URL}?cuenta={CUENTA_PARTNER}&limit=500",
                   **agente_informes_headers)
    )

    assert filas
    assert {f["cuenta"] for f in filas} == {"Navarro Integraciones Ltda."}
