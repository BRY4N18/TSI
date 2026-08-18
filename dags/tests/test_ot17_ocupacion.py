"""T033, T035 — ocupación declara cobertura; sin plan no es 0 % (SC-011, SC-012)."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tests.almacen import (  # noqa: E402
    ID_CLIENTE_PRUEBA,
    ID_PLAN_PRUEBA,
    ID_SUSCRIPCION_PRUEBA,
    ID_USUARIO_PRUEBA,
    asegurar_hechos_cuentas,
    cliente_de_prueba,
    ejecutar_cuentas,
    insertar,
    limpiar_cuentas,
    plan_de_prueba,
    requiere_modelo,
    suscripcion_de_prueba,
    usuario_org_de_prueba,
)


@pytest.fixture
def escenario():
    asegurar_hechos_cuentas()
    limpiar_cuentas()
    insertar("dim_plan", [plan_de_prueba(ID_PLAN_PRUEBA, limite_usuarios=10)])
    insertar("dim_cliente", [
        cliente_de_prueba(ID_CLIENTE_PRUEBA),
        cliente_de_prueba(ID_CLIENTE_PRUEBA + 1, nombre="Sin plan"),
    ])
    insertar("hecho_suscripcion", [
        suscripcion_de_prueba(ID_SUSCRIPCION_PRUEBA, idcliente=ID_CLIENTE_PRUEBA),
    ])
    insertar("dim_usuario_organizacion", [
        usuario_org_de_prueba(ID_USUARIO_PRUEBA, idcliente=ID_CLIENTE_PRUEBA),
        usuario_org_de_prueba(ID_USUARIO_PRUEBA + 1, idcliente=ID_CLIENTE_PRUEBA + 1),
        usuario_org_de_prueba(ID_USUARIO_PRUEBA + 2),
    ])
    yield
    limpiar_cuentas()


@requiere_modelo
class TestOcupacionYCobertura:
    def test_declara_cobertura_y_no_reparte_a_los_sin_pertenencia(self, escenario):
        filas = ejecutar_cuentas("ot17_usuarios_vs_tope")
        por = {int(f["idcliente"]): f for f in filas}
        con_plan = por[ID_CLIENTE_PRUEBA]
        assert "pct_cobertura_pertenencia" in con_plan
        assert float(con_plan["pct_cobertura_pertenencia"]) == pytest.approx(2 / 3, rel=1e-3)
        assert int(con_plan["usuarios_conocidos"]) == 1
        assert int(por[ID_CLIENTE_PRUEBA + 1]["usuarios_conocidos"]) == 1

    def test_sin_plan_ocupacion_ausente_no_cero(self, escenario):
        filas = ejecutar_cuentas("ot17_usuarios_vs_tope")
        sin_plan = next(f for f in filas if int(f["idcliente"]) == ID_CLIENTE_PRUEBA + 1)
        assert sin_plan["pct_ocupacion"] is None
        assert sin_plan["tope_plan"] is None
