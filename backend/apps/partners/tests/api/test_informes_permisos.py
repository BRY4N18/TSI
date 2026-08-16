"""T007 y T008 — quién entra a cada listado.

El permiso **falla cerrado**: sin usuario, sin autenticar o sin rol, no pasa.
Conceder aquí no implica ver todos los partners — eso lo decide el acotamiento,
que es una comprobación distinta y posterior.
"""

from __future__ import annotations

import pytest

from core.jwt_utils import create_access_token

BASE = "/api/v1/informes/partners-api"

DE_ACCESO = ["partners", "credenciales", "cambios-acceso"]
DE_GESTION = ["versiones-contrato", "alcance-datos"]
TODOS = DE_ACCESO + DE_GESTION

pytestmark = pytest.mark.django_db


def _headers(roles):
    token = create_access_token(user_id=4599, roles=roles, session_id=1)
    return {"HTTP_AUTHORIZATION": f"Bearer {token}"}


@pytest.mark.parametrize("informe", TODOS)
def test_sin_autenticar_es_401(client, informe):
    assert client.get(f"{BASE}/{informe}").status_code == 401


@pytest.mark.parametrize("informe", TODOS)
def test_un_rol_ajeno_al_departamento_es_403(client, todo_sembrado, informe):
    """Un operador de despacho no tiene nada que hacer en estos listados."""
    resp = client.get(f"{BASE}/{informe}", **_headers(["OperadorDespacho"]))
    assert resp.status_code == 403, resp.content


@pytest.mark.parametrize("informe", TODOS)
@pytest.mark.parametrize("rol", ["Administrador", "DesarrolladorAPIs"])
def test_los_gestores_entran_a_los_cinco(client, todo_sembrado, informe, rol):
    assert client.get(f"{BASE}/{informe}", **_headers([rol])).status_code == 200


@pytest.mark.parametrize("informe", DE_ACCESO)
def test_el_partner_entra_a_los_tres_de_acceso(
    client, todo_sembrado, partner_a_informes_headers, informe
):
    assert client.get(
        f"{BASE}/{informe}", **partner_a_informes_headers
    ).status_code == 200


@pytest.mark.parametrize("informe", DE_GESTION)
def test_el_partner_no_entra_a_los_de_gestion(
    client, todo_sembrado, partner_a_informes_headers, informe
):
    """El alcance de datos describe lo que cada CLIENTE contrató, y las
    versiones gobiernan el ciclo de vida del contrato: son materia de quien
    administra la plataforma, no de quien la consume (FR-013)."""
    assert client.get(
        f"{BASE}/{informe}", **partner_a_informes_headers
    ).status_code == 403


@pytest.mark.parametrize("informe", DE_ACCESO)
def test_un_partner_sin_cuenta_resuelta_es_403_no_todos(client, todo_sembrado, informe):
    """Si no se puede resolver su cuenta, se niega — **no** se le da el alcance
    completo. Fallar abierto aquí publicaría los partners de todas las cuentas.
    """
    huerfano = create_access_token(user_id=999_999, roles=["PartnerIntegracion"],
                                   session_id=1)
    resp = client.get(
        f"{BASE}/{informe}", HTTP_AUTHORIZATION=f"Bearer {huerfano}"
    )

    assert resp.status_code == 403, resp.content
    assert "data" not in resp.json()
