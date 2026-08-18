"""T063 — un período sin llamadas devuelve cero filas."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from lib.consultas import listar  # noqa: E402

from tests.almacen import asegurar_hechos_partners, ejecutar_partners, limpiar_partners, requiere_modelo  # noqa: E402

#: Informes que parten de dimensiones y pueden devolver filas sin tráfico.
DIMENSIONALES = {
    "ot09_comparativa_partners",
    "ot09_metricas_consumo",
    "ot08_motivo_credencial_inactiva",
    "ot08_tiempo_incorporacion",
    "ot10_clientes_integracion_activa",
}
INFORMES = [i for i in listar("partners") if i not in DIMENSIONALES]
VACIO = "1999-01-01"


@requiere_modelo
@pytest.mark.parametrize("informe", INFORMES)
def test_periodo_vacio_devuelve_cero_filas(informe):
    asegurar_hechos_partners()
    limpiar_partners()
    filas = ejecutar_partners(informe, desde=VACIO, hasta=VACIO, mes="1999-01")
    assert filas == [], f"'{informe}' devolvió {filas!r}"
