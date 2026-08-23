"""Período sin llamadas: data vacía, no ceros de uptime.

⚠️ **Cuatro informes no devuelven vacío, y eso está declarado.**

`integraciones-activas`, `consumo-por-partner`, `excedente-facturable` y
`comparativa-partners` cuentan el **numerador dentro del período** y el
**denominador sobre el estado de hoy**. Pedido enero de 2019 responden
«3 partners con acceso, 0 % de adopción»: los tres son de hoy, y en 2019 no
existía ninguno.

Hasta que se cargaron los hechos, esta prueba pasaba **porque las tablas estaban
vacías**, no porque el informe se callara. Se decidió (opción C) **declarar** el
sesgo en vez de acotar el denominador —acotarlo exige historizar `dim_partner` y
cambiaría lo que el informe mide—, así que aquí se exige la declaración: una
cifra con denominador de hoy que **no** lo diga es la que engaña.
"""

from __future__ import annotations

import pytest

from apps.informes_estrategicos.tests.conftest import INFORMES_OE2, cliente, pedir_oe2
from apps.informes_estrategicos.services.oe2_service import (
    DENOMINADOR_ACTUAL,
)

VACIO = {"desde": "2019-01-01", "hasta": "2019-01-31", "granularidad": "mes"}


@pytest.mark.parametrize("informe", INFORMES_OE2)
def test_oe2_periodo_vacio(informe):
    rol = ["DirectorFinanciero"] if informe in {
        "excedente-facturable", "participacion-ingresos-api", "mrr-por-linea"
    } else ["DirectorTecnologico"]
    respuesta = pedir_oe2(cliente(rol), informe, **VACIO)
    if respuesta.status_code != 200:
        pytest.skip("el modelo analítico no está disponible")
    cuerpo = respuesta.json()
    assert cuerpo["meta"]["cobertura"] in {"completa", "parcial"}

    if informe in DENOMINADOR_ACTUAL:
        # No se exige vacío: se exige que la cifra diga contra qué se midió.
        assert cuerpo["meta"].get("denominador_actual"), (
            f"'{informe}' devolvió {cuerpo['data']!r} en un período sin datos "
            f"sin declarar que el denominador es actual"
        )
        return

    assert cuerpo["data"] == [], (
        f"'{informe}' devolvió {cuerpo['data']!r} en un período sin datos"
    )
