"""T036 — antigüedad del activo hasta hoy, no hasta una baja inventada."""

from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tests.base_propia import base_propia, vaciar  # noqa: F401,E402
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
def escenario(base_propia):  # noqa: F811
    """⚠️ **Base propia, y no es cosmético.**

    `limpiar_cuentas()` no vacía `dim_cliente` —solo suelta particiones de
    `hecho_sesion` y `hecho_onboarding`—, así que esta prueba convivía con las
    cuentas reales. Pasaba **por accidente**: ninguna de ellas tenía `fecha_alta`
    y `dateDiff` las dejaba fuera de la mediana.

    El 2026-08-23 se rellenó `fecha_inicio_contrato` en las cuentas existentes y
    una de ellas, de tipo `aseguradora`, entró a competir con la sembrada aquí:
    la mediana pasó de 234 a 14 días sin que nada se hubiera roto. Sobre una base
    vacía la prueba vuelve a medir lo que dice medir.
    """
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
