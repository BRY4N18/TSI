"""Todo porcentaje de OE2 trae denominador."""

from __future__ import annotations

import pytest

from apps.informes_estrategicos.tests.conftest import INFORMES_OE2, cliente, pedir_oe2

DENOMS = (
    "denominador",
    "partners_con_acceso",
    "llamadas",
    "muestras",
    "cupo",
    "ingreso_total",
)


@pytest.mark.parametrize("informe", INFORMES_OE2)
def test_oe2_porcentaje_con_denominador(informe):
    rol = ["DirectorFinanciero"] if informe in {
        "excedente-facturable", "participacion-ingresos-api", "mrr-por-linea"
    } else ["DirectorTecnologico"]
    respuesta = pedir_oe2(cliente(rol), informe)
    if respuesta.status_code != 200:
        pytest.skip("el modelo analítico no está disponible")
    for fila in respuesta.json()["data"]:
        claves = set(fila)
        hay_pct = any("pct" in k or k.startswith("tasa") for k in claves)
        if hay_pct:
            assert claves & set(DENOMS), claves
