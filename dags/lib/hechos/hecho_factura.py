"""`hecho_factura`: transacción, **grano una factura o nota de crédito**.

`monto_con_signo` existe para que sumar ingresos sea sumar: las notas restan
solas. `En disputa` se conserva como estado propio — no es impago.

Sin `idmetodopago`, sin `desglose_cargos` y sin `motivo_anulacion`.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Callable, Iterable, Mapping

from lib.clickhouse_http_client import query_clickhouse
from lib.hechos.comun import FORMATO, a_datetime, indexar_por, texto_fecha
from lib.pinot_http_client import query_pinot

LIMITE = 500_000

#: `id_cliente` con guion bajo: así se llama en el origen.
CONSULTA_FACTURAS = f"""
    SELECT id_factura, id_cliente, id_suscripcion, estado_pago, tipo,
           monto_base, impuestos, monto_total, fecha_emision, fecha_vencimiento,
           reintentos, es_nota_credito, id_factura_original
    FROM Fact_Factura
    LIMIT {LIMITE}
"""

CONSULTA_SUSCRIPCIONES = (
    "SELECT id_suscripcion, idplan, plan, tipo_cliente FROM hecho_suscripcion FINAL"
)
CONSULTA_CLIENTES = "SELECT idcliente, tipo FROM dim_cliente FINAL"

ESTADO_DISPUTA = "En disputa"
ESTADO_PAGADA = "Pagada"
ESTADO_PENDIENTE = "Pendiente"


def extraer(
    consultar_origen: Callable[[str], list[dict]] = query_pinot,
    consultar_modelo: Callable[[str], list[dict]] = query_clickhouse,
) -> dict[str, list[dict]]:
    return {
        "facturas": consultar_origen(CONSULTA_FACTURAS),
        "hecho_suscripcion": consultar_modelo(CONSULTA_SUSCRIPCIONES),
        "dim_cliente": consultar_modelo(CONSULTA_CLIENTES),
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


def _es_nota(valor: Any) -> bool:
    return valor in (True, 1, "true", "1", "True")


def _monto(valor: Any) -> float:
    try:
        return round(float(valor or 0), 2)
    except (TypeError, ValueError):
        return 0.0


def pagada_primer_intento(estado: str, reintentos: int, es_nota: bool) -> int:
    if es_nota:
        return 0
    return 1 if estado == ESTADO_PAGADA and reintentos == 0 else 0


def dias_mora(
    estado: str, vencimiento: datetime | None, *, ahora: datetime, es_nota: bool
) -> int | None:
    """Días de mora, o ausente.

    `En disputa` no es impago: no suma mora. Una pagada o una nota tampoco.
    """
    if es_nota or estado in (ESTADO_DISPUTA, ESTADO_PAGADA, "Anulada"):
        return None
    if estado != ESTADO_PENDIENTE or vencimiento is None:
        return None
    delta = (ahora.date() - vencimiento.date()).days
    return delta if delta > 0 else None


def construir(
    datos: Mapping[str, Iterable[Mapping[str, Any]]], ahora: datetime
) -> list[dict]:
    por_suscripcion = indexar_por(
        (
            {**s, "id_suscripcion": int(s["id_suscripcion"])}
            for s in datos.get("hecho_suscripcion", [])
        ),
        "id_suscripcion",
    )
    clientes = indexar_por(
        ({**c, "idcliente": int(c["idcliente"])} for c in datos.get("dim_cliente", [])),
        "idcliente",
    )
    cargado = ahora.strftime(FORMATO)
    filas = []
    for f in datos.get("facturas", []):
        emision = _momento(f.get("fecha_emision")) or ahora
        vencimiento = _momento(f.get("fecha_vencimiento"))
        es_nota = _es_nota(f.get("es_nota_credito"))
        signo = -1 if es_nota else 1
        total = _monto(f.get("monto_total"))
        estado = str(f.get("estado_pago") or ESTADO_PENDIENTE)
        try:
            reintentos = int(f.get("reintentos") or 0)
        except (TypeError, ValueError):
            reintentos = 0
        idcliente = int(f.get("id_cliente") or f.get("idcliente") or 0)
        id_sus = f.get("id_suscripcion")
        try:
            id_sus_i = int(id_sus) if id_sus not in (None, "") else None
        except (TypeError, ValueError):
            id_sus_i = None
        sus = por_suscripcion.get(id_sus_i, {}) if id_sus_i is not None else {}
        cliente = clientes.get(idcliente, {})
        filas.append({
            "id_factura": str(f.get("id_factura") or ""),
            "fecha": emision.date().isoformat(),
            "fecha_emision": texto_fecha(emision),
            "fecha_vencimiento": texto_fecha(vencimiento),
            "idcliente": idcliente,
            "tipo_cliente": sus.get("tipo_cliente") or cliente.get("tipo"),
            "id_suscripcion": id_sus_i,
            "idplan": sus.get("idplan"),
            "plan": sus.get("plan"),
            "estado_pago": estado,
            "tipo": (str(f["tipo"]).strip() or None) if f.get("tipo") else None,
            "es_nota_credito": 1 if es_nota else 0,
            "id_factura_original": (
                str(f["id_factura_original"]) if f.get("id_factura_original") else None
            ),
            "signo": signo,
            "monto_base": _monto(f.get("monto_base")),
            "impuestos": _monto(f.get("impuestos")),
            "monto_total": total,
            "monto_con_signo": round(total * signo, 2),
            "reintentos": reintentos,
            "pagada_primer_intento": pagada_primer_intento(estado, reintentos, es_nota),
            "dias_mora": dias_mora(estado, vencimiento, ahora=ahora, es_nota=es_nota),
            "cargado_en": cargado,
        })
    return filas
