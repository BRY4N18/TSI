"""`hecho_suscripcion`: instantánea acumulada, **grano una suscripción**.

Cinco defectos del origen se resuelven **aquí**, no en las trece consultas:

1. `estado_derivado` **nunca** sale de `activo`: hay canceladas con esa columna
   en verdadero, y usarla inflaría el MRR.
2. `motivo_cancelacion` solo si el estado dice que canceló.
3. `vigencia_inconsistente` marca el fin anterior al inicio; no se corrige ni
   se descarta.
4. `idplan_programado` nulo en vez del centinela `0`.
5. `precio_mensualizado` ausente —nunca cero— si no hay periodicidad.

`fecha` / `fecha_alta` son el **alta original**. El origen reescribe
`fecha_inicio` al renovar; si se usara esa fecha como partición, una recarga
duplicaría la suscripción en dos meses.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Callable, Iterable, Mapping

from lib.clickhouse_http_client import query_clickhouse
from lib.dimensiones.desconocido import ETIQUETA_DESCONOCIDA, resolver_o_desconocido
from lib.hechos.comun import FORMATO, a_datetime, indexar_por, texto_fecha
from lib.pinot_http_client import query_pinot

LIMITE = 100_000

CONSULTA_SUSCRIPCIONES = f"""
    SELECT id_suscripcion, idcliente, idplan, precio, periodicidad, nivel,
           severidades_desbloqueadas, estado, renovacionautomatica,
           motivocancelacion, fechacancelacion, fecha_inicio, fecha_fin,
           idplan_programado
    FROM Fact_Suscripcion
    LIMIT {LIMITE}
