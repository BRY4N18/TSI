"""`dim_credencial_api`: motivo de inactividad derivado de la bitácora.

Sin `client_secret_hash`. El año 9999 no es una fecha: es «nunca expira».
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Callable, Iterable, Mapping

from lib.hechos.comun import FORMATO, a_datetime, texto_fecha
from lib.pinot_http_client import query_pinot

LIMITE = 50_000

#: Sin hash de secreto.
CONSULTA_CREDENCIALES = f"""
    SELECT idcredencial, idpartner, idcliente, entorno, activo,
           nombre_credencial, fecha_creacion, fecha_expiracion
    FROM Dim_CredencialAPI
    LIMIT {LIMITE}
"""

CONSULTA_BITACORA = f"""
    SELECT idhistorial, idcredencial, tipo_cambio,
           estado_anterior, estado_nuevo, fecha_cambio
    FROM Fact_HistorialAccesoPartner
    LIMIT {LIMITE}
"""

NUNCA_EXPIRA_MS = 253402300799000

MOTIVO_POR_TIPO = {
    "revocacion_credencial": "revocada",
    "desactivacion_por_cascada": "cascada",
    "suspension_manual": "suspension_manual",
    "suspension_automatica": "suspension_manual",
}


def extraer(consultar: Callable[[str], list[dict]] = query_pinot) -> dict[str, list[dict]]:
    return {
        "credenciales": consultar(CONSULTA_CREDENCIALES),
        "bitacora": consultar(CONSULTA_BITACORA),
    }


def _momento(valor: Any) -> datetime | None:
    if valor is None or valor == "" or valor == 0:
        return None
    if isinstance(valor, datetime):
        dt = valor.replace(tzinfo=None)
        return None if dt.year >= 9000 else dt
    if isinstance(valor, (int, float)):
        if valor <= 0 or int(valor) >= NUNCA_EXPIRA_MS:
            return None
        dt = a_datetime(int(valor))
        if dt is None or dt.year >= 9000:
            return None
        return dt
    return None


def _es_efectivo(fila: Mapping[str, Any]) -> bool:
    ant = str(fila.get("estado_anterior") or "").strip().lower()
    nue = str(fila.get("estado_nuevo") or "").strip().lower()
    if not ant or not nue:
        return True
    return ant != nue


def _ultimo_motivo(bitacora: Iterable[Mapping[str, Any]]) -> dict[int, str]:
    por: dict[int, tuple[datetime, str]] = {}
    for b in bitacora:
        cid = b.get("idcredencial")
        tipo = b.get("tipo_cambio")
        if cid is None or cid in ("", -1) or not tipo:
            continue
        if not _es_efectivo(b):
            continue
        motivo = MOTIVO_POR_TIPO.get(str(tipo).strip())
        if motivo is None:
            continue
        cuando = _momento(b.get("fecha_cambio")) or datetime.min
        prev = por.get(int(cid))
        if prev is None or cuando >= prev[0]:
            por[int(cid)] = (cuando, motivo)
    return {k: v[1] for k, v in por.items()}


def construir(
    datos: Mapping[str, Iterable[Mapping[str, Any]]], ahora: datetime
) -> list[dict]:
    version = ahora.strftime(FORMATO)
    motivos = _ultimo_motivo(datos.get("bitacora", []))
    filas = []
    for c in datos.get("credenciales", []):
        activa = c.get("activo") in (True, 1, "true", "1", "True")
        exp = _momento(c.get("fecha_expiracion"))
        nunca = 1 if exp is None else 0
        motivo = None
        if not activa:
            motivo = motivos.get(int(c["idcredencial"]))
            if motivo is None and exp is not None and exp <= ahora:
                motivo = "expirada"
            if motivo is None:
                motivo = "expirada" if nunca == 0 else "suspension_manual"
        filas.append({
            "idcredencial": int(c["idcredencial"]),
            "idpartner": int(c["idpartner"]),
            "idcliente": int(c["idcliente"]) if c.get("idcliente") not in (None, "") else None,
            "nombre_credencial": (c.get("nombre_credencial") or "").strip(),
            "entorno": c.get("entorno") or "",
            "esta_activa": 1 if activa else 0,
            "motivo_inactividad": motivo,
            "fecha_creacion": texto_fecha(_momento(c.get("fecha_creacion"))),
            "fecha_expiracion": texto_fecha(exp),
            "nunca_expira": nunca,
            "version": version,
        })
    return filas
