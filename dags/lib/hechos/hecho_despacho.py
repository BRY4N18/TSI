"""`hecho_despacho`: instantánea acumulada, **grano un intento de asignación**.

Por qué el grano es el intento y no el caso
--------------------------------------------
Un caso puede intentar despachar varias veces: la primera unidad rechaza, la
segunda no contesta, la tercera confirma. Con grano «caso» esos tres intentos se
colapsan en uno y **el rechazo desaparece de las cifras** — justo lo que un
informe de rendimiento por proveedor necesita ver.

Con grano intento, «despachos resueltos al primer intento» es contable:
`numero_intento = 1 AND resultado = 'confirmado'`.

De dónde salen los hitos ⚠️
----------------------------
No de `Fact_NotificacionDespacho`, que **no tiene hora propia de confirmación ni
de rechazo** —solo su última escritura— y además está prácticamente vacía: 31
filas para 4 314 despachos. Construir sobre ella habría producido cifras
plausibles y falsas.

Los hitos vienen de `Fact_HistorialDespachoUnidad`, que sí registra cada
transición con su instante y su motivo. La llegada y el retiro se toman de
`Fact_Despacho`, que los guarda directamente.

La atribución histórica, que es el motivo de todo esto
-------------------------------------------------------
`sk_unidad` es la **versión de unidad vigente al despachar**, y `proveedor` se
copia de esa versión. Copiar el proveedor actual reintroduciría exactamente el
defecto que el modelo existe para corregir: cambiar hoy de proveedor reescribiría
seis meses de historia.

Un despacho anterior al inicio del versionado apunta a la **versión desconocida**
en vez de a la actual. Es información honesta —«esto es anterior a que
empezáramos a mirar»— en lugar de una atribución inventada.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Callable, Iterable, Mapping

from lib.clickhouse_http_client import query_clickhouse
from lib.dimensiones.desconocido import ETIQUETA_DESCONOCIDA, ID_DESCONOCIDO, SK_DESCONOCIDO
from lib.hechos.atribucion import resolver_unidad_historica, versiones_por_unidad
from lib.hechos.comun import (
    FORMATO,
    a_datetime,
    agrupar_por,
    indexar_por,
    segundos_entre,
    texto_fecha,
)
from lib.pinot_http_client import query_pinot

LIMITE = 500_000

#: Estados de despacho, según `Dim_EstadoDespacho` del origen.
ESTADO_CONFIRMADO = 2
ESTADO_RECHAZADO = 3
ESTADO_TIMEOUT = 4
ESTADO_ABORTADO = 5

#: Estado terminal → resultado del intento. Los no terminales dejan el intento
#: `en_curso`, que es distinto de «terminó sin éxito» y no debe confundirse.
#:
#: ⚠️ `abortado` **no estaba en el contrato**, que enumeraba cuatro resultados.
#: Existe en el catálogo del origen y el informe de rendimiento por proveedor ya
#: publica un porcentaje de abortos, así que plegarlo a `en_curso` habría vaciado
#: en silencio una cifra que hoy se publica.
RESULTADO_POR_ESTADO = {
    ESTADO_CONFIRMADO: "confirmado",
    ESTADO_RECHAZADO: "rechazado",
    ESTADO_TIMEOUT: "vencido",
    ESTADO_ABORTADO: "abortado",
}

RESULTADO_EN_CURSO = "en_curso"

CONSULTA_DESPACHOS = f"""
    SELECT iddespacho, idaccidente, idunidademergencia, idorigendespacho,
           retiro_forzado, fechahoradespacho, fechahorallegada, fechahoraretiro
    FROM Fact_Despacho
    LIMIT {LIMITE}
"""

CONSULTA_HISTORIAL = f"""
    SELECT iddespacho, idestadodespacho, motivo, fechahora
    FROM Fact_HistorialDespachoUnidad
    LIMIT {LIMITE}
"""

CONSULTA_ACCIDENTES = f"""
    SELECT idaccidente, idseveridad, idcalle FROM Fact_Accidente LIMIT {LIMITE}
