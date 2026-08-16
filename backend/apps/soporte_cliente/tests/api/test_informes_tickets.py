"""US1 — La cola de tickets (L1).

**T016 protege contra el fallo que casi se coló en la revisión anterior.** Si el
Partner ve los tickets del Cliente, el acotamiento se decidió por el rol que se
**tiene** en vez de por el que **no** se tiene — y el Partner, que reporta pero
no es Cliente, se sale de él.

**T015 evita reintroducir un defecto ya corregido.** Un listado que omita el
ticket `sin compromiso` o lo muestre como `en curso` volvería invisible el único
estado en que un ticket queda sin que ningún proceso lo mire.
"""

from __future__ import annotations

import re

import pytest

from apps.soporte_cliente.tests.conftest import (
    AGENTE,
    CUENTA_CLIENTE,
    CUENTA_PARTNER,
)

pytestmark = pytest.mark.django_db

URL = "/api/v1/informes/soporte-cliente/tickets"


def _data(resp):
    assert resp.status_code == 200, resp.content
    return resp.json()["data"]


def _por_asunto(filas):
    return {f["asunto"]: f for f in filas}


# ── T015 — las dos ausencias no se confunden ────────────────────────────────


def test_el_ticket_sin_compromiso_es_listable_y_no_pasa_por_en_curso(
    client, todo_sembrado, agente_informes_headers
):
    filas = _data(client.get(f"{URL}?limit=500", **agente_informes_headers))
    ticket = _por_asunto(filas)["Consulta sobre cobertura"]

    assert ticket["situacion_compromiso"] == "sin compromiso"
    assert ticket["situacion_compromiso"] != "en curso"


def test_filtrar_por_sin_compromiso_devuelve_solo_esos(
    client, todo_sembrado, agente_informes_headers
):
    """Es el filtro que hace visible lo que ningún vigilante revisa."""
    filas = _data(
        client.get(
            f"{URL}?situacion_compromiso=sin%20compromiso", **agente_informes_headers
        )
    )

    assert filas
    assert {f["situacion_compromiso"] for f in filas} == {"sin compromiso"}


def test_el_ticket_sin_clasificar_llega_sin_situacion_atribuida(
    client, todo_sembrado, agente_informes_headers
):
    """Aún no hay contador: no se le atribuye ninguna situación (FR-006).

    Es distinto de `sin compromiso`, que sí está clasificado.
    """
    filas = _data(client.get(f"{URL}?limit=500", **agente_informes_headers))
    ticket = _por_asunto(filas)["Algo va mal"]

    assert ticket["situacion_compromiso"] is None


def test_el_filtro_de_situacion_admite_los_cinco_valores_del_dominio():
    """⚠️ El dominio tiene **cinco**, no las cuatro que enumera `data-model.md`.

    `cumplido` lo escribe `resolver_ticket_service` al resolver dentro de plazo.
    Implementar las cuatro de la spec dejaría el filtro rechazando con `400` un
    valor legítimo, e imposible listar los tickets resueltos a tiempo.
    """
    from apps.soporte_cliente import domain_constants as dc
    from apps.soporte_cliente import informes_views

    del_dominio = {
        v for k, v in vars(dc).items()
        if k.startswith("SLA_") and isinstance(v, str)
    }
    assert set(informes_views.SITUACIONES_COMPROMISO) == del_dominio


def test_cumplido_se_acepta_como_filtro(
    client, todo_sembrado, agente_informes_headers
):
    resp = client.get(
        f"{URL}?situacion_compromiso=cumplido", **agente_informes_headers
    )
    assert resp.status_code == 200, resp.content


def test_una_situacion_desconocida_da_400(
    client, todo_sembrado, agente_informes_headers
):
    resp = client.get(
        f"{URL}?situacion_compromiso=inventada", **agente_informes_headers
    )
    assert resp.status_code == 400, resp.content


# ── T016 — el Partner queda acotado igual que el Cliente ────────────────────


