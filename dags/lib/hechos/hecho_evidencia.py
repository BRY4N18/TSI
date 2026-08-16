"""`hecho_evidencia`: hecho de transacción, **grano una evidencia capturada**.

Fotos y notas en la misma tabla
-------------------------------
Comparten grano, dimensiones y preguntas. Separarlas obligaría a unir dos hechos
para responder «cobertura de foto **y** nota», que es justamente el informe #17.

Por qué un hecho y no unas métricas más del caso
-------------------------------------------------
Tiene **dos instantes propios** —capturada y sincronizada— y su grano no es el
caso: un caso puede tener varias evidencias con latencias muy distintas.
Contarlas en el caso respondería «cuántas hubo» pero nunca «cuánto tardaron».

⚠️ La unidad no viene en el origen: se deriva del despacho
-----------------------------------------------------------
Ni `Dim_EvidenciaFoto` ni `Dim_NotaAccidente` traen unidad. Traen `idusuario`, y
`idusuario` **no entra al modelo** (decisión D6). Así que la evidencia se atribuye
a la unidad que **atendió el caso**: la del primer despacho que llegó.

Es una atribución derivada, y conviene saber qué no garantiza. Si un caso tuvo
dos llegadas —una reasignación tras un retiro—, la evidencia se atribuye a la
primera, que es la que estuvo en el sitio en la inmensa mayoría de los casos,
pero no en todos.

Un caso **sin ninguna llegada** deja la evidencia en la unidad desconocida en vez
de repartirla o descartarla: la evidencia existió y el informe de cobertura tiene
que verla. Descartarla sería la peor salida — bajaría el volumen de evidencia sin
que nada indicara que faltan filas.

Y la versión de la unidad se resuelve **al instante de la captura**, no la
vigente hoy: es la misma atribución histórica que usan `hecho_despacho` y
`hecho_estado_unidad`.

⚠️ Las notas no tienen instante de sincronización, y no se inventa
------------------------------------------------------------------
`Dim_EvidenciaFoto` trae `fecha_sincronizacion`; `Dim_NotaAccidente` **no tiene
esa columna en absoluto**. Su latencia es genuinamente desconocida, así que va
ausente — ni cero, que diría que fue instantánea, ni la fecha de carga, que
diría que tardó justo lo que llevamos mirándola.

Lo mismo vale para lo aún no sincronizado: `fechahora_sincronia` ausente
significa **«todavía no»**, no «sincronizada en la época cero». Esas evidencias
cuentan en `pendientes` y su latencia es ausente, nunca infinita.

⚠️ `sincronizado = true` sin fecha no es contradictorio, es lo normal
---------------------------------------------------------------------
Las tres fotos del origen vienen con `sincronizado = true` y
`fecha_sincronizacion = null`. El indicador dice que llegó; la fecha, cuándo. Que
falte la segunda no desmiente la primera: solo impide medir la latencia. Por eso
`fechahora_sincronia` sale de la **fecha** y no del indicador — usar el indicador
para rellenar un instante sería fabricar el dato que falta.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Callable, Iterable, Mapping

from lib.clickhouse_http_client import query_clickhouse
from lib.dimensiones.desconocido import ETIQUETA_DESCONOCIDA, ID_DESCONOCIDO, SK_DESCONOCIDO
from lib.hechos.atribucion import resolver_unidad_historica, versiones_por_unidad
from lib.hechos.comun import FORMATO, a_datetime, agrupar_por, indexar_por, texto_fecha

LIMITE = 500_000

TIPO_FOTO = "foto"
TIPO_NOTA = "nota"

#: ⚠️ Sin `idusuario` y sin `urlevidenciafoto`. El primero es identidad de
#: persona; el segundo, un enlace al material, que no es una métrica y sí es una
#: forma de sacar contenido del sistema por un informe.
CONSULTA_FOTOS = f"""
    SELECT idevidenciafoto, idaccidente, fechahora, fecha_sincronizacion
    FROM Dim_EvidenciaFoto
    WHERE activo = true
    LIMIT {LIMITE}
"""

#: ⚠️ Sin `nota`: es el texto de la nota, dato interno (FR-016). `tipo` sí entra:
#: es una categoría de un conjunto cerrado —«Condiciones del sitio» y
#: similares—, no texto libre, y es lo que permite saber **qué** se documenta.
CONSULTA_NOTAS = f"""
    SELECT idnotaaccidentes, idaccidente, fechahora, tipo
    FROM Dim_NotaAccidente
    WHERE activo = true
    LIMIT {LIMITE}
"""

#: El despacho que **llegó** es lo que ata una evidencia a una unidad.
#:
#: Se usa la llegada y no la confirmación por dos razones. La primera es que
#: `Fact_Despacho` no guarda la hora de confirmación —vive en el historial de
#: estados—, así que usarla exigiría traer una tabla más. La segunda es mejor: la
#: unidad que **estuvo en el sitio** es la que capturó la evidencia, y confirmar
#: un despacho no es haber ido.
CONSULTA_DESPACHOS = f"""
    SELECT idaccidente, idunidademergencia, fechahorallegada
    FROM Fact_Despacho
    LIMIT {LIMITE}
