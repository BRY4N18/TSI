"""T025, T031 — acciones sin texto; FINAL ilegal en el hecho de transacción."""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from lib.hechos.hecho_accion_ticket import CONSULTA, construir  # noqa: E402
from tests.almacen import almacen_disponible  # noqa: E402

AHORA = datetime(2026, 8, 17, 12, 0, 0)


def test_el_extract_no_pide_mensaje_ni_nota_interna():
    sql = CONSULTA.lower()
    assert "mensaje" not in sql
    assert "es_nota_interna" not in sql


def test_construye_escalado_automatico_sin_texto():
    filas = construir(
        {
            "historial": [{
                "id_historial": 13, "id_reclamo": 1,
                "tipo_accion": "escalado_automatico_sla", "idusuario": 0,
                "estado_anterior": "En_progreso", "estado_nuevo": "Escalado",
                "fecha_accion": int(AHORA.timestamp() * 1000),
            }],
            "tickets": [{"id_reclamo": 1, "idcliente": 10, "id_agente_asignado": 7}],
        },
        AHORA,
    )
    assert filas[0]["es_escalado"] == 1
    assert filas[0]["es_escalado_automatico"] == 1
    assert "mensaje" not in filas[0]
    assert "es_nota_interna" not in filas[0]


@pytest.mark.skipif(not almacen_disponible(), reason="requiere el almacén táctico")
def test_final_sobre_hecho_accion_falla():
    from lib.clickhouse_http_client import query_clickhouse

    try:
        query_clickhouse("SELECT count() FROM hecho_accion_ticket")
    except Exception:  # noqa: BLE001
        pytest.skip("hecho_accion_ticket aún no existe en el almacén")
    with pytest.raises(Exception, match="ILLEGAL_FINAL|FINAL"):
        query_clickhouse("SELECT count() FROM hecho_accion_ticket FINAL")
