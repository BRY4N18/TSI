"""T013 y T014 — las reglas del catálogo de Red Operativa, sobre el **texto**.

La regla propia de este departamento —no unir con el catálogo de estados— y las
comunes —la versión final, el orden, el rango—.

⚠️ Todas se comprueban sobre el texto y no sobre el resultado, porque los fallos
que vigilan **no se ven ejecutando la consulta una vez**: un `JOIN` con el
catálogo devuelve filas perfectamente plausibles, y una consulta sin `FINAL`
devuelve cifras infladas solo a veces.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from lib.consultas import cargar, listar  # noqa: E402

DEPARTAMENTO = "red_operativa"
INFORMES = listar(DEPARTAMENTO)

#: `FINAL` obligatorio: dimensiones versionadas y hechos de instantánea.
CON_FINAL = ("dim_region", "dim_unidad", "dim_geografia", "hecho_despacho")

#: `FINAL` prohibido: hechos de transacción. Pedirlo falla con `ILLEGAL_FINAL`.
SIN_FINAL = ("hecho_estado_unidad", "hecho_ping_unidad", "hecho_baja_unidad")

#: Informes de **estado actual**, no de período.
#:
#: ⚠️ Se declaran uno a uno, y la lista es la prueba. La regla general —toda
#: consulta acepta y filtra el rango— existe porque un informe que ignora el
#: rango devuelve lo mismo para cualquier período y nadie lo nota. Pero
#: «pendientes de primer acceso» pregunta **qué unidades están pendientes
#: ahora**, no cuáles lo estuvieron en marzo: darle un `desde` sería un parámetro
#: que no filtra nada, o peor, que filtra por una fecha de alta que 15 de 18
#: unidades no tienen y las dejaría fuera justo a ellas.
#:
#: Usan `{hasta:Date}` como **corte**, que es lo que les da sentido: «pendientes
#: a fecha de». Sin él serían no reproducibles.
DE_ESTADO_ACTUAL = frozenset({
    "ot12_pendientes_primer_acceso",
    # Las dos de cobertura miden **que cobertura hay**, no la que hubo: leen la
    # version vigente de unidad y geografia. Un `desde` las convertiria en otra
    # pregunta -«que cobertura hubo en marzo»- que el modelo si podria responder,
    # pero que no es la que el catalogo pide y exigiria recorrer las versiones.
    "ot12_cobertura_flota_por_region",
    "ot12_condados_cobertura_critica",
    # «Mercados activos» es un **corte**: cuantas regiones hay en cada estado a
    # fecha de. Un `desde` sugeriria un flujo —cuantas entraron en el periodo—
    # que es otra pregunta y necesita el historial de versiones.
    "ot11_mercados_activos",
    # La puesta en operacion mide desde la primera validacion de cada region
    # hasta que entro en produccion, y esos dos instantes son propios de la
    # region: acotarlos por un `desde` recortaria la medida a la mitad y daria
    # duraciones menores de las reales.
    "ot11_tiempo_puesta_operacion",
    # Los tres de OT13 son cortes: «que regiones estan en riesgo **a fecha de**»,
    # «cuanto se tarda en retirar una region» y «cuantos casos quedaron abiertos
    # al despublicarla». Los dos ultimos miden desde la primera version de cada
    # region hasta su despublicacion, y esos instantes son propios de la region:
    # acotarlos por un `desde` recortaria la medida y daria tiempos menores de
    # los reales, que en un informe de reaccion es el error que halaga.
    "ot13_regiones_en_riesgo",
    "ot13_tiempo_perdida_a_despublicacion",
    "ot13_casos_activos_al_despublicar",
})

#: El catálogo de estados de unidad del origen. **Ninguna consulta lo une.**
CATALOGO_DE_ESTADOS = ("Dim_EstadoUnidadEmergencia", "dim_estado_unidad")


def cuerpo(nombre: str) -> str:
    return "\n".join(
        l for l in cargar(nombre, departamento=DEPARTAMENTO).splitlines()
        if not l.strip().startswith("--")
    )


def _apariciones(texto: str, tabla: str) -> list[bool]:
    return [
        re.match(r"\s*(?:AS\s+\w+\s+|\w+\s+)?FINAL\b", m.group(1)) is not None
        for m in re.finditer(rf"\b(?:FROM|JOIN)\s+{tabla}\b(.*)", texto)
    ]


def test_el_catalogo_no_esta_vacio():
    """⚠️ Sin esto, todas las pruebas de abajo pasarían sin mirar nada.

    Son comprobaciones que recorren el catálogo: con cero consultas, el bucle no
    itera y el fichero entero queda en verde sin haber comprobado una sola regla.
    Es la forma más silenciosa de tener pruebas que no prueban.
    """
    assert INFORMES, "el catálogo de Red Operativa está vacío"


@pytest.mark.parametrize("informe", INFORMES)
def test_ninguna_consulta_une_con_el_catalogo_de_estados(informe):
    """⚠️ T013 — la regla propia del departamento.

    Unir con `Dim_EstadoUnidadEmergencia` es lo correcto en un modelo bien
    formado, y aquí **pierde el 13 % de los datos sin fallar**: el catálogo tiene
    tres estados y el histórico usa cuatro. De 45 transiciones, 6 son `En Misión`
    y no están en él.

    Un `INNER JOIN` devolvería 39 filas verosímiles. No hay error, no hay aviso,
    y lo que desaparece es justamente la actividad de las unidades trabajando.
    """
    texto = cuerpo(informe)

    for catalogo in CATALOGO_DE_ESTADOS:
        assert catalogo not in texto, (
            f"'{informe}' toca '{catalogo}': ese catálogo está incompleto y unir "
            f"con él pierde las transiciones a 'En Misión' sin que nada falle"
        )


@pytest.mark.parametrize("informe", INFORMES)
def test_el_estado_se_lee_por_su_texto(informe):
    """La otra mitad de la misma regla: si no se une, hay que leer el nombre.

    Comprobar solo que no se une dejaría pasar una consulta que agrupara por
    `idestadounidademergencia` —el identificador— y publicara números en vez de
    estados. No perdería filas, pero el informe sería ilegible y la primera
    tentación al arreglarlo sería volver a unir con el catálogo.
    """
    texto = cuerpo(informe)
    if "hecho_estado_unidad" not in texto:
        pytest.skip(f"'{informe}' no lee estados de unidad")

    assert "estado_nuevo" in texto, (
        f"'{informe}' lee transiciones de estado y no usa 'estado_nuevo': "
        f"el nombre del estado viene resuelto en el hecho, precisamente para no "
        f"tener que unir con el catálogo"
    )


@pytest.mark.parametrize("informe", INFORMES)
def test_la_regla_de_version_final(informe):
    """T014. Omitirla infla las cifras **solo a veces**; pedirla de más falla."""
    texto = cuerpo(informe)

    for tabla in CON_FINAL:
        apariciones = _apariciones(texto, tabla)
        assert all(apariciones), (
            f"'{informe}' toca {tabla} sin forzar la versión final: devolverá "
            f"cifras infladas tras una recarga, y solo a veces"
        )

    for tabla in SIN_FINAL:
        assert not any(_apariciones(texto, tabla)), (
            f"'{informe}' pide FINAL sobre {tabla}, que es de transacción: "
            f"falla con ILLEGAL_FINAL"
        )


@pytest.mark.parametrize("informe", INFORMES)
def test_la_forma_de_la_consulta(informe):
    texto = cuerpo(informe)

    assert re.search(r"^ORDER BY", texto, re.MULTILINE), (
        f"'{informe}' no ordena su salida: comparar dos corridas dejaría de ser "
        f"posible. Un ORDER BY dentro de una función de ventana no cuenta"
    )
    assert "SELECT *" not in texto.upper(), f"'{informe}' usa SELECT *"
    assert "{hasta:Date}" in texto, (
        f"'{informe}' no acepta ningún corte de fecha: devolvería lo mismo para "
        f"cualquier período y dos capturas no serían comparables"
    )
    if informe in DE_ESTADO_ACTUAL:
        return
    assert "{desde:Date}" in texto, (
        f"'{informe}' no acepta 'desde'. Si es un informe de estado actual y no "
        f"de período, decláralo en DE_ESTADO_ACTUAL con su razón"
    )


def test_lo_declarado_de_estado_actual_existe():
    """Una entrada muerta dejaría exenta a una consulta que ya no está.

    Y peor: si mañana se creara otra con ese nombre, nacería exenta de la regla
    sin que nadie lo decidiera.
    """
    assert DE_ESTADO_ACTUAL <= set(INFORMES), (
        f"sobran: {sorted(DE_ESTADO_ACTUAL - set(INFORMES))}"
    )
