"""`dim_region`: una fila por **versión** de región operativa.

Versionada por la misma razón que la unidad: un informe de hace tres meses tiene
que decir en qué estado estaba la región **entonces**, no en cuál está hoy. Sin
versionar, despublicar una región reescribiría todos sus informes anteriores.

⚠️ El origen confunde dos cosas distintas, y este módulo las separa
--------------------------------------------------------------------
* **`estado_ciclo_vida`** — `Definida`, `En validación`, `Producción`,
  `Despublicada`. Vive en `Dim_RegionOperativa.estadoregion`.
* **`estado_geo`** — «Ciudad de Mexico». Vive en `Dim_EstadoRegion.estadoregion`,
  **pese al nombre**.

`Dim_RegionOperativaEstadoRegion` relaciona la región con **el segundo**, aunque
el catálogo de informes la citaba como fuente del primero. Se comprobó contra el
origen: sus dos filas apuntan a `Dim_EstadoRegion`, que contiene «Ciudad de
Mexico».

La confusión no sería inocua. Un informe de «regiones publicadas» que leyera la
geografía devolvería todas las regiones o ninguna, y **las dos respuestas parecen
plausibles**: con dos regiones en producción, «2 de 2» y «0 de 2» son cifras que
nadie cuestiona sin conocer el dato.

Solo `estado_ciclo_vida` abre versión
--------------------------------------
La geografía de una región no cambia; si cambiara, sería otra región. Versionar
por ella abriría versiones nuevas cada vez que alguien corrigiera una etiqueta.

⚠️ Todas las versiones iniciales llevan `inicio_es_real = 0`
------------------------------------------------------------
El estado actual se conoce; **desde cuándo lo es, no**. El origen no historiza el
cambio de estado de una región: guarda el estado presente y lo sobrescribe. Así
que la primera versión abre por la izquierda y declara que su fecha de inicio es
«desde que empezamos a mirar», no un cambio observado.

Es la misma marca que lleva la unidad, y por el mismo motivo. Ponerla a `1`
afirmaría que la región entró en producción el día de la primera carga, que es
falso y además fabrica precisión donde no la hay.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Callable, Iterable, Mapping

from lib.clickhouse_http_client import query_clickhouse
from lib.dimensiones.versionado import INICIO_DESCONOCIDO, decidir_version
from lib.hechos.comun import a_datetime
from lib.pinot_http_client import query_pinot

LIMITE = 500_000

#: Único atributo cuyo cambio abre versión. Ver el docstring.
ATRIBUTOS_VERSIONADOS_REGION = ("estado_ciclo_vida",)

#: ⚠️ `estadoregion` de **esta** tabla es el ciclo de vida.
CONSULTA_REGIONES = f"""
    SELECT idregionoperativa, nombreregion, estadoregion, idestado,
           fechaestadoregion
    FROM Dim_RegionOperativa
    WHERE activo = true
    LIMIT {LIMITE}
"""

#: ⚠️ `estadoregion` de **esta otra** es geografía, pese al nombre idéntico.
CONSULTA_ESTADOS_GEO = f"""
    SELECT idestadoregion, estadoregion
    FROM Dim_EstadoRegion
    LIMIT {LIMITE}
"""

#: La relación región → estado geográfico. No aporta el ciclo de vida.
CONSULTA_RELACION_GEO = f"""
    SELECT idregionoperativa, idestadoregion
    FROM Dim_RegionOperativaEstadoRegion
    WHERE activo = true
    LIMIT {LIMITE}
"""

CONSULTA_VIGENTES = """
    SELECT * FROM dim_region FINAL WHERE es_vigente = 1
