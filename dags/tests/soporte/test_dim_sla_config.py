"""T011, T012 — dim_sla_config respeta las vigencias del origen."""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from lib.dimensiones.dim_sla_config import CONSULTA, construir  # noqa: E402

AHORA = datetime(2026, 8, 17, 12, 0, 0)
CAMBIO = int(datetime(2026, 6, 1, 0, 0, 0).timestamp() * 1000)
ANTES = CAMBIO - 86_400_000


def test_un_plan_con_dos_configuraciones_produce_dos_filas():
    filas = construir(
        [
            {
                "idslaconfig": 1, "idplan": 1, "tipoincidencia": "tecnica",
                "prioridad": "alta", "activo": False,
                "tiemporespuestamax": 3600, "tiemporesolucionmax": 86400,
                "fechavigenciadesde": ANTES, "fechavigenciahasta": CAMBIO,
            },
            {
                "idslaconfig": 6, "idplan": 1, "tipoincidencia": "tecnica",
                "prioridad": "alta", "activo": True,
                "tiemporespuestamax": 1800, "tiemporesolucionmax": 7200,
                "fechavigenciadesde": CAMBIO, "fechavigenciahasta": None,
            },
        ],
        AHORA,
    )
    assert len(filas) == 2
    cerrada = next(f for f in filas if f["idslaconfig"] == 1)
    abierta = next(f for f in filas if f["idslaconfig"] == 6)
    assert cerrada["valido_hasta"] is not None
    assert cerrada["es_vigente"] == 0
    assert cerrada["segundos_resolucion_max"] == 86400
    assert abierta["valido_hasta"] is None
    assert abierta["es_vigente"] == 1
    assert abierta["segundos_resolucion_max"] == 7200


def test_no_declara_inicio_es_real():
    filas = construir(
        [{
            "idslaconfig": 1, "idplan": 1, "tipoincidencia": "tecnica",
            "prioridad": "alta", "activo": True,
            "tiemporespuestamax": 3600, "tiemporesolucionmax": 7200,
            "fechavigenciadesde": CAMBIO, "fechavigenciahasta": None,
        }],
        AHORA,
    )
    assert "inicio_es_real" not in filas[0]


def test_la_consulta_no_invoca_versionado():
    assert "versionado" not in CONSULTA.lower()
