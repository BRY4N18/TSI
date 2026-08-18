"""T018–T020 — intervalo semiabierto del SLA vigente."""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from lib.hechos.sla_vigente import sla_vigente_en  # noqa: E402

CAMBIO = datetime(2026, 6, 1, 0, 0, 0)
CONFIGS = [
    {
        "idslaconfig": 1, "idplan": 1, "tipo_incidencia": "tecnica",
        "prioridad": "alta", "segundos_resolucion_max": 86400,
        "valido_desde": datetime(2026, 1, 1), "valido_hasta": CAMBIO,
    },
    {
        "idslaconfig": 6, "idplan": 1, "tipo_incidencia": "tecnica",
        "prioridad": "alta", "segundos_resolucion_max": 7200,
        "valido_desde": CAMBIO, "valido_hasta": None,
    },
]


def test_un_instante_anterior_al_cambio_resuelve_86400():
    fila = sla_vigente_en(CONFIGS, 1, "tecnica", "alta", datetime(2026, 5, 31, 23, 0, 0))
    assert fila is not None
    assert fila["segundos_resolucion_max"] == 86400


def test_un_instante_posterior_resuelve_7200():
    fila = sla_vigente_en(CONFIGS, 1, "tecnica", "alta", datetime(2026, 6, 1, 1, 0, 0))
    assert fila is not None
    assert fila["segundos_resolucion_max"] == 7200


def test_el_instante_exacto_del_cambio_resuelve_la_nueva():
    fila = sla_vigente_en(CONFIGS, 1, "tecnica", "alta", CAMBIO)
    assert fila is not None
    assert fila["idslaconfig"] == 6
    assert fila["segundos_resolucion_max"] == 7200


def test_sin_configuracion_devuelve_ausente():
    assert sla_vigente_en(CONFIGS, 1, "inexistente", "alta", CAMBIO) is None
    assert sla_vigente_en(CONFIGS, 99, "tecnica", "alta", CAMBIO) is None
