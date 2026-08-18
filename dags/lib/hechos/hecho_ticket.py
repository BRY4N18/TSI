"""`hecho_ticket`: instantánea acumulada, **grano un ticket**.

Los límites de SLA se copian de la vigencia **al crearse**, no de la actual.
Los ceros de tiempo del origen se traducen a ausencia: un promedio que los
incluyera mejoraría cuantos más tickets sin atender hubiera.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Callable, Iterable, Mapping

from lib.clickhouse_http_client import query_clickhouse
from lib.hechos.comun import FORMATO, a_datetime, agrupar_por, segundos_entre, texto_fecha
from lib.hechos.sla_vigente import sla_vigente_en
from lib.pinot_http_client import query_pinot

LIMITE = 100_000

ESTADO_PENDIENTE = "Pendiente_de_clasificacion"
SLA_SIN_COMPROMISO = "sin compromiso"
MOTIVO_PENDIENTE = "pendiente_clasificar"
MOTIVO_SIN_COMPROMISO = "sin_compromiso"
MOTIVO_SIN_CONFIG = "sin_config"

ACCIONES_PRIMERA_RESPUESTA = frozenset({"asignacion_agente", "comentario"})
ACCIONES_RESOLUCION = frozenset({"resolucion"})
ACCIONES_CIERRE = frozenset({"cierre_confirmado", "cierre_automatico_por_vencimiento"})

#: Columnas del ticket. **Sin asunto ni descripcion.**
CONSULTA_TICKETS = f"""
    SELECT id_reclamo, idcliente, idestadosoporte, idservicio, idslaconfig,
           tipo, prioridad, id_agente_asignado, tipo_incidencia, sla_status,
           estado, sla_primera_respuesta, sla_resolucion, tiempo_solucion,
           fechahora, fechahoraconfirmacioncierre
    FROM Fact_Reclamo
    LIMIT {LIMITE}
"""

#: Historial **sin** mensaje ni es_nota_interna.
CONSULTA_HISTORIAL = f"""
    SELECT id_historial, id_reclamo, tipo_accion, idusuario,
           estado_anterior, estado_nuevo, fecha_accion
    FROM Fact_Historial_Ticket
    LIMIT {LIMITE}
"""

CONSULTA_SLA = "SELECT * FROM dim_sla_config FINAL"
CONSULTA_PLANES = "SELECT idplan, nombre FROM dim_plan FINAL"
CONSULTA_SERVICIOS = "SELECT id_servicio, nombre FROM dim_servicio FINAL"
CONSULTA_CLIENTES = "SELECT idcliente, tipo FROM dim_cliente FINAL"
CONSULTA_SUSCRIPCIONES = f"""
    SELECT idcliente, idplan
    FROM Fact_Suscripcion
    LIMIT {LIMITE}
