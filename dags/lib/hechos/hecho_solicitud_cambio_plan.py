"""`hecho_solicitud_cambio_plan`: transacción, **grano una solicitud**.

`tipo_movimiento` sale del **delta de precio**, no del nivel: el catálogo tiene
un Empresarial más barato que un Profesional.

`segundos_resolucion` ausente mientras esté pendiente: una abierta no se resolvió
en cero segundos. Una rechazada **sí** se resolvió.

Sin `idadminaprobador` y sin `motivo_rechazo`.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Callable, Iterable, Mapping

from lib.clickhouse_http_client import query_clickhouse
from lib.dimensiones.desconocido import ETIQUETA_DESCONOCIDA, resolver_o_desconocido
from lib.hechos.comun import FORMATO, a_datetime, indexar_por, segundos_entre, texto_fecha
from lib.pinot_http_client import query_pinot

LIMITE = 100_000

CONSULTA_SOLICITUDES = f"""
    SELECT idsolicitud, idcliente, idplanactual, idplansolicitado, estado,
           fecha_solicitud, fecha_resolucion
    FROM Fact_Solicitud_Cambio_Plan
    LIMIT {LIMITE}
"""

CONSULTA_PLANES = "SELECT idplan, nombre, precio_lista FROM dim_plan FINAL"

ESTADOS_RESUELTOS = frozenset({"aprobada", "rechazada", "aplicada"})


def extraer(
    consultar_origen: Callable[[str], list[dict]] = query_pinot,
    consultar_modelo: Callable[[str], list[dict]] = query_clickhouse,
) -> dict[str, list[dict]]:
    return {
        "solicitudes": consultar_origen(CONSULTA_SOLICITUDES),
        "dim_plan": consultar_modelo(CONSULTA_PLANES),
    }


def _momento(valor: Any) -> datetime | None:
    if valor is None or valor == "" or valor == 0:
        return None
    if isinstance(valor, datetime):
        return valor.replace(tzinfo=None)
    if isinstance(valor, (int, float)):
        if valor <= 0:
            return None
        return a_datetime(int(valor))
    texto = str(valor).strip()
    if not texto or texto.startswith("1970-01-01"):
        return None
    try:
        return datetime.fromisoformat(texto.replace("Z", "").split(".")[0])
    except ValueError:
        return None


def _precio(plan: Mapping[str, Any]) -> float:
    try:
        return float(plan.get("precio_lista") or 0)
    except (TypeError, ValueError):
        return 0.0


def tipo_movimiento(delta: float) -> str:
    if delta > 0:
        return "upgrade"
    if delta < 0:
        return "downgrade"
    return "lateral"


def construir(
    datos: Mapping[str, Iterable[Mapping[str, Any]]], ahora: datetime
) -> list[dict]:
    planes = indexar_por(
        ({**p, "idplan": int(p["idplan"])} for p in datos.get("dim_plan", [])),
        "idplan",
    )
    cargado = ahora.strftime(FORMATO)
    filas = []
    for s in datos.get("solicitudes", []):
        id_actual = int(resolver_o_desconocido(s.get("idplanactual"), planes))
        id_nuevo = int(resolver_o_desconocido(s.get("idplansolicitado"), planes))
        actual = planes.get(id_actual, {})
        nuevo = planes.get(id_nuevo, {})
        delta = round(_precio(nuevo) - _precio(actual), 2)
        estado = str(s.get("estado") or "Pendiente").strip().lower()
        solicitud = _momento(s.get("fecha_solicitud")) or ahora
        resolucion = _momento(s.get("fecha_resolucion"))
        resuelta = 1 if estado in ESTADOS_RESUELTOS else 0
        filas.append({
            "idsolicitud": int(s["idsolicitud"]),
            "fecha": solicitud.date().isoformat(),
            "fecha_solicitud": texto_fecha(solicitud),
            "fecha_resolucion": texto_fecha(resolucion),
            "idcliente": int(s.get("idcliente") or 0),
            "idplan_actual": id_actual,
            "plan_actual": actual.get("nombre") or ETIQUETA_DESCONOCIDA,
            "idplan_solicitado": id_nuevo,
            "plan_solicitado": nuevo.get("nombre") or ETIQUETA_DESCONOCIDA,
            "tipo_movimiento": tipo_movimiento(delta),
            "delta_precio": delta,
            "estado": estado,
            "esta_resuelta": resuelta,
            "segundos_resolucion": (
                segundos_entre(solicitud, resolucion) if resuelta else None
            ),
            "cargado_en": cargado,
        })
    return filas
