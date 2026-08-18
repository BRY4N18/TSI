"""T028–T030 — hitos ausentes, SLA histórico y motivos de sin-compromiso."""

from __future__ import annotations

import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from lib.hechos.hecho_ticket import CONSULTA_TICKETS, construir  # noqa: E402

AHORA = datetime(2026, 8, 17, 12, 0, 0)
CAMBIO = datetime(2026, 6, 1, 0, 0, 0)

CONFIGS = [
    {
        "idslaconfig": 1, "idplan": 1, "tipo_incidencia": "tecnica",
        "prioridad": "alta", "segundos_respuesta_max": 3600,
        "segundos_resolucion_max": 86400,
        "valido_desde": "2026-01-01 00:00:00", "valido_hasta": "2026-06-01 00:00:00",
    },
    {
        "idslaconfig": 6, "idplan": 1, "tipo_incidencia": "tecnica",
        "prioridad": "alta", "segundos_respuesta_max": 1800,
        "segundos_resolucion_max": 7200,
        "valido_desde": "2026-06-01 00:00:00", "valido_hasta": None,
    },
]


def _base(**extra):
    fila = {
        "id_reclamo": 1, "idcliente": 10, "idestadosoporte": 1, "idservicio": None,
        "idslaconfig": 1, "tipo": "incidente", "prioridad": "alta",
        "id_agente_asignado": 7, "tipo_incidencia": "tecnica",
        "sla_status": "en curso", "estado": "En_progreso",
        "sla_primera_respuesta": 0, "sla_resolucion": 0, "tiempo_solucion": 0,
        "fechahora": int(datetime(2026, 5, 1, 10, 0, 0).timestamp() * 1000),
        "fechahoraconfirmacioncierre": None,
    }
    fila.update(extra)
    return fila


def _datos(tickets, historial=None):
    return {
        "tickets": tickets,
        "historial": historial or [],
        "suscripciones": [{"idcliente": 10, "idplan": 1}],
        "dim_sla_config": CONFIGS,
        "dim_plan": [{"idplan": 1, "nombre": "Pro"}],
        "dim_servicio": [],
        "dim_cliente": [{"idcliente": 10, "tipo": "aseguradora"}],
    }


def test_la_consulta_no_pide_asunto_ni_descripcion():
    sql = CONSULTA_TICKETS.lower()
    assert "asunto" not in sql
    assert "descripcion" not in sql


def test_un_ticket_abierto_tiene_segundos_resolucion_ausente():
    filas = construir(_datos([_base()]), AHORA)
    assert filas[0]["segundos_resolucion"] is None
    assert filas[0]["segundos_resolucion"] != 0


def test_un_ticket_anterior_al_cambio_conserva_86400():
    creacion = datetime(2026, 5, 1, 10, 0, 0)
    resolucion = creacion + timedelta(hours=5)
    filas = construir(
        _datos(
            [_base(fechahora=int(creacion.timestamp() * 1000))],
            [{
                "id_historial": 1, "id_reclamo": 1, "tipo_accion": "resolucion",
                "idusuario": 7, "estado_anterior": "En_progreso",
                "estado_nuevo": "Resuelto",
                "fecha_accion": int(resolucion.timestamp() * 1000),
            }],
        ),
        AHORA,
    )
    assert filas[0]["segundos_resolucion_max"] == 86400
    assert filas[0]["desenlace_sla"] == "cumplido"
    assert filas[0]["segundos_resolucion"] == 5 * 3600


def test_los_tres_motivos_se_distinguen():
    pendiente = _base(
        id_reclamo=1, estado="Pendiente_de_clasificacion",
        tipo_incidencia="", sla_status=None, idslaconfig=None,
    )
    sin_comp = _base(
        id_reclamo=2, sla_status="sin compromiso", idslaconfig=None,
        tipo_incidencia="tecnica",
    )
    sin_cfg = _base(
        id_reclamo=3, tipo_incidencia="otra", prioridad="baja",
        sla_status="en curso", idslaconfig=None,
    )
    filas = {f["id_reclamo"]: f for f in construir(_datos([pendiente, sin_comp, sin_cfg]), AHORA)}
    assert filas[1]["tiene_compromiso"] == 0
    assert filas[1]["motivo_sin_compromiso"] == "pendiente_clasificar"
    assert filas[2]["tiene_compromiso"] == 0
    assert filas[2]["motivo_sin_compromiso"] == "sin_compromiso"
    assert filas[3]["tiene_compromiso"] == 0
    assert filas[3]["motivo_sin_compromiso"] == "sin_config"
    assert all(f["desenlace_sla"] is None for f in filas.values())
