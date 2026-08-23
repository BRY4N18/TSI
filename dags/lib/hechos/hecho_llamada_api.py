"""`hecho_llamada_api`: transacción, grano **una llamada**. Sin IP.

⚠️ NO se carga `Fact_APIIntegracion`. Difiere del detalle en un orden de
magnitud (500 llamadas vs 18 registros) y haría imposibles p95, consumo por
endpoint y taxonomía de errores: esa información se perdió al agregar.
Tenerla al lado en el modelo sería una invitación a usarla el día que el
detalle diera un número incómodo.
"""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any, Callable, Iterable, Mapping
from urllib.parse import urlparse

from lib.clickhouse_http_client import query_clickhouse
from lib.hechos.comun import FORMATO, a_datetime, texto_fecha
from lib.pinot_http_client import query_pinot

LIMITE = 500_000

#: `iporigen` **no se selecciona**.
CONSULTA_LLAMADAS = f"""
    SELECT idlogllamadaapi, idpartner, idcredencialapi, endpoint,
           metodohttp, codigohttp, latenciams, fechallamada, version_contrato
    FROM Fact_LogLlamadaAPI
    LIMIT {LIMITE}
"""

CONSULTA_PARTNERS = (
    "SELECT idpartner, nombre_partner, idcliente, plan_api FROM dim_partner FINAL"
)

CONSULTA_CREDENCIALES = (
    "SELECT idcredencial, entorno FROM dim_credencial_api FINAL"
)

PATH_API = re.compile(r"^/api/(v[0-9]+)/([^/?]+)", re.IGNORECASE)


def extraer(
    consultar_origen: Callable[[str], list[dict]] = query_pinot,
    consultar_modelo: Callable[[str], list[dict]] = query_clickhouse,
) -> dict[str, list[dict]]:
    partners: list[dict] = []
    credenciales: list[dict] = []
    try:
        partners = consultar_modelo(CONSULTA_PARTNERS)
    except Exception:  # noqa: BLE001
        partners = []
    try:
        credenciales = consultar_modelo(CONSULTA_CREDENCIALES)
    except Exception:  # noqa: BLE001
        credenciales = []
    return {
        "llamadas": consultar_origen(CONSULTA_LLAMADAS),
        "partners": partners,
        "credenciales": credenciales,
    }


def normalizar_path(endpoint: Any) -> str:
    """Path sin cadena de consulta. Agrupar por la URL completa fragmentaría el consumo."""
    texto = str(endpoint or "").strip()
    if not texto:
        return ""
    if "://" in texto:
        texto = urlparse(texto).path or texto
    return texto.split("?", 1)[0] or texto


def derivar_contrato(path: str) -> tuple[str | None, str | None]:
    m = PATH_API.match(path)
    if not m:
        return None, None
    return m.group(2), m.group(1).lower()


PREFIJO_DECLARADA = "declarada:"


def _texto(valor):
    """`None` ante ausencia y ante los centinelas de Pinot para STRING."""
    if valor is None:
        return None
    texto = str(valor).strip()
    return None if texto in ("", "null") else texto


def clase_resultado(codigo: int) -> str:
    """429 es cupo, 403 autorización, 5xx fallo del servicio. No se mezclan."""
    if codigo == 429:
        return "limite_cupo"
    if codigo in (401, 403):
        return "autorizacion"
    if codigo >= 500:
        return "error_servicio"
    if 200 <= codigo < 400:
        return "exito"
    return "error_cliente"


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
        try:
            return datetime.fromisoformat(texto.replace("Z", "").split(".")[0])
        except ValueError:
            return None


def construir(
    datos: Mapping[str, Iterable[Mapping[str, Any]]], ahora: datetime
) -> list[dict]:
    cargado = ahora.strftime(FORMATO)
    partners = {int(p["idpartner"]): p for p in datos.get("partners", []) if p.get("idpartner") is not None}
    creds = {
        int(c["idcredencial"]): c
        for c in datos.get("credenciales", [])
        if c.get("idcredencial") is not None
    }
    filas = []
    for l in datos.get("llamadas", []):
        cuando = _momento(l.get("fechallamada"))
        if cuando is None:
            continue
        pid = int(l["idpartner"])
        pert = partners.get(pid, {})
        cid = l.get("idcredencialapi") if l.get("idcredencialapi") is not None else l.get("idcredencial")
        try:
            cid_i = int(cid) if cid not in (None, "", -1) else None
        except (TypeError, ValueError):
            cid_i = None
        cred = creds.get(cid_i, {}) if cid_i is not None else {}
        path = normalizar_path(l.get("endpoint"))
        servicio, version_del_path = derivar_contrato(path)
        # ⚠️ **Se prefiere la que el origen guardo** (#46). Desde el 2026-08-23
        # el middleware la resuelve en el instante de la llamada y la escribe en
        # `Fact_LogLlamadaAPI.version_contrato`, asi que esas filas conservan la
        # version que era cierta entonces. Las anteriores no la traen y se
        # siguen deduciendo del path, con la marca puesta: el riesgo declarado
        # —que un cambio de forma del path reinterprete llamadas viejas sin
        # fallar— solo desaparece para las nuevas.
        guardada = _texto(l.get("version_contrato"))
        # ⚠️ **Declarada y guardada no son lo mismo.** El origen guarda siempre
        # una version —asi la fila conserva la que era cierta cuando ocurrio la
        # llamada, aunque el path cambie de forma despues— pero solo lleva el
        # prefijo `declarada:` cuando el **partner** la mando por cabecera. Esa
        # es la unica que no es una lectura del path.
        declarada = None
        if guardada and guardada.startswith(PREFIJO_DECLARADA):
            declarada = guardada[len(PREFIJO_DECLARADA):] or None
            guardada = declarada
        version = guardada or version_del_path
        try:
            codigo = int(l.get("codigohttp") or 0)
        except (TypeError, ValueError):
            codigo = 0
        try:
            latencia = int(float(l.get("latenciams") or 0))
        except (TypeError, ValueError):
            latencia = 0
        filas.append({
            "idlog": int(l.get("idlogllamadaapi") or l.get("idlog") or 0),
            "fecha": cuando.date().isoformat(),
            "fechahora": texto_fecha(cuando),
            "idpartner": pid,
            "partner": pert.get("nombre_partner") or "",
            "idcliente": pert.get("idcliente"),
            "plan_api": pert.get("plan_api"),
            "idcredencial": cid_i,
            "entorno": cred.get("entorno"),
            "endpoint_path": path,
            "metodo_http": str(l.get("metodohttp") or "GET"),
            "codigo_http": codigo,
            "clase_resultado": clase_resultado(codigo),
            "latencia_ms": latencia,
            "servicio": servicio,
            "version_contrato": version,
            "version_es_derivada": 0 if declarada else 1,
            "cargado_en": cargado,
        })
    return filas
