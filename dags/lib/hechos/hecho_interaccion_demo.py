"""`hecho_interaccion_demo`: una fila por evento de la demo (Ventas y CRM, US3).

La fuente puede estar vacia hoy. El diagnostico es de **entorno, no de diseno**:
el repositorio publica a Kafka. Este cargador existe para cuando haya demos; con
la fuente vacia, una consulta rota y un origen vacio devuelven lo mismo, y por
eso las pruebas van con datos sinteticos.

⚠️ `metadata` no se copia: es un campo libre cuyo contenido nadie garantiza.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Callable, Iterable, Mapping

from lib.clickhouse_http_client import query_clickhouse
from lib.dimensiones.desconocido import ETIQUETA_DESCONOCIDA
from lib.hechos.comun import FORMATO, a_datetime, texto_fecha
from lib.pinot_http_client import query_pinot

LIMITE = 500_000

#: ⚠️ Sin `metadata`.
CONSULTA_DEMO = f"""
    SELECT idinteraccion, idprospecto, tipo_evento, seccion, timestamp_evento
    FROM Fact_Interaccion_Demo
    LIMIT {LIMITE}
"""

CONSULTA_DIM_PROSPECTO = (
    "SELECT idprospecto, empresa, canal FROM dim_prospecto FINAL"
)


def extraer(
    consultar_origen: Callable[[str], list[dict]] = query_pinot,
    consultar_modelo: Callable[[str], list[dict]] = query_clickhouse,
) -> dict[str, list[dict]]:
    return {
        "interacciones": consultar_origen(CONSULTA_DEMO),
        "dim_prospecto": consultar_modelo(CONSULTA_DIM_PROSPECTO),
    }


def _texto(valor: Any) -> str | None:
    if valor is None:
        return None
    texto = str(valor).strip()
    return texto or None


def construir(
    datos: Mapping[str, Iterable[Mapping[str, Any]]], ahora: datetime
) -> list[dict]:
    """Una fila por evento. Logica pura: no consulta ni escribe."""
    por_prospecto = {
        int(p["idprospecto"]): p
        for p in datos.get("dim_prospecto", [])
        if p.get("idprospecto") is not None
    }
    marca = ahora.strftime(FORMATO)
    filas: list[dict] = []

    for registro in datos.get("interacciones", []):
        momento = a_datetime(registro.get("timestamp_evento"))
        if momento is None:
            continue
        idprospecto = registro.get("idprospecto")
        dim = por_prospecto.get(int(idprospecto), {}) if idprospecto is not None else {}

        filas.append(
            {
                "idinteraccion": registro["idinteraccion"],
                "fecha": momento.date().isoformat(),
                "fechahora": texto_fecha(momento),
                "idprospecto": int(idprospecto) if idprospecto is not None else 0,
                "empresa": dim.get("empresa") or ETIQUETA_DESCONOCIDA,
                "canal": dim.get("canal") or ETIQUETA_DESCONOCIDA,
                "tipo_evento": _texto(registro.get("tipo_evento")) or ETIQUETA_DESCONOCIDA,
                "seccion": _texto(registro.get("seccion")),
                "cargado_en": marca,
            }
        )

    return filas
