"""T048 — la etapa actual se deriva de lo registrado, no de la columna nula (FR-016)."""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from lib.dimensiones.dim_cliente import construir  # noqa: E402
from lib.dimensiones.dim_etapa_onboarding import CATALOGO, construir as construir_etapas  # noqa: E402

AHORA = datetime(2026, 8, 17, 12, 0, 0)


def test_el_catalogo_no_se_infiere_de_lo_observado():
    filas = construir_etapas([], AHORA)
    assert [f["etapa"] for f in filas] == [e[1] for e in CATALOGO]
    assert len(filas) == 5


def test_etapa_actual_sale_de_las_completadas_no_del_estado_nulo():
    filas = construir(
        {
            "clientes": [{
                "idcliente": 1,
                "razon_social": "Acme",
                "nombre": "Acme",
                "tipo": "aseguradora",
                "estado": "Activo",
                "estado_onboarding": None,
                "fecha_inicio_contrato": int(datetime(2026, 1, 1).timestamp() * 1000),
            }],
            "metodos": [],
            "onboarding": [
                {"id_cliente": 1, "etapa": "cambio_password", "completado": True},
                {"id_cliente": 1, "etapa": "perfil_corporativo", "completado": True},
                {"id_cliente": 1, "etapa": "preferencias", "completado": False},
            ],
        },
        AHORA,
    )
    assert filas[0]["estado_onboarding"] is None
    assert filas[0]["etapa_onboarding_actual"] == "perfil_corporativo"
    assert filas[0]["onboarding_completo"] == 0
