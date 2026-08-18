"""`dim_cliente`: dimensión **conformada**, sin dato fiscal ni medio de cobro.

Se crea aquí porque Suscripciones es el primer departamento que la necesita.
Cuentas y Clientes **la amplía, no la recrea**: cohorte, baja, etapa derivada
de las filas de onboarding —nunca de `estado_onboarding` del origen, nula en
un cliente activo—.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Callable, Iterable, Mapping

from lib.dimensiones.dim_etapa_onboarding import OBLIGATORIAS, orden_de
from lib.hechos.comun import a_datetime, texto_fecha
from lib.pinot_http_client import query_pinot

LIMITE = 50_000

#: Sin `nit_identificacion`, sin `admin_local_id`, sin contacto.
CONSULTA_CLIENTES = f"""
    SELECT idcliente, razon_social, nombre, tipo, estado, estado_onboarding,
           fecha_inicio_contrato, fecha_actualizacion
    FROM Dim_Cliente
    LIMIT {LIMITE}
"""

#: Solo las columnas que el informe de ausencia necesita. El token y los
#: últimos dígitos **no se piden**: si no viajan, no pueden colarse.
CONSULTA_METODOS = f"""
    SELECT idcliente, fechaexpiracion, activo
    FROM Dim_MetodoPago
    LIMIT {LIMITE}
"""

CONSULTA_ONBOARDING = f"""
    SELECT id_cliente, etapa, completado, fecha_completado, fecha_actualizacion
    FROM Fact_Onboarding
    LIMIT {LIMITE}
"""

ESTADO_BAJA = "dado de baja"
ESTADOS_APROBADA = frozenset({"activo", "dado de baja"})
ESTADOS_RECHAZADA = frozenset({"rechazado"})


def extraer(consultar: Callable[[str], list[dict]] = query_pinot) -> dict[str, list[dict]]:
    return {
        "clientes": consultar(CONSULTA_CLIENTES),
        "metodos": consultar(CONSULTA_METODOS),
        "onboarding": consultar(CONSULTA_ONBOARDING),
    }


def _es_activo(valor: Any) -> bool:
    return valor in (True, 1, "true", "1", "True")


def _norm(valor: Any) -> str:
    return str(valor or "").strip().lower().replace("_", " ")


def _resultado_solicitud(estado: Any) -> str | None:
    clave = _norm(estado)
    if clave in ESTADOS_APROBADA:
        return "aprobada"
    if clave in ESTADOS_RECHAZADA:
        return "rechazada"
    return None


def _etapas_por_cliente(
    filas: Iterable[Mapping[str, Any]],
) -> dict[int, list[str]]:
    por: dict[int, list[str]] = {}
    for f in filas:
        if not _es_activo(f.get("completado")):
            continue
        cid = f.get("id_cliente") if f.get("id_cliente") is not None else f.get("idcliente")
        etapa = f.get("etapa")
        if cid is None or not etapa:
            continue
        por.setdefault(int(cid), []).append(str(etapa).strip())
    return por


def _etapa_actual(completadas: list[str]) -> str | None:
    if not completadas:
        return None
    return max(completadas, key=lambda e: orden_de(e) or 0)


def construir(
    datos: Mapping[str, Iterable[Mapping[str, Any]]], ahora: datetime
) -> list[dict]:
    version = ahora.strftime("%Y-%m-%d %H:%M:%S")
    caduca_por_cliente: dict[int, datetime] = {}
    con_metodo: set[int] = set()
    for m in datos.get("metodos", []):
        if not _es_activo(m.get("activo")):
            continue
        cid = m.get("idcliente")
        if cid is None:
            continue
        cid = int(cid)
        con_metodo.add(cid)
        exp = a_datetime(m.get("fechaexpiracion"))
        if exp is None:
            continue
        previo = caduca_por_cliente.get(cid)
        if previo is None or exp > previo:
            caduca_por_cliente[cid] = exp

    etapas = _etapas_por_cliente(datos.get("onboarding", []))

    filas = []
    for c in datos.get("clientes", []):
        cid = int(c["idcliente"])
        nombre = (c.get("razon_social") or c.get("nombre") or "").strip()
        alta = a_datetime(c.get("fecha_inicio_contrato"))
        caduca = caduca_por_cliente.get(cid)
        estado = c.get("estado") or None
        es_baja = _norm(estado) == ESTADO_BAJA
        actualizacion = a_datetime(c.get("fecha_actualizacion"))
        completadas = etapas.get(cid, [])
        filas.append({
            "idcliente": cid,
            "nombre_comercial": nombre,
            "tipo": c.get("tipo") or None,
            "estado_comercial": estado,
            "estado_onboarding": c.get("estado_onboarding") or None,
            "tiene_metodo_pago": 1 if cid in con_metodo else 0,
            "metodo_pago_caduca": caduca.date().isoformat() if caduca else None,
            "fecha_alta": texto_fecha(alta),
            "cohorte_alta": alta.strftime("%Y-%m") if alta else None,
            "fecha_baja": texto_fecha(actualizacion) if es_baja else None,
            "motivo_baja": None,
            "etapa_onboarding_actual": _etapa_actual(completadas),
            "onboarding_completo": 1 if OBLIGATORIAS <= set(completadas) else 0,
            "resultado_solicitud": _resultado_solicitud(estado),
            "version": version,
        })
    return filas
