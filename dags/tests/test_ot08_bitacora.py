"""T055 — eventos no efectivos no inflan el rechazo."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tests.almacen import (  # noqa: E402
    ID_HISTORIAL_PRUEBA,
    asegurar_hechos_partners,
    cambio_de_prueba,
    ejecutar_partners,
    insertar,
    limpiar_partners,
    requiere_modelo,
)


@pytest.fixture
def escenario():
    asegurar_hechos_partners()
    limpiar_partners()
    insertar("hecho_cambio_acceso", [
        cambio_de_prueba(
            ID_HISTORIAL_PRUEBA,
            tipo_cambio="solicitud_promocion_produccion",
            motivo="alta",
        ),
        cambio_de_prueba(
            ID_HISTORIAL_PRUEBA + 1,
            tipo_cambio="rechazo_promocion_produccion",
            estado_anterior="Activo",
            estado_nuevo="Activo",
            efectivo=0,
            motivo="duplicado",
        ),
        cambio_de_prueba(
            ID_HISTORIAL_PRUEBA + 2,
            tipo_cambio="rechazo_promocion_produccion",
            estado_anterior="Pendiente de aprobación",
            estado_nuevo="Registrado",
            efectivo=1,
            motivo="documentacion",
        ),
    ])
    yield
    limpiar_partners()


@requiere_modelo
def test_el_no_efectivo_no_cuenta(escenario):
    filas = ejecutar_partners("ot08_tasa_rechazo_produccion")
    assert filas
    rechazadas = sum(int(f["rechazadas"]) for f in filas)
    assert rechazadas == 1
