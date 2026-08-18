"""`hecho_cambio_acceso`: transacción, grano un cambio. Sin ejecutor.

`es_cambio_efectivo` descarta `Activo → Activo` y duplicados a milisegundos.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Callable, Iterable, Mapping

from lib.clickhouse_http_client import query_clickhouse
from lib.hechos.comun import FORMATO, a_datetime, texto_fecha
from lib.pinot_http_client import query_pinot

LIMITE = 50_000

#: `ejecutado_por` **no se selecciona**.
CONSULTA_BITACORA = f"""
    SELECT idhistorial, idpartner, idcredencial, tipo_cambio, motivo,
           estado_anterior, estado_nuevo, fecha_cambio
    FROM Fact_HistorialAccesoPartner
    LIMIT {LIMITE}
"""

CONSULTA_PARTNERS = "SELECT idpartner, nombre_partner FROM dim_partner FINAL"


def extraer(
    consultar_origen: Callable[[str], list[dict]] = query_pinot,
    consultar_modelo: Callable[[str], list[dict]] = query_clickhouse,
) -> dict[str, list[dict]]:
    partners: list[dict] = []
    try:
        partners = consultar_modelo(CONSULTA_PARTNERS)
    except Exception:  # noqa: BLE001
        partners = []
    return {
        "bitacora": consultar_origen(CONSULTA_BITACORA),
        "partners": partners,
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
    if not texto:
        return None
    try:
        return datetime.strptime(texto[:19], FORMATO)
    except ValueError:
        return None


def _norm(valor: Any) -> str:
    return str(valor or "").strip().lower()


def es_cambio_efectivo(anterior: Any, nuevo: Any) -> int:
    a, n = _norm(anterior), _norm(nuevo)
    if not a or not n:
        return 1
    return 0 if a == n else 1


def construir(
    datos: Mapping[str, Iterable[Mapping[str, Any]]], ahora: datetime
) -> list[dict]:
    cargado = ahora.strftime(FORMATO)
    partners = {
        int(p["idpartner"]): p.get("nombre_partner") or ""
        for p in datos.get("partners", [])
        if p.get("idpartner") is not None
    }
    vistos: set[tuple] = set()
    filas = []
    ordenados = sorted(
        datos.get("bitacora", []),
        key=lambda b: (_momento(b.get("fecha_cambio")) or datetime.min, int(b.get("idhistorial") or 0)),
    )
    for b in ordenados:
        cuando = _momento(b.get("fecha_cambio"))
        if cuando is None:
            continue
        pid = int(b["idpartner"])
        tipo = str(b.get("tipo_cambio") or "")
        clave = (pid, tipo, cuando.replace(microsecond=0), _norm(b.get("estado_anterior")), _norm(b.get("estado_nuevo")))
        duplicado = clave in vistos
        vistos.add(clave)
        efectivo = 0 if duplicado else es_cambio_efectivo(b.get("estado_anterior"), b.get("estado_nuevo"))
        cid = b.get("idcredencial")
        try:
            cid_i = int(cid) if cid not in (None, "", -1) else None
        except (TypeError, ValueError):
            cid_i = None
        motivo = str(b["motivo"]).strip() if b.get("motivo") else None
        if motivo == "":
            motivo = None
        filas.append({
            "idhistorial": int(b["idhistorial"]),
            "fecha": cuando.date().isoformat(),
            "fechahora": texto_fecha(cuando),
            "idpartner": pid,
            "partner": partners.get(pid, ""),
            "idcredencial": cid_i,
            "tipo_cambio": tipo,
            "estado_anterior": (str(b["estado_anterior"]).strip() or None) if b.get("estado_anterior") else None,
            "estado_nuevo": (str(b["estado_nuevo"]).strip() or None) if b.get("estado_nuevo") else None,
            "es_cambio_efectivo": efectivo,
            "motivo": motivo,
            "cargado_en": cargado,
        })
    return filas