def test_el_cliente_solo_ve_los_de_su_cuenta(
    client, todo_sembrado, cliente_informes_headers
):
    cuerpo = client.get(f"{URL}?limit=500", **cliente_informes_headers).json()

    cuentas = {f["cuenta"] for f in cuerpo["data"]}
    assert cuentas == {"Transportes Ferrer S.A."}
    assert cuerpo["meta"]["acotado_a"] == "propios"


def test_el_partner_queda_acotado_igual_que_el_cliente(
    client, todo_sembrado, partner_informes_headers
):
    """El Partner reporta y **no es Cliente**.

    Decidir el acotamiento por «ser Cliente» lo dejaría fuera de él — es decir,
    viendo los tickets de todas las cuentas.
    """
    cuerpo = client.get(f"{URL}?limit=500", **partner_informes_headers).json()

    cuentas = {f["cuenta"] for f in cuerpo["data"]}
    assert cuentas == {"Navarro Integraciones Ltda."}
    assert "Transportes Ferrer S.A." not in cuentas
    assert cuerpo["meta"]["acotado_a"] == "propios"


def test_ninguno_de_los_dos_ve_los_del_otro(
    client, todo_sembrado, cliente_informes_headers, partner_informes_headers
):
    del_cliente = {
        f["numero_ticket"]
        for f in _data(client.get(f"{URL}?limit=500", **cliente_informes_headers))
    }
    del_partner = {
        f["numero_ticket"]
        for f in _data(client.get(f"{URL}?limit=500", **partner_informes_headers))
    }

    assert del_cliente and del_partner
    assert not (del_cliente & del_partner)


# ── T017 — el rol mixto no queda acotado ────────────────────────────────────


def test_un_usuario_que_es_cliente_y_agente_obtiene_la_cola_completa(
    client, todo_sembrado, mixto_informes_headers
):
    """Tener un rol de atención saca del acotamiento (FR-012)."""
    cuerpo = client.get(f"{URL}?limit=500", **mixto_informes_headers).json()

    cuentas = {f["cuenta"] for f in cuerpo["data"]}
    assert {"Transportes Ferrer S.A.", "Navarro Integraciones Ltda."} <= cuentas
    assert cuerpo["meta"]["acotado_a"] == "todos"


def test_el_acotamiento_coincide_con_la_condicion_del_modulo_operativo():
    """La vista y `es_solo_reportador` deben decidir lo mismo.

    Son dos expresiones del mismo criterio —«no tener ningún rol de atención»— y
    si divergieran, la pantalla y el listado acotarían a poblaciones distintas
    sin que ninguna de las dos supiera de la otra.
    """
    from itertools import combinations

    from apps.soporte_cliente.permissions import (
        ROLES_ATENCION,
        ROLES_REPORTADORES,
        es_solo_reportador,
    )
    from core.informes.acotamiento import ACOTADO_PROPIOS, resolver_organizacion

    todos = sorted(ROLES_ATENCION | ROLES_REPORTADORES)
    for n in (1, 2, 3):
        for combo in combinations(todos, n):
            acot = resolver_organizacion(
                roles=list(combo),
                user_id=1,
                roles_amplios=ROLES_ATENCION,
                roles_acotados=ROLES_REPORTADORES,
                resolver_cuenta=lambda _uid: 99,
            )
            queda_acotado = acot.alcance == ACOTADO_PROPIOS

            assert queda_acotado is es_solo_reportador(combo), combo


def test_el_gerente_de_exito_no_queda_acotado(
    client, todo_sembrado, gerente_exito_headers
):
    """Autoridad del departamento (FR-014a)."""
    cuerpo = client.get(f"{URL}?limit=500", **gerente_exito_headers).json()

    assert cuerpo["meta"]["acotado_a"] == "todos"
    assert len({f["cuenta"] for f in cuerpo["data"]}) == 2


# ── T018 — pedir otra cuenta ────────────────────────────────────────────────


def test_pedir_una_cuenta_ajena_da_403_sin_filas(
    client, todo_sembrado, cliente_informes_headers
):
    resp = client.get(f"{URL}?cuenta={CUENTA_PARTNER}", **cliente_informes_headers)

    assert resp.status_code == 403, resp.content
    assert "data" not in resp.json()


