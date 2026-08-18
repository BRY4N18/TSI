"""T047 — un cliente aún en proceso no cuenta como cero días (SC-005)."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tests.almacen import (  # noqa: E402
    ID_CLIENTE_PRUEBA,
    ID_ONBOARDING_PRUEBA,
    asegurar_hechos_cuentas,
    cliente_de_prueba,
    etapas_catalogo,
    ejecutar_cuentas,
    insertar,
    limpiar_cuentas,
    onboarding_de_prueba,
    requiere_modelo,
)


@pytest.fixture
def escenario():
    asegurar_hechos_cuentas()
    limpiar_cuentas()
    insertar("dim_etapa_onboarding", etapas_catalogo())
    insertar("dim_cliente", [
        cliente_de_prueba(ID_CLIENTE_PRUEBA, onboarding_completo=1),
        cliente_de_prueba(ID_CLIENTE_PRUEBA + 1, onboarding_completo=0),
    ])
    insertar("hecho_onboarding", [
        onboarding_de_prueba(
            ID_ONBOARDING_PRUEBA,
            idcliente=ID_CLIENTE_PRUEBA,
            idetapa=3,
            etapa="preferencias",
            dias_desde_alta=10,
        ),
        onboarding_de_prueba(
            ID_ONBOARDING_PRUEBA + 1,
            idcliente=ID_CLIENTE_PRUEBA + 1,
            idetapa=1,
            etapa="cambio_password",
            dias_desde_alta=0,
        ),
    ])
    yield
    limpiar_cuentas()


@requiere_modelo
class TestTiempoOnboarding:
    def test_en_proceso_fuera_de_la_mediana(self, escenario):
        filas = ejecutar_cuentas("ot04_tiempo_onboarding")
        assert filas, "con clientes en el período debe haber fila"
        fila = filas[0]
        assert int(fila["clientes_completados"]) == 1
        assert int(fila["en_proceso"]) == 1
        assert float(fila["dias_mediana"]) == pytest.approx(10.0)
        assert float(fila["dias_mediana"]) != pytest.approx(0)
        assert float(fila["dias_mediana"]) != pytest.approx(5.0)
