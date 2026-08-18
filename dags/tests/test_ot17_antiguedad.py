"""T036 — antigüedad del activo hasta hoy, no hasta una baja inventada."""

from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tests.almacen import (  # noqa: E402
    ID_CLIENTE_PRUEBA,
    asegurar_hechos_cuentas,
    cliente_de_prueba,
    ejecutar_cuentas,
    insertar,
    limpiar_cuentas,
    requiere_modelo,
)


@pytest.fixture
def escenario():
    asegurar_hechos_cuentas()
    limpiar_cuentas()
    insertar("dim_cliente", [
        cliente_de_prueba(
            ID_CLIENTE_PRUEBA,
            fecha_alta="2026-01-01 08:00:00",
            cohorte_alta="2026-01",
            fecha_baja=None,
            tipo="aseguradora",
        ),
        cliente_de_prueba(
            ID_CLIENTE_PRUEBA + 1,
            fecha_alta="2026-01-01 08:00:00",
            cohorte_alta="2026-01",
            fecha_baja="2026-01-31 08:00:00",
            tipo="gobierno",
        ),
    ])
    yield
    limpiar_cuentas()


@requiere_modelo
class TestAntiguedad:
    def test_el_activo_se_mide_hasta_hoy(self, escenario):
        filas = ejecutar_cuentas(
            "ot17_antiguedad_media",
            desde="2026-01-01",
            hasta="2026-12-31",
        )
        por = {f["tipo_cliente"]: f for f in filas}
        activos = por["aseguradora"]
        esperados = (date.today() - date(2026, 1, 1)).days
        assert float(activos["dias_mediana"]) == pytest.approx(esperados, abs=1.0)
        assert float(activos["dias_mediana"]) != pytest.approx(0)
        assert float(por["gobierno"]["dias_mediana"]) == pytest.approx(30, abs=1.0)