def test_pedir_la_propia_cuenta_funciona(
    client, todo_sembrado, cliente_informes_headers
):
    resp = client.get(f"{URL}?cuenta={CUENTA_CLIENTE}", **cliente_informes_headers)
    assert resp.status_code == 200, resp.content


def test_un_rol_ajeno_al_departamento_da_403(
    client, todo_sembrado, ajeno_informes_headers
):
    resp = client.get(URL, **ajeno_informes_headers)
    assert resp.status_code == 403, resp.content


# ── T019 — la descripción del reporte no sale ───────────────────────────────


def test_la_respuesta_no_contiene_la_descripcion(
    client, todo_sembrado, agente_informes_headers
):
    resp = client.get(f"{URL}?limit=500", **agente_informes_headers)

    assert "DESCRIPCION-LARGA" not in resp.content.decode("utf-8")
    for fila in _data(resp):
        assert "descripcion" not in fila


def test_el_repositorio_enumera_las_columnas_en_vez_de_pedirlas_todas():
    from core.repositories.soporte import informes_tickets_repository as repo

    fuente = open(repo.__file__, encoding="utf-8").read()
    consultas = re.findall(r'"(SELECT [^"]+)"', fuente)

    assert consultas
    for consulta in consultas:
        assert "SELECT *" not in consulta, consulta
    assert "descripcion" not in repo.COLUMNAS_TICKET


# ── T020 — los filtros, sueltos y combinados ────────────────────────────────


def test_filtrar_por_agente(client, todo_sembrado, agente_informes_headers):
    filas = _data(client.get(f"{URL}?agente={AGENTE}", **agente_informes_headers))

    assert filas
    assert all(f["agente_asignado"] == "Bruno Salas" for f in filas)


def test_un_ticket_sin_agente_aparece_con_el_agente_ausente(
    client, todo_sembrado, agente_informes_headers
):
    """No se omite: un ticket que nadie ha tomado es el que más hay que ver."""
    filas = _data(client.get(f"{URL}?limit=500", **agente_informes_headers))
    ticket = _por_asunto(filas)["Consulta sobre cobertura"]

    assert ticket["agente_asignado"] is None


def test_filtrar_por_factura_vinculada(
    client, todo_sembrado, agente_informes_headers
):
    con = _data(client.get(f"{URL}?con_factura=true", **agente_informes_headers))
    sin = _data(client.get(f"{URL}?con_factura=false&limit=500",
                           **agente_informes_headers))

    assert [f["asunto"] for f in con] == ["Disputa de la factura de julio"]
    assert con[0]["factura_vinculada"]
    assert sin
    assert all(f["factura_vinculada"] is None for f in sin)


def test_filtros_combinados(client, todo_sembrado, agente_informes_headers):
    filas = _data(
        client.get(
            f"{URL}?estado=En_progreso&situacion_compromiso=en%20riesgo",
            **agente_informes_headers,
        )
    )

    assert [f["asunto"] for f in filas] == ["Error al adjuntar fotos"]


def test_el_orden_por_defecto_es_determinista(
    client, todo_sembrado, agente_informes_headers
):
    filas = _data(client.get(f"{URL}?limit=500", **agente_informes_headers))
    fechas = [f["fecha_registro"] for f in filas]

    assert fechas == sorted(fechas, reverse=True)


def test_un_rango_de_fechas_da_400(client, todo_sembrado, agente_informes_headers):
    """Es un listado de **estado actual**: el rango no se ignora, se rechaza."""
    resp = client.get(f"{URL}?desde=2026-01-01", **agente_informes_headers)
    assert resp.status_code == 400, resp.content


def test_sin_resultados_es_200_con_data_vacia(
    client, todo_sembrado, agente_informes_headers
):
    """Que no haya tickets incumplidos es una buena noticia, no un error."""
    resp = client.get(f"{URL}?estado=Cerrado", **agente_informes_headers)

    assert resp.status_code == 200
    assert resp.json()["data"] == []
