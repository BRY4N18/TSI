"""`hecho_onboarding`: transacción, grano **una etapa completada**.

⚠️ **El abandono ya se puede medir** (decision #45). El origen solo publicaba
etapas completadas, asi que un embudo sobre lo observado daba 100 % de
finalizacion. Desde el 2026-08-23 declara las obligatorias al aprobar la cuenta
con `completado = False`, y aqui se copian **las dos**: una etapa que llego y
sigue sin completar **es** el abandono observado, sin umbral inventado.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Callable, Iterable, Mapping

from lib.clickhouse_http_client import query_clickhouse
from lib.dimensiones.dim_etapa_onboarding import orden_de
from lib.hechos.comun import FORMATO, a_datetime, texto_fecha
from lib.pinot_http_client import query_pinot

LIMITE = 50_000

CONSULTA_ONBOARDING = f"""
    SELECT id_onboarding, id_cliente, etapa, completado,
           fecha_completado, fecha_actualizacion
    FROM Fact_Onboarding
    LIMIT {LIMITE}
"""

CONSULTA_CLIENTES = "SELECT idcliente, tipo, fecha_alta FROM dim_cliente FINAL"


def extraer(
    consultar_origen: Callable[[str], list[dict]] = query_pinot,
    consultar_modelo: Callable[[str], list[dict]] = query_clickhouse,
) -> dict[str, list[dict]]:
    clientes: list[dict] = []
    try:
        clientes = consultar_modelo(CONSULTA_CLIENTES)
    except Exception:  # noqa: BLE001
        clientes = []
    return {
        "onboarding": consultar_origen(CONSULTA_ONBOARDING),
        "clientes": clientes,
    }


def _es_completado(valor: Any) -> bool:
    return valor in (True, 1, "true", "1", "True")


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


def construir(
    datos: Mapping[str, Iterable[Mapping[str, Any]]], ahora: datetime
) -> list[dict]:
    cargado = ahora.strftime("%Y-%m-%d %H:%M:%S")
    clientes = {int(c["idcliente"]): c for c in datos.get("clientes", [])}
    filas = []
    for f in datos.get("onboarding", []):
        completada = _es_completado(f.get("completado"))
        cid = f.get("id_cliente")
        etapa = f.get("etapa")
        if cid is None or not etapa:
            continue
        cid = int(cid)
        # Completada: cuando se completo. Pendiente: cuando se declaro, que es
        # el momento en que el cliente **llego** a esa etapa.
        cuando = _momento(f.get("fecha_completado")) or _momento(f.get("fecha_actualizacion"))
        if cuando is None:
            continue
        cliente = clientes.get(cid, {})
        alta = _momento(cliente.get("fecha_alta"))
        dias = (cuando.date() - alta.date()).days if alta is not None else None
        oid = f.get("id_onboarding") or f.get("idonboarding") or 0
        filas.append({
            "idonboarding": int(oid),
            "fecha": cuando.date().isoformat(),
            "fechahora": texto_fecha(cuando),
            "idcliente": cid,
            "tipo_cliente": cliente.get("tipo"),
            "idetapa": orden_de(etapa),
            "etapa": str(etapa).strip(),
            "orden_etapa": orden_de(etapa),
            "completada": 1 if completada else 0,
            # ⚠️ Ausente si no se completo: no hay «dias hasta» algo que no
            # ocurrio, y un 0 se leeria como «la hizo el mismo dia».
            "dias_desde_alta": dias if completada else None,
            "cargado_en": cargado,
        })
    return filas