"""

CONSULTA_DIM_UNIDAD = "SELECT * FROM dim_unidad FINAL"

#: Del modelo, no del origen: la copia debe salir de la dimensión, que es lo que
#: impide que copia y dimensión diverjan.
CONSULTA_HECHO_ACCIDENTE = """
    SELECT idaccidente, idseveridad, severidad, condado
    FROM hecho_accidente FINAL
"""


def extraer(
    consultar_origen: Callable[[str], list[dict]] = None,
    consultar_modelo: Callable[[str], list[dict]] = query_clickhouse,
) -> dict[str, list[dict]]:
    if consultar_origen is None:
        from lib.pinot_http_client import query_pinot

        consultar_origen = query_pinot
    return {
        "fotos": consultar_origen(CONSULTA_FOTOS),
        "notas": consultar_origen(CONSULTA_NOTAS),
        "despachos": consultar_origen(CONSULTA_DESPACHOS),
        "dim_unidad": consultar_modelo(CONSULTA_DIM_UNIDAD),
        "hecho_accidente": consultar_modelo(CONSULTA_HECHO_ACCIDENTE),
    }


def _unidad_que_atendio(despachos: Iterable[Mapping[str, Any]]) -> int | None:
    """La unidad del **primer** despacho que llegó al caso.

    La primera y no la última: es la que estuvo en el sitio mientras se capturaba
    la evidencia. Un caso puede tener varias llegadas —una reasignación tras un
    retiro— y en ese supuesto la atribución es aproximada; se documenta en vez de
    disimularse, porque es el límite conocido de esta derivación.

    Un despacho **sin llegada** no atendió nada: rechazado, vencido o abortado.
    Tomarlo como atribución colgaría la evidencia de una unidad que nunca fue.
    """
    llegadas = [
        (a_datetime(d.get("fechahorallegada")), d.get("idunidademergencia"))
        for d in despachos
    ]
    presentes = [(m, u) for m, u in llegadas if m is not None and u is not None]
    if not presentes:
        return None
    return min(presentes, key=lambda par: par[0])[1]


def construir(datos: Mapping[str, Iterable[Mapping[str, Any]]], ahora: datetime) -> list[dict]:
    """Una fila por evidencia. Lógica pura: no consulta ni escribe."""
    versiones = versiones_por_unidad(datos.get("dim_unidad", []))
    despachos_por_caso = agrupar_por(datos.get("despachos", []), "idaccidente")
    casos = indexar_por(datos.get("hecho_accidente", []), "idaccidente")
    marca = ahora.strftime(FORMATO)

    filas: list[dict] = []

    def agregar(idevidencia, idaccidente, tipo, captura, sincronia, categoria):
        momento = a_datetime(captura)
        if momento is None:
            # Sin instante de captura no hay partición posible. Es la única razón
            # por la que una evidencia no entra al modelo.
            return

        idunidad = _unidad_que_atendio(despachos_por_caso.get(idaccidente, []))
        version = resolver_unidad_historica(versiones, idunidad, momento)
        caso = casos.get(idaccidente, {})

        instante_sincronia = a_datetime(sincronia)
        filas.append(
            {
                "idevidencia": idevidencia,
                "tipo": tipo,
                "fecha": momento.date().isoformat(),
                "fechahora_captura": texto_fecha(momento),
                # Ausente = aún no sincronizada. Nunca la época cero.
                "fechahora_sincronia": texto_fecha(instante_sincronia),
                "idaccidente": idaccidente,
                "sk_unidad": version["sk_unidad"] if version else SK_DESCONOCIDO,
                "idunidademergencia": idunidad if idunidad is not None else ID_DESCONOCIDO,
                "proveedor": (version or {}).get("proveedor") or ETIQUETA_DESCONOCIDA,
                "idseveridad": caso.get("idseveridad"),
                "severidad": caso.get("severidad"),
                "condado": caso.get("condado"),
                # Ausente mientras no haya sincronizado: la latencia de lo que no
                # ha llegado no es cero ni infinita, es desconocida.
                "segundos_hasta_sincronia": (
                    int((instante_sincronia - momento).total_seconds())
                    if instante_sincronia is not None
                    else None
                ),
                "categoria_nota": categoria,
                "cargado_en": marca,
            }
        )

    for foto in datos.get("fotos", []):
        agregar(
            foto["idevidenciafoto"],
            foto.get("idaccidente"),
            TIPO_FOTO,
            foto.get("fechahora"),
            foto.get("fecha_sincronizacion"),
            # Una foto no tiene categoría de nota. Ausente, no cadena vacía: no
            # es que su categoría esté en blanco, es que no le corresponde una.
            None,
        )

    for nota in datos.get("notas", []):
        agregar(
            nota["idnotaaccidentes"],
            nota.get("idaccidente"),
            TIPO_NOTA,
            nota.get("fechahora"),
            # ⚠️ El origen de las notas **no tiene** columna de sincronización.
            None,
            nota.get("tipo"),
        )

    return filas
