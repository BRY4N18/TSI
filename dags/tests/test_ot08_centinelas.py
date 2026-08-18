"""T052 — año 9999 y época cero no son fechas (SC-004)."""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from lib.dimensiones.dim_credencial_api import NUNCA_EXPIRA_MS, construir as construir_cred  # noqa: E402
from lib.dimensiones.dim_version_contrato import construir as construir_ver  # noqa: E402

AHORA = datetime(2026, 8, 17, 12, 0, 0)


def test_el_anio_9999_no_entra_a_la_fecha():
    filas = construir_cred(
        {
            "credenciales": [{
                "idcredencial": 1, "idpartner": 1, "idcliente": None,
                "entorno": "Producción", "activo": True,
                "nombre_credencial": "prod",
                "fecha_creacion": 1,
                "fecha_expiracion": NUNCA_EXPIRA_MS,
            }],
            "bitacora": [],
        },
        AHORA,
    )
    assert filas[0]["fecha_expiracion"] is None
    assert filas[0]["nunca_expira"] == 1


def test_epoca_cero_no_es_retiro():
    filas = construir_ver(
        {
            "versiones": [{
                "idversion": 1, "id_servicio": 1, "version": "v1",
                "estado": "vigente", "fecha_publicacion": 1_700_000_000_000,
                "fecha_retiro": 0,
            }],
            "servicios": [{"id_servicio": 1, "nombre": "API Datos"}],
        },
        AHORA,
    )
    assert filas[0]["fecha_retiro"] is None
    assert filas[0]["servicio"] == "API Datos"
