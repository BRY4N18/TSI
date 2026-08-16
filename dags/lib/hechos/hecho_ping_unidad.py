"""`hecho_ping_unidad`: hecho de transacción, grano una posición reportada.

Por qué existe
--------------
Sin él, el informe de **pérdida de señal** no se puede calcular desde el modelo,
y su tabla propia no se podría retirar (fase 6). Los huecos se detectan
comparando instantes consecutivos de la misma unidad, y eso exige tener los
instantes.

Sin coordenadas ⚠️
------------------
El origen trae latitud y longitud en cada posición, y **no se copian**. Es el
caso que mejor ilustra la exclusión del §5 del contrato: la pérdida de señal se
calcula con los instantes, no con las posiciones. La utilidad analítica no
requiere el dato sensible, así que el dato sensible no entra.

Dónde se calcula el hueco
-------------------------
`segundos_desde_anterior` se calcula **al cargar**, no al consultar. Es lo que
convierte «detectar huecos» en un filtro por columna en vez de una función de
ventana sobre 59 045 filas en cada consulta — y es la misma decisión que hace que
los tiempos de un caso sean restas de su propia fila.

La primera posición de cada unidad lo lleva **ausente**: no había anterior contra
la que medir, y cero significaría «llegó al instante», que es lo contrario.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Callable, Iterable, Mapping

from lib.clickhouse_http_client import query_clickhouse
from lib.dimensiones.desconocido import ETIQUETA_DESCONOCIDA, ID_DESCONOCIDO, SK_DESCONOCIDO
from lib.hechos.atribucion import resolver_unidad_historica, versiones_por_unidad
from lib.hechos.comun import FORMATO, a_datetime, agrupar_por, texto_fecha
from lib.pinot_http_client import query_pinot

LIMITE = 2_000_000

#: ⚠️ La consulta **no pide latitud ni longitud**. No es que se descarten
#: después: no se traen.
CONSULTA_PINGS = f"""
    SELECT idhistorialunidademergencia, idunidademergencia, idaccidente, fechahora
    FROM Dim_HistorialUbicacionUnidadEmergencia
    LIMIT {LIMITE}
"""

CONSULTA_DIM_UNIDAD = "SELECT * FROM dim_unidad FINAL"


def extraer(
    consultar_origen: Callable[[str], list[dict]] = query_pinot,
    consultar_modelo: Callable[[str], list[dict]] = query_clickhouse,
) -> dict[str, list[dict]]:
    return {
        "pings": consultar_origen(CONSULTA_PINGS),
        "dim_unidad": consultar_modelo(CONSULTA_DIM_UNIDAD),
    }


def construir(datos: Mapping[str, Iterable[Mapping[str, Any]]], ahora: datetime) -> list[dict]:
    """Una fila por posición reportada. Lógica pura: no consulta ni escribe."""
    versiones = versiones_por_unidad(datos["dim_unidad"])
    marca = ahora.strftime(FORMATO)

    filas = []
    for idunidad, de_la_unidad in agrupar_por(datos["pings"], "idunidademergencia").items():
        ordenados = sorted(de_la_unidad, key=lambda p: p.get("fechahora") or 0)
        anterior: datetime | None = None

        for ping in ordenados:
            momento = a_datetime(ping.get("fechahora"))
            if momento is None:
                continue

            version = resolver_unidad_historica(versiones, idunidad, momento)
            filas.append(
                {
                    "idping": ping["idhistorialunidademergencia"],
                    "fecha": momento.date().isoformat(),
                    "fechahora": texto_fecha(momento),
                    "sk_unidad": version["sk_unidad"] if version else SK_DESCONOCIDO,
                    "idunidademergencia": idunidad if idunidad is not None else ID_DESCONOCIDO,
                    "proveedor": (version or {}).get("proveedor") or ETIQUETA_DESCONOCIDA,
                    "idaccidente": ping.get("idaccidente"),
                    "segundos_desde_anterior": (
                        int((momento - anterior).total_seconds()) if anterior else None
                    ),
                    "cargado_en": marca,
                }
            )
            anterior = momento

    return filas
