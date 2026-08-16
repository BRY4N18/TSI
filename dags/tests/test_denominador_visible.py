"""T074 — todo porcentaje viene con su denominador.

Un 12,5 % sobre 8 casos y un 12,5 % sobre 8 000 son afirmaciones muy distintas, y
en una pantalla se ven exactamente igual. La primera es ruido —un caso de ocho— y
la segunda es un problema de mil casos.

Sin el denominador no hay forma de distinguirlas, y tampoco de **recomponer** un
porcentaje de período a partir de los diarios: promediar tasas diarias da un
número distinto y plausible. Es el obstáculo que apareció tres veces al escribir
las pruebas de contraste, en `descarte-fusion`, en `abortos-perdidas` y en
`cierres-forzados`, los tres del diseño anterior. Esta prueba es lo que impide
que el catálogo nuevo repita el error.

La regla es del catálogo, no de un informe: se recorre entero.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from lib.consultas import cargar, listar  # noqa: E402

INFORMES = listar("emergencias")

#: Columnas que sirven de denominador. No se exige una en concreto porque cada
#: informe cuenta lo suyo: casos, despachos, intentos, evidencias, llegadas.
DENOMINADORES = (
    "casos", "despachos", "intentos", "evidencias", "llegadas", "medidos",
    "confirmados", "cerrados", "intervalos_medidos", "llegadas_medidas",
    "unidades_vigentes", "casos_abiertos", "calificados",
)


def columnas_de(informe: str) -> list[str]:
    """Los alias de salida, en orden. Es lo que el consumidor recibe."""
    cuerpo = "\n".join(
        l for l in cargar(informe, departamento="emergencias").splitlines()
        if not l.strip().startswith("--")
    )
    return re.findall(r"\bAS\s+([A-Za-z_][A-Za-z0-9_]*)", cuerpo)


@pytest.mark.parametrize("informe", INFORMES)
def test_todo_porcentaje_va_acompanado_de_su_denominador(informe):
    columnas = columnas_de(informe)
    porcentajes = [c for c in columnas if c.startswith("pct") or c == "ratio"]
    if not porcentajes:
        pytest.skip(f"'{informe}' no publica ningún porcentaje")

    tiene_denominador = any(
        c == d or c.endswith("_" + d) or c.startswith(d)
        for c in columnas
        for d in DENOMINADORES
    )

    assert tiene_denominador, (
        f"'{informe}' publica {porcentajes} y ninguna columna que diga sobre "
        f"cuántos. Un 12,5 % sobre 8 y sobre 8 000 se leen igual, y sus tasas no "
        f"se pueden recomponer en una del período"
    )


#: Cada porcentaje con la columna que lo produce, declarada a mano.
#:
#: Se declara en vez de deducirse del nombre. La primera version de esta prueba
#: intentaba emparejarlos por morfologia -`pct_descarte` con `descartados`,
#: `pct_huecos` con `huecos`- y fallaba en siete informes de veintiseis: en
#: espanol el plural del nombre no se deriva del singular del prefijo
#: (`pct_retiro_forzado` frente a `retiros_forzados`), y ninguna regla razonable
#: los junta.
#:
#: Una regla que no funciona se relaja hasta no comprobar nada. Un mapa escrito a
#: mano no se relaja: un informe nuevo sin entrada falla, que es el defecto
#: correcto.
NUMERADORES = {
    "ot21_completitud_campos_criticos": {"pct_completitud": "completos"},
    "ot21_descarte_fusion": {"pct_descarte": "descartados", "pct_fusion": "fusionados"},
    "ot21_distribucion_severidad": {"pct": "casos"},
    "ot21_distribucion_zona": {"pct": "casos"},
    "ot22_asignacion_automatica_vs_manual": {"pct": "despachos"},
    "ot22_primer_intento": {"pct_primer_intento": "resueltos_primer_intento"},
    "ot22_ratio_demanda_capacidad": {"ratio": "casos"},
    "ot22_rechazo_timeout_por_unidad": {
        "pct_rechazo": "rechazados", "pct_vencimiento": "vencidos",
    },
    "ot23_abortos_perdidas": {"pct_aborto": "abortados"},
    "ot23_perdida_senal": {"pct_huecos": "huecos"},
    "ot24_cobertura_evidencia": {"pct_con_alguna": "casos"},
    "ot24_completitud_enriquecimiento": {"pct_enriquecidos": "enriquecidos"},
    "ot25_cierres_forzados": {"pct_con_retiro_forzado": "con_retiro_forzado"},
    "ot25_retiros_forzados_por_proveedor": {"pct_retiro_forzado": "retiros_forzados"},
}


@pytest.mark.parametrize("informe", INFORMES)
def test_todo_porcentaje_lleva_su_numerador_al_lado(informe):
    """No basta con el denominador: hace falta la fraccion entera.

    Con el total y la tasa se puede reconstruir el numerador dividiendo, si -con
    el redondeo de la tasa metido dentro-. Publicar los dos enteros evita esa
    reconstruccion y hace la cifra **comprobable a mano**, que es lo que permite
    a alguien discutirla.
    """
    columnas = columnas_de(informe)
    porcentajes = [c for c in columnas if c.startswith("pct") or c == "ratio"]
    if not porcentajes:
        pytest.skip(f"'{informe}' no publica ningun porcentaje")

    declarados = NUMERADORES.get(informe)
    assert declarados is not None, (
        f"'{informe}' publica {porcentajes} y no esta en NUMERADORES: nadie "
        f"declaro que columna produce cada tasa"
    )

    for pct in porcentajes:
        numerador = declarados.get(pct)
        assert numerador, f"'{informe}': falta declarar el numerador de '{pct}'"
        assert numerador in columnas, (
            f"'{informe}' publica '{pct}' pero no '{numerador}', que es lo que "
            f"lo produce: la fraccion no se puede comprobar a mano"
        )


def test_no_sobra_ninguna_entrada_en_el_mapa():
    """Un informe retirado dejaria una entrada muerta, y con ella la impresion
    de que algo se sigue vigilando."""
    assert set(NUMERADORES) <= set(INFORMES), (
        f"sobran entradas: {sorted(set(NUMERADORES) - set(INFORMES))}"
    )
