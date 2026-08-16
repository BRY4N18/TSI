"""US2 — Bitácora de cambios de acceso (L3).

Lo que US1 no puede decir, US2 lo dice con su tipo propio: en el listado de
credenciales, revocada y desactivada-en-cascada son la misma fila; aquí son dos
tipos distintos, y esa diferencia es la que impide reactivar una credencial
comprometida creyendo que solo estaba suspendida por impago.
"""

from __future__ import annotations

import pytest

from apps.partners.domain_constants import (
    CAMBIO_DESACTIVACION_POR_CASCADA,
    CAMBIO_REACTIVACION,
    CAMBIO_REVOCACION_CREDENCIAL,
)

pytestmark = pytest.mark.django_db

URL = "/api/v1/informes/partners-api/cambios-acceso"


def _data(resp):
    assert resp.status_code == 200, resp.content
    return resp.json()["data"]


# ── T026 — el defecto que esta prueba existe para impedir ────────────────────


def test_la_revocacion_no_se_confunde_con_la_desactivacion_en_cascada(
    client, todo_sembrado, gestor_headers
):
    """Una decisión de seguridad y una consecuencia de impago no son lo mismo.

    Ambos dejan la credencial `activo=False`. Agruparlos bajo una etiqueta como
    «desactivada» llevaría a reactivar en bloque tras el pago — resucitando una
    credencial cuyo secreto está comprometido.
    """
    tipos = {f["tipo_cambio"] for f in _data(client.get(URL, **gestor_headers))}

    assert CAMBIO_REVOCACION_CREDENCIAL in tipos
    assert CAMBIO_DESACTIVACION_POR_CASCADA in tipos
    assert CAMBIO_REVOCACION_CREDENCIAL != CAMBIO_DESACTIVACION_POR_CASCADA


def test_cada_cambio_conserva_su_motivo_y_su_ejecutor(
    client, todo_sembrado, gestor_headers
):
    por_tipo = {f["tipo_cambio"]: f for f in _data(client.get(URL, **gestor_headers))}

    revocacion = por_tipo[CAMBIO_REVOCACION_CREDENCIAL]
    assert revocacion["motivo"] == "secreto comprometido"
    assert revocacion["ejecutado_por"] == "Partner"
    # La revocación sí apunta a una credencial concreta.
    assert revocacion["credencial"] == "revocada"

    cascada = por_tipo[CAMBIO_DESACTIVACION_POR_CASCADA]
    assert cascada["ejecutado_por"] == "Administrador"
    assert cascada["credencial"] == "cascada"


# ── T027 — la ausencia de motivo es correcta, no un dato que falte ───────────


def test_la_reactivacion_sin_motivo_es_correcta(
    client, todo_sembrado, gestor_headers
):
    """El SRS exige motivo al cortar el acceso, no al devolverlo.

    Presentarla como dato faltante induciría a «completar» un registro que ya
    está completo.
    """
    filas = _data(
        client.get(f"{URL}?tipo_cambio={CAMBIO_REACTIVACION}", **gestor_headers)
    )

    assert filas
    assert all(f["motivo"] is None for f in filas)


def test_un_evento_del_partner_sin_credencial_se_presenta_ausente(
    client, todo_sembrado, gestor_headers
):
    """`-1` es el centinela de «no afecta a ninguna credencial», no un id."""
    filas = _data(
        client.get(f"{URL}?tipo_cambio={CAMBIO_REACTIVACION}", **gestor_headers)
    )
    assert all(f["credencial"] is None for f in filas)


# ── T028 — el rango es opcional ─────────────────────────────────────────────


def test_sin_rango_devuelve_toda_la_bitacora(client, todo_sembrado, gestor_headers):
    resp = client.get(URL, **gestor_headers)
    cuerpo = resp.json()

    assert cuerpo["data"]
    # Un extremo que no se aplicó **no aparece**: `meta.filtros` refleja los
    # filtros aplicados, y ausencia no es lo mismo que un filtro con valor nulo.
    assert "desde" not in cuerpo["meta"]["filtros"]
    assert "hasta" not in cuerpo["meta"]["filtros"]


def test_con_rango_recorta_por_fecha(client, todo_sembrado, gestor_headers):
    completo = _data(client.get(URL, **gestor_headers))
    recortado = _data(
        client.get(f"{URL}?desde=2026-08-01&hasta=2026-08-11", **gestor_headers)
    )

    assert 0 < len(recortado) < len(completo)


def test_un_rango_invertido_da_400(client, todo_sembrado, gestor_headers):
    resp = client.get(f"{URL}?desde=2026-08-11&hasta=2026-08-01", **gestor_headers)
    assert resp.status_code == 400, resp.content


# ── T029 — acotamiento sobre una tabla que no guarda el cliente ─────────────


def test_un_partner_solo_ve_los_cambios_de_sus_partners(
    client, todo_sembrado, partner_a_informes_headers
):
    """La bitácora guarda el partner, no la cuenta: acotar exige resolverlos."""
    resp = client.get(URL, **partner_a_informes_headers)
    cuerpo = resp.json()

    partners = {f["partner"] for f in cuerpo["data"]}
    assert partners
    assert "Andina Conecta" not in partners
    assert cuerpo["meta"]["acotado_a"] == "propios"


def test_el_partner_suspendido_ve_por_que_lo_suspendieron(
    client, todo_sembrado, partner_a_informes_headers
):
    filas = _data(client.get(URL, **partner_a_informes_headers))
    suspension = [f for f in filas if f["partner"] == "Silva Legacy"]

    assert suspension
    assert any(f["motivo"] == "impago" for f in suspension)


def test_un_tipo_de_cambio_desconocido_da_400(
    client, todo_sembrado, gestor_headers
):
    resp = client.get(f"{URL}?tipo_cambio=inventado", **gestor_headers)
    assert resp.status_code == 400, resp.content
