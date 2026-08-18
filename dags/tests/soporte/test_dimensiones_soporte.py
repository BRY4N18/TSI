"""T016 — las tres dimensiones de Soporte se construyen y son idempotentes."""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from lib.dimensiones.dim_estado_soporte import construir as construir_estado  # noqa: E402
from lib.dimensiones.dim_servicio import construir as construir_servicio  # noqa: E402
from lib.dimensiones.dim_sla_config import construir as construir_sla  # noqa: E402

AHORA = datetime(2026, 8, 17, 12, 0, 0)


def test_las_tres_se_construyen_y_repetir_no_cambia_el_resultado():
    sla = [{
        "idslaconfig": 1, "idplan": 1, "tipoincidencia": "tecnica",
        "prioridad": "alta", "activo": True,
        "tiemporespuestamax": 3600, "tiemporesolucionmax": 7200,
        "fechavigenciadesde": int(AHORA.timestamp() * 1000),
        "fechavigenciahasta": None,
    }]
    servicios = [{"id_servicio": 1, "nombre": "API", "tipo": "api", "activo": True}]
    estados = [{"id_estado_soporte": 1, "nombre": "Abierto", "activo": True}]

    assert construir_sla(sla, AHORA) == construir_sla(sla, AHORA)
    assert construir_servicio(servicios, AHORA) == construir_servicio(servicios, AHORA)
    assert construir_estado(estados, AHORA) == construir_estado(estados, AHORA)
    assert construir_servicio(servicios, AHORA)[0]["nombre"] == "API"
    assert construir_estado(estados, AHORA)[0]["nombre"] == "Abierto"