"""

CONSULTA_PLANES = "SELECT idplan, nombre, nivel FROM dim_plan FINAL"
CONSULTA_CLIENTES = "SELECT idcliente, tipo FROM dim_cliente FINAL"
CONSULTA_EXISTENTES = (
    "SELECT id_suscripcion, fecha, fecha_alta FROM hecho_suscripcion FINAL"
)

ESTADO_CANCELADA = "cancelada"
ESTADO_SUSPENDIDA = "suspendida"
ESTADO_VENCIDA = "vencida"
ESTADO_VIGENTE = "vigente"

PERIODICIDAD_MENSUAL = {"mensual", "month", "monthly"}
PERIODICIDAD_ANUAL = {"anual", "year", "yearly", "annual"}


def extraer(
    consultar_origen: Callable[[str], list[dict]] = query_pinot,
    consultar_modelo: Callable[[str], list[dict]] = query_clickhouse,
) -> dict[str, list[dict]]:
    existentes: list[dict] = []
    try:
        existentes = consultar_modelo(CONSULTA_EXISTENTES)
    except Exception:  # noqa: BLE001 — la tabla puede no existir en la primera carga
        existentes = []
    return {
        "suscripciones": consultar_origen(CONSULTA_SUSCRIPCIONES),
        "dim_plan": consultar_modelo(CONSULTA_PLANES),
        "dim_cliente": consultar_modelo(CONSULTA_CLIENTES),
        "existentes": existentes,
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


def estado_derivado(
    fila: Mapping[str, Any], *, ahora: datetime, inicio: datetime | None, fin: datetime | None
) -> str:
    """El estado analítico. **No mira `activo`.**

    Una vigencia invertida no se trata como vencida: el origen sigue cobrando
    esa fila, y marcarla vencida la sacaría del MRR — descartarla por la
    puerta de atrás.
    """
    crudo = str(fila.get("estado") or "").strip().lower()
    if crudo == ESTADO_CANCELADA:
        return ESTADO_CANCELADA
    if crudo == ESTADO_SUSPENDIDA:
        return ESTADO_SUSPENDIDA
    if vigencia_inconsistente(inicio, fin):
        return ESTADO_VIGENTE
    if fin is not None and fin.date() < ahora.date():
        return ESTADO_VENCIDA
    return ESTADO_VIGENTE


def precio_mensualizado(precio: Any, periodicidad: Any) -> float | None:
    """Normaliza a mensual con el **precio de la suscripción**, no el de lista.

    Ausente —nunca cero— si no se sabe cada cuánto se cobra.
    """
    if precio is None or precio == "":
        return None
    try:
        monto = float(precio)
    except (TypeError, ValueError):
        return None
    per = str(periodicidad or "").strip().lower()
    if not per:
        return None
    if per in PERIODICIDAD_MENSUAL:
        return round(monto, 2)
    if per in PERIODICIDAD_ANUAL:
        return round(monto / 12.0, 2)
    return None


def vigencia_inconsistente(inicio: datetime | None, fin: datetime | None) -> int:
    if inicio is None or fin is None:
        return 0
    return 1 if fin < inicio else 0


def plan_programado_o_nulo(valor: Any) -> int | None:
    if valor is None or valor == "":
        return None
    try:
        n = int(valor)
    except (TypeError, ValueError):
        return None
    return None if n <= 0 else n


def _motivo_si_cancelo(estado: str, motivo: Any) -> str | None:
    if estado != ESTADO_CANCELADA:
        return None
    texto = str(motivo).strip() if motivo is not None else ""
    return texto or None


def _severidades(valor: Any) -> list[int]:
    from lib.dimensiones.dim_plan import desplegar_severidades

    return desplegar_severidades(valor)


def construir(
    datos: Mapping[str, Iterable[Mapping[str, Any]]], ahora: datetime
) -> list[dict]:
    planes = indexar_por(datos.get("dim_plan", []), "idplan")
    clientes = indexar_por(
        ({**c, "idcliente": int(c["idcliente"])} for c in datos.get("dim_cliente", [])),
        "idcliente",
    )
    altas: dict[int, datetime] = {}
    for e in datos.get("existentes", []):
        sid = int(e["id_suscripcion"])
        momento = _momento(e.get("fecha_alta")) or _momento(e.get("fecha"))
        if momento is not None:
            altas[sid] = momento

    cargado = ahora.strftime(FORMATO)
    filas = []
    for s in datos.get("suscripciones", []):
        sid = int(s["id_suscripcion"])
        inicio_origen = _momento(s.get("fecha_inicio"))
        alta = altas.get(sid) or inicio_origen or ahora
        fin = _momento(s.get("fecha_fin"))
        estado = estado_derivado(s, ahora=ahora, inicio=inicio_origen, fin=fin)
        idplan = int(resolver_o_desconocido(s.get("idplan"), planes))
        plan = planes.get(idplan, {})
        idcliente = int(s.get("idcliente") or 0)
        cliente = clientes.get(idcliente, {})
        precio = float(s.get("precio") or 0)
        periodicidad = s.get("periodicidad") or None
        filas.append({
            "id_suscripcion": sid,
            "fecha": alta.date().isoformat(),
            "idcliente": idcliente,
            "tipo_cliente": cliente.get("tipo"),
            "idplan": idplan,
            "plan": plan.get("nombre") or ETIQUETA_DESCONOCIDA,
            "nivel": s.get("nivel") or plan.get("nivel"),
            "fecha_alta": texto_fecha(alta),
            "fecha_fin_prevista": texto_fecha(fin),
            "fecha_ultima_renovacion": (
                texto_fecha(inicio_origen)
                if altas.get(sid) and inicio_origen and inicio_origen != altas[sid]
                else None
            ),
            "fecha_suspension": None,
            "fecha_reactivacion": None,
            "fecha_cancelacion": texto_fecha(_momento(s.get("fechacancelacion"))),
            "estado_derivado": estado,
            "motivo_cancelacion": _motivo_si_cancelo(estado, s.get("motivocancelacion")),
            "precio": round(precio, 2),
            "periodicidad": periodicidad,
            "precio_mensualizado": precio_mensualizado(s.get("precio"), periodicidad),
            "renovacion_automatica": 1 if s.get("renovacionautomatica") in (True, 1, "true", "1") else 0,
            "idplan_programado": plan_programado_o_nulo(s.get("idplan_programado")),
            "severidades_contratadas": _severidades(s.get("severidades_desbloqueadas")),
            "vigencia_inconsistente": vigencia_inconsistente(inicio_origen, fin),
            "cargado_en": cargado,
            "version": cargado,
        })
    return filas
