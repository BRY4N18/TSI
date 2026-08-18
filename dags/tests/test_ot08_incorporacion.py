"""T053 — partner en proceso no cuenta como cero días (SC-009)."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tests.almacen import (  # noqa: E402
    ID_HISTORIAL_PRUEBA,
    ID_PARTNER_PRUEBA,
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
            tipo_cambio="registro",
            estado_anterior=None,
            estado_nuevo="Registrado",
        ),
        cambio_de_prueba(
            ID_HISTORIAL_PRUEBA + 1,
            idpartner=ID_PARTNER_PRUEBA + 1,
            partner="Listo",
            tipo_cambio="registro",
            estado_anterior=None,
            estado_nuevo="Registrado",
            cuando="2099-12-01 08:00:00",
        ),
        cambio_de_prueba(
            ID_HISTORIAL_PRUEBA + 2,
            idpartner=ID_PARTNER_PRUEBA + 1,
            partner="Listo",
            tipo_cambio="activacion_produccion",
            estado_anterior="Pendiente de aprobación",
            estado_nuevo="Producción activa",
            cuando="2099-12-11 08:00:00",
        ),
    ])
    yield
    limpiar_partners()


@requiere_modelo
def test_en_proceso_fuera_de_la_media(escenario):
    filas = ejecutar_partners(
        "ot08_tiempo_incorporacion", desde="2099-12-01", hasta="2099-12-31"
    )
    por = {f["partner"]: f for f in filas}
    en_proceso = por["Partner prueba"]
    assert int(en_proceso["en_proceso"]) == 1
    assert en_proceso["dias"] is None
    listo = por["Listo"]
    assert int(listo["en_proceso"]) == 0
    assert int(listo["dias"]) == 10