"""


def extraer(
    consultar_origen: Callable[[str], list[dict]] = query_pinot,
    consultar_modelo: Callable[[str], list[dict]] = query_clickhouse,
) -> dict[str, list[dict]]:
    return {
        "regiones": consultar_origen(CONSULTA_REGIONES),
        "estados_geo": consultar_origen(CONSULTA_ESTADOS_GEO),
        "relacion_geo": consultar_origen(CONSULTA_RELACION_GEO),
        "vigentes": consultar_modelo(CONSULTA_VIGENTES),
    }


def aplanar(
    regiones: Iterable[Mapping[str, Any]],
    estados_geo: Iterable[Mapping[str, Any]],
    relacion_geo: Iterable[Mapping[str, Any]],
) -> list[dict]:
    """Una fila por región, con las dos nociones de «estado» ya separadas."""
    geo_por_id = {e["idestadoregion"]: e.get("estadoregion") for e in estados_geo}
    geo_por_region = {r["idregionoperativa"]: r.get("idestadoregion") for r in relacion_geo}

    filas = []
    for region in regiones:
        idregion = region["idregionoperativa"]
        idgeo = geo_por_region.get(idregion)
        filas.append(
            {
                "idregionoperativa": idregion,
                "nombre_region": region.get("nombreregion") or "",
                # Del campo de la región, no de la tabla de relación.
                "estado_ciclo_vida": region.get("estadoregion") or "Desconocido",
                "idestado_geo": idgeo,
                "estado_geo": geo_por_id.get(idgeo),
                # El país no está en el origen de regiones. Ausente, no inventado.
                "pais": None,
                # ⚠️ Desde cuándo está en ese estado. Lo sella el origen al
                # cambiarlo (`region_operativa_repository.update`). Es lo que
                # convierte la versión en un cambio **observado** en vez de
                # «desde que empezamos a mirar». Ver `construir`.
                "_instante_estado": region.get("fechaestadoregion"),
            }
        )
    return filas


def _serializar(fila: dict) -> dict:
    """Fechas a texto. `valido_hasta` ausente queda nulo, no época cero."""
    salida = dict(fila)
    for campo in ("valido_desde", "valido_hasta", "version"):
        valor = salida.get(campo)
        if isinstance(valor, datetime):
            salida[campo] = valor.strftime("%Y-%m-%d %H:%M:%S")
    return salida


def construir(
    regiones: Iterable[Mapping[str, Any]],
    estados_geo: Iterable[Mapping[str, Any]],
    relacion_geo: Iterable[Mapping[str, Any]],
    vigentes: Iterable[Mapping[str, Any]],
    ahora: datetime,
) -> list[dict]:
    """Filas a escribir. **Vacía si ninguna región cambió**, que es lo normal."""
    por_clave = {v["idregionoperativa"]: v for v in vigentes}

    # Se llama a `decidir_version` en vez de a `versionar_lote` porque el segundo
    # no propaga `campo_sk` y esta dimensión necesita `sk_region`, no
    # `sk_unidad`. Es el bucle que `versionar_lote` haría, con ese argumento de
    # más — y es preferible a tocar `versionado.py`, que sostiene la atribución
    # histórica de tres hechos ya en producción.
    filas: list[dict] = []
    for fila in aplanar(regiones, estados_geo, relacion_geo):
        vigente = por_clave.get(fila["idregionoperativa"])
        instante = _instante_observado(fila.pop("_instante_estado", None), vigente)
        resultado = decidir_version(
            fila,
            vigente,
            clave_negocio="idregionoperativa",
            atributos=ATRIBUTOS_VERSIONADOS_REGION,
            ahora=ahora,
            campo_sk="sk_region",
            instante_observado=instante,
        )
        filas.extend(resultado.filas)
    _verificar_sin_inicio_real(filas)
    return [_serializar(f) for f in filas]


def _instante_observado(
    marca: Any, vigente: Mapping[str, Any] | None
) -> datetime | None:
    """El instante real del cambio de estado, o nada.

    ⚠️ **La primera versión de una región nunca lo lleva**, aunque el origen
    traiga la marca: se sabe cuándo entró en el estado *actual*, no cuándo entró
    en el que tenía antes de que empezáramos a mirar. Abrir la primera versión
    en esa fecha dejaría sin cubrir todo lo anterior, y `_verificar_sin_inicio_real`
    lo rechaza por eso mismo (T006).

    A partir de la segunda, la marca **sí** es la fecha del cambio observado:
    `region_operativa_repository` la sella al cambiar `estadoregion`.
    """
    if vigente is None or marca in (None, "", 0):
        return None
    try:
        valor = int(marca)
    except (TypeError, ValueError):
        return None
    if valor <= 0:
        return None
    return a_datetime(valor)


def _verificar_sin_inicio_real(filas: Iterable[Mapping[str, Any]]) -> None:
    """Ninguna versión **inicial** de región puede declarar un inicio real (T006).

    Se comprueba aquí y no solo en una prueba porque es una afirmación **sobre el
    origen**: nada historiza el cambio de estado de una región. Si algún día el
    origen empezara a historizarlo, este error salta y obliga a decidir
    conscientemente —reconstruir el histórico— en vez de que la marca cambie de
    significado sin que nadie lo advierta.

    Las versiones **posteriores** sí llevan `inicio_es_real = 1`: esas sí
    corresponden a un cambio observado entre dos corridas.
    """
    mentirosas = [
        f for f in filas
        if f.get("inicio_es_real") == 1 and f.get("valido_desde") == INICIO_DESCONOCIDO
    ]
    if mentirosas:
        raise ValueError(
            f"{len(mentirosas)} versiones iniciales de región declaran inicio real. "
            f"El origen no historiza el estado de una región: si ahora lo hace, "
            f"hay que decidir qué hacer con el histórico anterior."
        )