"""


def extraer(
    consultar_origen: Callable[[str], list[dict]] = query_pinot,
    consultar_modelo: Callable[[str], list[dict]] = query_clickhouse,
) -> dict[str, list[dict]]:
    return {
        "tickets": consultar_origen(CONSULTA_TICKETS),
        "historial": consultar_origen(CONSULTA_HISTORIAL),
        "suscripciones": consultar_origen(CONSULTA_SUSCRIPCIONES),
        "dim_sla_config": _modelo_o_vacio(consultar_modelo, CONSULTA_SLA),
        "dim_plan": _modelo_o_vacio(consultar_modelo, CONSULTA_PLANES),
        "dim_servicio": _modelo_o_vacio(consultar_modelo, CONSULTA_SERVICIOS),
        "dim_cliente": _modelo_o_vacio(consultar_modelo, CONSULTA_CLIENTES),
    }


def _modelo_o_vacio(consultar, sql: str) -> list[dict]:
    try:
        return consultar(sql)
    except Exception:  # noqa: BLE001 — primera carga, la tabla puede no existir
        return []


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


def _entero(valor: Any) -> int | None:
    if valor is None or valor == "":
        return None
    try:
        n = int(valor)
    except (TypeError, ValueError):
        return None
    return n


def _hito(acciones: list[Mapping[str, Any]], tipos: frozenset[str]) -> datetime | None:
    momentos = []
    for a in acciones:
        if (a.get("tipo_accion") or "") not in tipos:
            continue
        momento = _momento(a.get("fecha_accion"))
        if momento is not None:
            momentos.append(momento)
    return min(momentos) if momentos else None


def _segundos_desde_origen(valor: Any) -> int | None:
    """`tiempo_solucion` del origen llega en milisegundos; 0 es centinela."""
    n = _entero(valor)
    if n is None or n <= 0:
        return None
    return int(n / 1000)


def desenlace_sla(
    *,
    tiene_compromiso: int,
    segundos_resolucion: int | None,
    segundos_resolucion_max: int | None,
    segundos_primera_respuesta: int | None,
    segundos_respuesta_max: int | None,
    ahora: datetime,
    creacion: datetime | None,
) -> str | None:
    if not tiene_compromiso:
        return None
    if segundos_resolucion is not None and segundos_resolucion_max is not None:
        if segundos_resolucion > segundos_resolucion_max:
            return "incumplido"
        if (
            segundos_primera_respuesta is not None
            and segundos_respuesta_max is not None
            and segundos_primera_respuesta > segundos_respuesta_max
        ):
            return "incumplido"
        return "cumplido"
    if (
        creacion is not None
        and segundos_resolucion_max is not None
        and (ahora - creacion).total_seconds() > segundos_resolucion_max
    ):
        return "incumplido"
    return None


def compromiso_de(
    ticket: Mapping[str, Any],
    config: Mapping[str, Any] | None,
) -> tuple[int, str | None]:
    estado = (ticket.get("estado") or "").strip()
    tipo = (ticket.get("tipo_incidencia") or "").strip()
    sla_status = (ticket.get("sla_status") or "").strip().lower()
    if estado == ESTADO_PENDIENTE or not tipo:
        return 0, MOTIVO_PENDIENTE
    if sla_status == SLA_SIN_COMPROMISO:
        return 0, MOTIVO_SIN_COMPROMISO
    if config is None:
        return 0, MOTIVO_SIN_CONFIG
    return 1, None


def construir(datos: Mapping[str, Iterable[Mapping[str, Any]]], ahora: datetime) -> list[dict]:
    marca = ahora.strftime(FORMATO)
    planes = {int(p["idplan"]): p for p in datos.get("dim_plan", []) if p.get("idplan") is not None}
    servicios = {
        int(s["id_servicio"]): s for s in datos.get("dim_servicio", []) if s.get("id_servicio") is not None
    }
    clientes = {
        int(c["idcliente"]): c for c in datos.get("dim_cliente", []) if c.get("idcliente") is not None
    }
    plan_por_cliente: dict[int, int] = {}
    for s in datos.get("suscripciones", []):
        cid = _entero(s.get("idcliente"))
        pid = _entero(s.get("idplan"))
        if cid is not None and pid is not None and pid > 0:
            plan_por_cliente[cid] = pid

    por_ticket = agrupar_por(list(datos.get("historial", [])), "id_reclamo")
    configs = list(datos.get("dim_sla_config", []))
    filas = []

    for t in datos.get("tickets", []):
        id_reclamo = _entero(t.get("id_reclamo"))
        if id_reclamo is None:
            continue
        creacion = _momento(t.get("fechahora"))
        if creacion is None:
            continue
        idcliente = _entero(t.get("idcliente")) or 0
        idplan = plan_por_cliente.get(idcliente)
        tipo_inc = (t.get("tipo_incidencia") or None) or None
        prioridad = (t.get("prioridad") or None) or None
        config = sla_vigente_en(configs, idplan, tipo_inc, prioridad, creacion)
        tiene, motivo = compromiso_de(t, config)

        acciones = por_ticket.get(id_reclamo, por_ticket.get(str(id_reclamo), []))
        hora_primera = _hito(acciones, ACCIONES_PRIMERA_RESPUESTA)
        hora_resolucion = _hito(acciones, ACCIONES_RESOLUCION)
        hora_cierre = _hito(acciones, ACCIONES_CIERRE)
        hora_cierre_confirmado = _momento(t.get("fechahoraconfirmacioncierre")) or hora_cierre

        segundos_primera = segundos_entre(creacion, hora_primera)
        segundos_resolucion = segundos_entre(creacion, hora_resolucion)
        if segundos_resolucion is None:
            segundos_resolucion = _segundos_desde_origen(t.get("tiempo_solucion"))

        idagente = _entero(t.get("id_agente_asignado"))
        idservicio = _entero(t.get("idservicio"))
        plan_fila = planes.get(idplan) if idplan is not None else None
        servicio_fila = servicios.get(idservicio) if idservicio is not None else None
        cliente_fila = clientes.get(idcliente)
        reaperturas = sum(1 for a in acciones if (a.get("tipo_accion") or "") == "reapertura")

        max_resp = _entero(config.get("segundos_respuesta_max")) if config else None
        max_res = _entero(config.get("segundos_resolucion_max")) if config else None
        idsla = _entero(config.get("idslaconfig")) if config and tiene else None

        filas.append({
            "id_reclamo": id_reclamo,
            "fecha": creacion.date().isoformat(),
            "fechahora_creacion": texto_fecha(creacion),
            "idcliente": idcliente,
            "tipo_cliente": (cliente_fila or {}).get("tipo"),
            "idplan": idplan,
            "plan": (plan_fila or {}).get("nombre") if plan_fila else None,
            "idagente": idagente,
            "tiene_agente": 1 if idagente is not None else 0,
            "tipo": (t.get("tipo") or None) or None,
            "tipo_incidencia": tipo_inc,
            "prioridad": prioridad,
            "idservicio": idservicio,
            "servicio": (servicio_fila or {}).get("nombre") if servicio_fila else None,
            "estado": (t.get("estado") or "").strip() or "Abierto",
            "idslaconfig": idsla,
            "tiene_compromiso": tiene,
            "motivo_sin_compromiso": motivo,
            "segundos_respuesta_max": max_resp if tiene else None,
            "segundos_resolucion_max": max_res if tiene else None,
            "hora_primera_respuesta": texto_fecha(hora_primera),
            "hora_resolucion": texto_fecha(hora_resolucion),
            "hora_cierre": texto_fecha(hora_cierre),
            "hora_cierre_confirmado": texto_fecha(hora_cierre_confirmado),
            "segundos_primera_respuesta": segundos_primera,
            "segundos_resolucion": segundos_resolucion,
            "desenlace_sla": desenlace_sla(
                tiene_compromiso=tiene,
                segundos_resolucion=segundos_resolucion,
                segundos_resolucion_max=max_res if tiene else None,
                segundos_primera_respuesta=segundos_primera,
                segundos_respuesta_max=max_resp if tiene else None,
                ahora=ahora,
                creacion=creacion,
            ),
            "fue_reabierto": 1 if reaperturas else 0,
            "reaperturas": reaperturas,
            "cargado_en": marca,
            "version": marca,
        })
    return filas
