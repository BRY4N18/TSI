"""T061 — un período sin datos devuelve cero filas, no una fila de ceros.

⚠️ **Dos informes son la excepción, y está declarada.**

`ot17_cuentas_en_riesgo` y `ot17_usuarios_vs_tope` listan **todas las cuentas de
`dim_cliente`** aunque el período no tenga un solo hecho: devuelven una fila por
cliente con `sin_actividad_conocida: 1`. Es defendible —«de estas cuentas no
sabemos nada» es justo la anomalía que la supervisión busca— pero entonces el
total **no es del período**, y quien lea «7 cuentas en riesgo en julio» tiene que
poder saberlo.

Hasta que se cargó `dim_cliente`, esta prueba pasaba **porque la dimensión estaba
vacía**, no porque el informe se callara. Se decidió (opción C) declarar el sesgo
en `nota_denominador_actual` en vez de acotar el denominador, que exigiría
historizar la dimensión y cambiaría lo que el informe mide.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from lib.consultas import listar  # noqa: E402

from tests.almacen import asegurar_hechos_cuentas, ejecutar_cuentas, requiere_modelo  # noqa: E402

INFORMES = [i for i in listar("cuentas") if i != "ot04_embudo_abandono"]

#: Cuentan sobre el estado de hoy, no sobre el período. Ver el docstring y
#: `CuentasCompuestosService.INFORMES_DENOMINADOR_ACTUAL`, que es quien publica
#: la declaración en la respuesta.
#: Informe → columna con la que **cada fila** declara que no mide el período.
DENOMINADOR_ACTUAL = {
    # «De esta cuenta no sabemos nada», en vez de inventar un cero de actividad.
    "ot17_cuentas_en_riesgo": "sin_actividad_conocida",
    # La ocupación va con la fracción de usuarios cuya pertenencia se conoce:
    # sin ella, «10 % ocupado» parecería medido sobre la plantilla entera.
    "ot17_usuarios_vs_tope": "pct_cobertura_pertenencia",
}
VACIO = "1999-01-01"


@requiere_modelo
@pytest.mark.parametrize("informe", INFORMES)
def test_periodo_vacio_devuelve_cero_filas(informe):
    asegurar_hechos_cuentas()
    from tests.almacen import limpiar_cuentas

    limpiar_cuentas()
    filas = ejecutar_cuentas(
        informe,
        desde=VACIO,
        hasta=VACIO,
        mes_cohorte="1999-01",
        pares="",
    )
    if informe in DENOMINADOR_ACTUAL:
        # No se exige vacío. Lo que sí se exige: que **cada fila** lleve su
        # declaración, porque es lo que distingue una cuenta de la que no se sabe
        # nada de una cuenta medida y tranquila.
        columna = DENOMINADOR_ACTUAL[informe]
        for fila in filas:
            assert columna in fila, (
                f"'{informe}' devolvió una fila sin «{columna}», así que la cifra "
                f"no dice contra qué se midió: {fila!r}"
            )
        return

    assert filas == [], (
        f"'{informe}' devolvió {filas!r} en un período sin datos"
    )
