"""`dim_canal`: el canal por el que llegó un prospecto.

⚠️ El origen lo guarda como **texto libre**
--------------------------------------------
`Dim_Prospecto.como_nos_conocio` lo escribe quien registra el prospecto. Sin
normalizar, «Redes sociales», «redes sociales» y «  Redes Sociales » son tres
canales distintos, y el informe de rendimiento por canal repartiría el mismo
canal en tres filas con un tercio del volumen cada una. **Ninguna de las tres
parecería importante**, y la decisión de dónde invertir se tomaría sobre un
reparto inventado por las mayúsculas.

La normalización es deliberadamente conservadora: espacios y mayúsculas, nada
más. Agrupar «Facebook» con «Redes sociales» sería una decisión de negocio —puede
que se quiera ver Facebook aparte— y no le corresponde a la carga tomarla.

⚠️ La fila desconocida cuenta en los totales
---------------------------------------------
Un prospecto sin canal registrado **llegó igual**. Dejarlo fuera haría que la
suma de los canales fuera menor que el total del embudo, y los porcentajes
seguirían sumando 100 % entre ellos sin que nada lo delatara.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Iterable, Mapping


#: Variantes que son **el mismo canal**, declaradas una a una.
#:
#: ⚠️ Esto no se deduce, se decide. «Web / catalogo planes» y «Web / catalogo de
#: planes» son el mismo canal —falta un «de»— pero «Referido institucional» y
#: «Referido tsi» **no lo son**, y ninguna regla automatica que junte el primer
#: par deja el segundo en paz.
#:
#: Se midio sobre los datos de hoy: sin este mapa, ese canal aparece como dos
#: filas de 2 y 1 sobre 10 prospectos, cuando en realidad es el **mayor** con 3.
#: El informe de rendimiento por canal no lo mostraria como tal, y la decision de
#: donde invertir se tomaria sobre un reparto que invento un error de tecleo.
#:
#: Cada entrada es una decision de negocio. Anadir una sin preguntar juntaria
#: canales que alguien quiere ver por separado, que es el error simetrico y peor:
#: el primero se ve mirando la lista, este desaparece.
ALIAS = {
    "Web / catalogo planes": "Web / catálogo de planes",
    "Web / catálogo planes": "Web / catálogo de planes",
}


def limpiar(crudo: Any) -> str | None:
    """El texto del origen sin espacios sobrantes, o `None` si no se registró.

    **Conserva las mayúsculas tal como se escribieron.** Es la grafía que se
    muestra; agrupar es otra cosa y la hace `clave`.
    """
    if crudo is None:
        return None
    texto = " ".join(str(crudo).split()).strip()
    return texto or None


def clave(crudo: Any) -> str | None:
    """La clave con la que dos escrituras cuentan como **el mismo canal**.

    Solo sirve para agrupar: no se muestra nunca. Ver `construir`.
    """
    texto = limpiar(crudo)
    if texto is None:
        return None
    # El alias se aplica sobre la forma plegada, para que la lista no tenga que
    # repetir cada variante de capitalización.
    plegado = texto.casefold()
    return {k.casefold(): v.casefold() for k, v in ALIAS.items()}.get(plegado, plegado)


def normalizar(crudo: Any) -> str | None:
    """La forma canónica de un canal **aislado**, sin más contexto.

    ⚠️ Devuelve la grafía tal como se escribió, no una capitalización forzada.

    Hasta el 2026-08-19 hacía `texto[0].upper() + texto[1:].lower()`. La
    intención era buena —«REDES SOCIALES» y «redes sociales» tienen que
    converger— pero **usaba la misma cadena para agrupar y para mostrar**, y al
    forzar el resto a minúscula destrozaba los nombres propios: en pantalla
    salían «Linkedin» y «Referido tsi» cuando el origen dice «LinkedIn» y
    «Referido TSI».

    Ahora las dos cosas están separadas: `clave` agrupa sin distinguir
    mayúsculas y esto conserva lo que se escribió. `construir` elige qué grafía
    representa al grupo cuando hay varias.
    """
    texto = limpiar(crudo)
    if texto is None:
        return None
    return ALIAS.get(texto, texto)


def construir(
    prospectos: Iterable[Mapping[str, Any]], ahora: datetime
) -> list[dict]:
    """Un canal por cada valor distinto del origen, ya normalizado.

    El identificador se asigna aquí y es **estable mientras el conjunto de
    canales no cambie**: sale del orden alfabético, no del orden en que Pinot
    devuelva las filas — que no está garantizado y haría que el mismo canal
    cambiara de identificador entre dos corridas.
    """
    from collections import Counter

    # Grafías vistas por clave de agrupación. La clave no se muestra jamás.
    grafias: dict[str, Counter] = {}
    for p in prospectos:
        crudo = p.get("como_nos_conocio")
        k = clave(crudo)
        if k is None:
            continue
        grafias.setdefault(k, Counter())[normalizar(crudo)] += 1

    # ⚠️ **La grafía que representa al grupo se elige de forma determinista.**
    #
    # Lo pedido era «la primera que se vio», pero «primera» depende del orden en
    # que Pinot devuelva las filas, y ese orden no está garantizado: el mismo
    # canal se mostraría «LinkedIn» en una corrida y «linkedin» en la siguiente,
    # y el identificador —que sale del orden alfabético justamente para ser
    # estable— dejaría de acompañar a un nombre estable.
    #
    # Se toma la **más frecuente**, que es la que la gente escribe de verdad, y
    # se desempata por orden alfabético.
    canales = sorted(
        min(cuenta, key=lambda g: (-cuenta[g], g)) for cuenta in grafias.values()
    )
    version = ahora.strftime("%Y-%m-%d %H:%M:%S")

    return [
        {"idcanal": indice, "canal": canal, "version": version}
        for indice, canal in enumerate(canales, start=1)
    ]
