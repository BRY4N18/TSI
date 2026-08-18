"""T060 — una sesión que cruza medianoche cuenta en ambas franjas (FR-019)."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tests.almacen import (  # noqa: E402
    ID_SESION_PRUEBA,
    asegurar_hechos_cuentas,
    ejecutar_cuentas,
    insertar,
    limpiar_cuentas,
    requiere_modelo,
    sesion_de_prueba,
)


@pytest.fixture
def escenario():
    asegurar_hechos_cuentas()
    limpiar_cuentas()
    insertar("hecho_sesion", [
        sesion_de_prueba(
            ID_SESION_PRUEBA,
            inicio="2099-12-01 23:00:00",
            cierre="2099-12-02 01:00:00",
        ),
    ])
    yield
    limpiar_cuentas()


@requiere_modelo
class TestFranjasQueCruzanMedianoche:
    def test_cuenta_en_ambas_franjas(self, escenario):
        filas = ejecutar_cuentas(
            "ot18_concurrencia_sesiones",
            desde="2099-12-01",
            hasta="2099-12-02",
        )
        por = {(str(f["fecha"])[:10], f["franja"]): f for f in filas}
        noche = por[("2099-12-01", "noche")]
        madrugada = por[("2099-12-02", "madrugada")]
        assert int(noche["concurrencia_maxima"]) >= 1
        assert int(madrugada["concurrencia_maxima"]) >= 1
        assert int(noche["cruza_medianoche"]) == 1 or int(madrugada["cruza_medianoche"]) == 1