"""

#: Desde el modelo: las copias desnormalizadas salen de la dimensión, no del
#: origen, para que no puedan divergir de ella.
CONSULTA_DIM_UNIDAD = "SELECT * FROM dim_unidad FINAL"
CONSULTA_DIM_ORIGEN = "SELECT idorigendespacho, origen FROM dim_origen_despacho FINAL"
CONSULTA_DIM_SEVERIDAD = "SELECT idseveridad, severidad FROM dim_severidad FINAL"
CONSULTA_DIM_GEOGRAFIA = "SELECT idcalle, condado FROM dim_geografia FINAL"


def extraer(
    consultar_origen: Callable[[str], list[dict]] = query_pinot,
    consultar_modelo: Callable[[str], list[dict]] = query_clickhouse,
) -> dict[str, list[dict]]:
    return {
        "despachos": consultar_origen(CONSULTA_DESPACHOS),
        "historial": consultar_origen(CONSULTA_HISTORIAL),
        "accidentes": consultar_origen(CONSULTA_ACCIDENTES),
        "dim_unidad": consultar_modelo(CONSULTA_DIM_UNIDAD),
        "dim_origen": consultar_modelo(CONSULTA_DIM_ORIGEN),
        "dim_severidad": consultar_modelo(CONSULTA_DIM_SEVERIDAD),
        "dim_geografia": consultar_modelo(CONSULTA_DIM_GEOGRAFIA),
    }


def _numerar_intentos(despachos: Iterable[Mapping[str, Any]]) -> dict[Any, int]:
    """Ordinal de cada intento dentro de su caso, por orden de despacho.

    Se numera por el instante y se desempata por identificador: sin desempate,
    dos intentos simultáneos recibirían un ordinal distinto en cada corrida y
    «resueltos al primer intento» daría una cifra diferente cada día.
    """
    numeros: dict[Any, int] = {}
    for _, del_caso in agrupar_por(despachos, "idaccidente").items():
        ordenados = sorted(
            del_caso,
            key=lambda d: (d.get("fechahoradespacho") or 0, d["iddespacho"]),
        )
        for posicion, despacho in enumerate(ordenados, start=1):
            numeros[despacho["iddespacho"]] = posicion
    return numeros


def _hitos_del_historial(transiciones: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    """Confirmación, rechazo, resultado y motivo, a partir de las transiciones."""
    ordenadas = sorted(transiciones, key=lambda t: t.get("fechahora") or 0)

    def primera(estado: int) -> Mapping[str, Any] | None:
        return next((t for t in ordenadas if t.get("idestadodespacho") == estado), None)

    confirmacion = primera(ESTADO_CONFIRMADO)
    rechazo = primera(ESTADO_RECHAZADO)

    resultado = RESULTADO_EN_CURSO
    motivo = None
    for transicion in reversed(ordenadas):
        estado = transicion.get("idestadodespacho")
        if estado in RESULTADO_POR_ESTADO:
            resultado = RESULTADO_POR_ESTADO[estado]
            motivo = transicion.get("motivo")
            break

    return {
        "hora_confirmacion": a_datetime(confirmacion.get("fechahora")) if confirmacion else None,
        "hora_rechazo": a_datetime(rechazo.get("fechahora")) if rechazo else None,
        "resultado": resultado,
        "motivo_rechazo": motivo if resultado == "rechazado" else None,
    }


def construir(datos: Mapping[str, Iterable[Mapping[str, Any]]], ahora: datetime) -> list[dict]:
    """Una fila por intento de despacho. Lógica pura: no consulta ni escribe."""
    despachos = list(datos["despachos"])
    historial = agrupar_por(datos["historial"], "iddespacho")
    accidentes = indexar_por(datos["accidentes"], "idaccidente")
    versiones = versiones_por_unidad(datos["dim_unidad"])
    origenes = indexar_por(datos["dim_origen"], "idorigendespacho")
    severidades = indexar_por(datos["dim_severidad"], "idseveridad")
    geografia = indexar_por(datos["dim_geografia"], "idcalle")
    numeros = _numerar_intentos(despachos)
    marca = ahora.strftime(FORMATO)

    filas = []
    for d in despachos:
        momento = a_datetime(d.get("fechahoradespacho"))
        if momento is None:
            # Sin instante no hay partición ni atribución histórica posibles.
            continue

        hitos = _hitos_del_historial(historial.get(d["iddespacho"], []))
        llegada = a_datetime(d.get("fechahorallegada"))
        retiro = a_datetime(d.get("fechahoraretiro"))

        version = resolver_unidad_historica(versiones, d.get("idunidademergencia"), momento)
        accidente = accidentes.get(d.get("idaccidente"), {})
        idseveridad = accidente.get("idseveridad")
        origen = origenes.get(d.get("idorigendespacho"), {})

        filas.append(
            {
                "iddespacho": d["iddespacho"],
                "idaccidente": d.get("idaccidente"),
                "fecha": momento.date().isoformat(),
                "fechahora_despacho": texto_fecha(momento),
                # ⚠️ La versión de aquel momento, no la actual.
                "sk_unidad": version["sk_unidad"] if version else SK_DESCONOCIDO,
                "idunidademergencia": d.get("idunidademergencia") or ID_DESCONOCIDO,
                "unidad": (version or {}).get("placa") or ETIQUETA_DESCONOCIDA,
                "proveedor": (version or {}).get("proveedor") or ETIQUETA_DESCONOCIDA,
                "idorigendespacho": d.get("idorigendespacho") or ID_DESCONOCIDO,
                "origen_despacho": origen.get("origen") or ETIQUETA_DESCONOCIDA,
                "idseveridad": idseveridad,
                "severidad": severidades.get(idseveridad, {}).get("severidad"),
                "condado": geografia.get(accidente.get("idcalle"), {}).get("condado"),
                "hora_confirmacion": texto_fecha(hitos["hora_confirmacion"]),
                "hora_rechazo": texto_fecha(hitos["hora_rechazo"]),
                "hora_llegada": texto_fecha(llegada),
                "hora_retiro": texto_fecha(retiro),
                "segundos_respuesta": segundos_entre(momento, hitos["hora_confirmacion"]),
                "segundos_transito": segundos_entre(hitos["hora_confirmacion"] or momento, llegada),
                "segundos_atencion": segundos_entre(llegada, retiro),
                "numero_intento": min(numeros.get(d["iddespacho"], 1), 255),
                "resultado": hitos["resultado"],
                "motivo_rechazo": hitos["motivo_rechazo"],
                "retiro_forzado": 1 if d.get("retiro_forzado") else 0,
                "cargado_en": marca,
                "version": marca,
            }
        )
    return filas
