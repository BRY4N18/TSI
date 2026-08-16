"""`hecho_estado_unidad`: hecho de **transacción**, grano un cambio de estado.

Para qué está aquí
------------------
Es el tercer hecho del modelo, y su función es **ejercitar el crecimiento**, no
solo documentarlo: si añadir un hecho exigiera tocar los dos existentes, la
promesa de que el modelo crece sin rehacer lo construido sería una afirmación sin
comprobar (US3).

Además es el primero que **no** es una instantánea acumulada, así que ejercita el
otro camino: motor sin deduplicación, sin necesidad de forzar versión final al
consultar, e idempotencia por descarte de partición.

Dos trampas del origen, ya vistas antes ⚠️
-------------------------------------------
`Fact_HistorialEstadoUnidad` repite lo que la bitácora de partners:

1. **Filas donde el estado no cambió** (`Activa → Activa`). Se registró una
   escritura, no una transición. Contarlas como cambios inflaría cualquier
   métrica de rotación de flota. Aquí **no se descartan** —el registro existió y
   perderlo sería otra clase de mentira— sino que se marcan con
   `es_cambio_efectivo = 0`, y quien pregunte por cambios reales filtra.
2. **`estadonuevo` puede venir nulo.** Se conserva ausente, no se rellena con el
   estado anterior ni con una etiqueta inventada.

Reutiliza la atribución histórica
---------------------------------
`sk_unidad` y `proveedor` salen de la **versión vigente en el momento del
cambio**, con la misma función que usa `hecho_despacho`. Es la prueba de que el
mecanismo de US2 sirve a más de un hecho sin duplicarse.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Callable, Iterable, Mapping

from lib.clickhouse_http_client import query_clickhouse
from lib.dimensiones.desconocido import ETIQUETA_DESCONOCIDA, ID_DESCONOCIDO, SK_DESCONOCIDO
from lib.hechos.atribucion import resolver_unidad_historica, versiones_por_unidad
from lib.hechos.comun import FORMATO, a_datetime, agrupar_por, texto_fecha
from lib.pinot_http_client import query_pinot

LIMITE = 500_000

CONSULTA_HISTORIAL = f"""
    SELECT idhistorialestadosunidadesemergencias, idunidademergencia,
           idestadounidademergencia, estadoanterior, estadonuevo, fechahora
    FROM Fact_HistorialEstadoUnidad
    LIMIT {LIMITE}
"""

CONSULTA_DIM_UNIDAD = "SELECT * FROM dim_unidad FINAL"


def extraer(
    consultar_origen: Callable[[str], list[dict]] = query_pinot,
    consultar_modelo: Callable[[str], list[dict]] = query_clickhouse,
) -> dict[str, list[dict]]:
    return {
        "historial": consultar_origen(CONSULTA_HISTORIAL),
        "dim_unidad": consultar_modelo(CONSULTA_DIM_UNIDAD),
    }


def construir(datos: Mapping[str, Iterable[Mapping[str, Any]]], ahora: datetime) -> list[dict]:
    """Una fila por cambio registrado. Lógica pura: no consulta ni escribe."""
    versiones = versiones_por_unidad(datos["dim_unidad"])
    marca = ahora.strftime(FORMATO)

    filas = []
    for _, de_la_unidad in agrupar_por(datos["historial"], "idunidademergencia").items():
        ordenados = sorted(de_la_unidad, key=lambda h: h.get("fechahora") or 0)
        anterior: datetime | None = None

        for registro in ordenados:
            momento = a_datetime(registro.get("fechahora"))
            if momento is None:
                continue

            idunidad = registro.get("idunidademergencia")
            version = resolver_unidad_historica(versiones, idunidad, momento)
            estado_nuevo = registro.get("estadonuevo")
            estado_anterior = registro.get("estadoanterior")

            filas.append(
                {
                    "idhistorial": registro["idhistorialestadosunidadesemergencias"],
                    "fecha": momento.date().isoformat(),
                    "fechahora": texto_fecha(momento),
                    "sk_unidad": version["sk_unidad"] if version else SK_DESCONOCIDO,
                    "idunidademergencia": idunidad if idunidad is not None else ID_DESCONOCIDO,
                    "unidad": (version or {}).get("placa") or ETIQUETA_DESCONOCIDA,
                    "proveedor": (version or {}).get("proveedor") or ETIQUETA_DESCONOCIDA,
                    "idestadounidademergencia": registro.get("idestadounidademergencia"),
                    "estado_nuevo": estado_nuevo,
                    "estado_anterior": estado_anterior,
                    # El registro se conserva aunque no haya cambiado nada; la
                    # marca permite contar transiciones reales sin perderlo.
                    "es_cambio_efectivo": 0 if estado_nuevo == estado_anterior else 1,
                    # Ausente en el primer registro de cada unidad: no se sabe
                    # cuánto llevaba en ese estado, y cero sería falso.
                    "segundos_en_estado_anterior": (
                        int((momento - anterior).total_seconds()) if anterior else None
                    ),
                    "cargado_en": marca,
                }
            )
            anterior = momento

    return filas
