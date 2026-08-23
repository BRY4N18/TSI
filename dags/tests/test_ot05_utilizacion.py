"""T061, T062 — utilización: usados y contratados; sin columnas de API."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tests.base_propia import base_propia, vaciar  # noqa: E402,F401
from tests.almacen import (  # noqa: E402
    FECHA_DE_PRUEBA,
    ID_CLIENTE_PRUEBA,
    ID_PLAN_PRUEBA,
    ID_SUSCRIPCION_PRUEBA,
    asegurar_hechos_suscripciones,
    ejecutar_suscripciones,
    insertar,
    limpiar_suscripciones,
    plan_de_prueba,
    requiere_modelo,
    suscripcion_de_prueba,
)


def _unidad(i: int) -> dict:
    return {
        "sk_unidad": 980000 + i,
        "idunidademergencia": 980000 + i,
        "placa": f"TST-{i}",
        "nombre_unidad": f"U{i}",
        "tipo_unidad": "Patrulla",
        "capacidad": 4,
        "idcliente": ID_CLIENTE_PRUEBA,
        "proveedor": "Prueba",
        "idcondado": 1,
        "condado": "X",
        "zona_cobertura": None,
        "valido_desde": f"{FECHA_DE_PRUEBA} 00:00:00",
        "valido_hasta": None,
        "es_vigente": 1,
        "inicio_es_real": 1,
        "version": f"{FECHA_DE_PRUEBA} 12:00:00",
    }


@pytest.fixture
def escenario(base_propia):
    """⚠️ Corre sobre `base_propia`, no sobre el modelo cargado.

    Esta prueba compara su escenario contra un total **global** (el MRR, la
    utilización, el NRR). Contra el modelo real ese total incluye las
    suscripciones de verdad y el número esperado deja de tener sentido: pasaba
    solo mientras las tablas estaban vacías.
    """
    vaciar("hecho_suscripcion", "dim_plan")
    asegurar_hechos_suscripciones()
    limpiar_suscripciones()
    insertar("dim_plan", [plan_de_prueba(ID_PLAN_PRUEBA, limite_unidades=25, limite_usuarios=2500)])
    insertar("hecho_suscripcion", [suscripcion_de_prueba(ID_SUSCRIPCION_PRUEBA)])
    insertar("dim_unidad", [_unidad(i) for i in range(5)])
    yield
    limpiar_suscripciones()


@requiere_modelo
class TestUtilizacion:
    def test_no_inventa_la_dimension_de_api(self, escenario):
        filas = ejecutar_suscripciones("ot05_utilizacion_limites")
        assert filas
        claves = {k.lower() for k in filas[0]}
        for prohibida in ("llamadas", "api_calls", "api_call"):
            assert not any(prohibida in c for c in claves), claves

    def test_devuelve_usado_y_contratado(self, escenario):
        fila = ejecutar_suscripciones("ot05_utilizacion_limites")[0]
        assert int(fila["unidades_usadas"]) == 5
        assert int(fila["unidades_limite"]) == 25
        assert int(fila["usuarios_limite"]) == 2500
        assert fila["usuarios_usados"] is None
