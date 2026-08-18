"""`hecho_sesion`: transacción, grano **una sesión**. Sin token.

`duracion_segundos` ausente cuando no hay cierre. Nunca cero y nunca «hasta
ahora». `desenlace` distingue cerrada, abierta y expulsada.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Callable, Iterable, Mapping

from lib.clickhouse_http_client import query_clickhouse
from lib.hechos.comun import FORMATO, a_datetime, franja_horaria, segundos_entre, texto_fecha
from lib.pinot_http_client import query_pinot

LIMITE = 200_000

#: `token` y `refresh_token` **no se seleccionan**.
CONSULTA_SESIONES = f"""
    SELECT idsession, idusuario, navegador,
           fechahorainiciosesion, fechahoracierresesion, estadosession
    FROM Fact_Session
    LIMIT {LIMITE}
"""

CONSULTA_PERTENENCIA = (
    "SELECT idusuario, idcliente, tiene_pertenencia "
    "FROM dim_usuario_organizacion FINAL"
)

ESTADO_CIERRE = {"cierre sesion", "cierre", "cerrada"}
ESTADO_EXPULSADA = {"expulsado", "expulsada"}


def extraer(
    consultar_origen: Callable[[str], list[dict]] = query_pinot,
    consultar_modelo: Callable[[str], list[dict]] = query_clickhouse,
) -> dict[str, list[dict]]:
    pertenencia: list[dict] = []
    try:
        pertenencia = consultar_modelo(CONSULTA_PERTENENCIA)
    except Exception:  # noqa: BLE001
        pertenencia = []
    return {
        "sesiones": consultar_origen(CONSULTA_SESIONES),
        "pertenencia": pertenencia,
    }


def _momento(valor: Any) -> datetime | None:
    if valor is None or valor == "" or valor == 0:
        return None
    if isinstance(valor, datetime):
        return valor.replace(tzinfo=None)
    if isinstance(valor, str):
        try:
            return datetime.strptime(valor[:19], FORMATO)
        except ValueError:
            return None
    if isinstance(valor, (int, float)):
        if valor <= 0:
            return None
        return a_datetime(int(valor))
    return None


def _desenlace(estado: Any) -> str:
    clave = str(estado or "").strip().lower()
    if clave in ESTADO_EXPULSADA:
        return "expulsada"
    if clave in ESTADO_CIERRE:
        return "cerrada"
    return "abierta"


def construir(
    datos: Mapping[str, Iterable[Mapping[str, Any]]], ahora: datetime
) -> list[dict]:
    cargado = ahora.strftime("%Y-%m-%d %H:%M:%S")
    org = {
        int(p["idusuario"]): p
        for p in datos.get("pertenencia", [])
        if p.get("idusuario") is not None
    }
    filas = []
    for s in datos.get("sesiones", []):
        inicio = _momento(s.get("fechahorainiciosesion"))
        if inicio is None:
            continue
        cierre = _momento(s.get("fechahoracierresesion"))
        uid = int(s["idusuario"])
        pert = org.get(uid, {})
        conocida = int(pert.get("tiene_pertenencia") or 0)
        filas.append({
            "idsesion": int(s["idsession"]),
            "fecha": inicio.date().isoformat(),
            "fechahora_inicio": texto_fecha(inicio),
            "fechahora_cierre": texto_fecha(cierre),
            "idusuario": uid,
            "idcliente": pert.get("idcliente"),
            "pertenencia_conocida": 1 if conocida else 0,
            "desenlace": _desenlace(s.get("estadosession")),
            "navegador": s.get("navegador") or None,
            "franja_horaria": franja_horaria(inicio),
            "duracion_segundos": segundos_entre(inicio, cierre),
            "cargado_en": cargado,
        })
    return filas
