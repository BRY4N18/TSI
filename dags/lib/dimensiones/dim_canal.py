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


def normalizar(crudo: Any) -> str | None:
    """El canal en su forma canónica, o `None` si no se registró.

    Solo espacios y mayúsculas. Ver el docstring del módulo: agrupar canales
    distintos bajo un mismo nombre es una decisión de negocio, no de carga.
    """
    if crudo is None:
        return None
    texto = " ".join(str(crudo).split()).strip()
    if not texto:
        return None
    # Capitaliza la primera letra y deja el resto en minúscula: «REDES SOCIALES»
    # y «redes sociales» convergen sin destruir la legibilidad.
    canonico = texto[0].upper() + texto[1:].lower()
    # El alias se aplica **despues** de normalizar espacios y mayusculas, para
    # que la lista no tenga que repetir cada variante de capitalizacion.
    return ALIAS.get(canonico, canonico)


def construir(
    prospectos: Iterable[Mapping[str, Any]], ahora: datetime
) -> list[dict]:
    """Un canal por cada valor distinto del origen, ya normalizado.

    El identificador se asigna aquí y es **estable mientras el conjunto de
    canales no cambie**: sale del orden alfabético, no del orden en que Pinot
    devuelva las filas — que no está garantizado y haría que el mismo canal
    cambiara de identificador entre dos corridas.
    """
    canales = sorted({
        canal for canal in (normalizar(p.get("como_nos_conocio")) for p in prospectos)
        if canal
    })
    version = ahora.strftime("%Y-%m-%d %H:%M:%S")

    return [
        {"idcanal": indice, "canal": canal, "version": version}
        for indice, canal in enumerate(canales, start=1)
    ]
