"""Servicio de facturación — L2 facturas y L4 métodos de pago.

Dos reglas de presentación que este módulo sostiene:

**`dias_mora` solo cuando de verdad hay mora.** Una factura pagada, o una en
disputa, no lleva días de mora — ni siquiera `0`. Un `0` se lee como «vence hoy»
y una factura en disputa no está venciendo: está detenida a propósito.

**`tipo_documento` se expone aunque hoy tenga un solo valor** (research D6). La
operación no emite notas de crédito todavía; exponerlo cuesta nada y evita que,
el día que las emita, un listado de facturación las sume como cargos.
"""

from __future__ import annotations

from typing import Any, Callable

from core.informes.acotamiento import Acotamiento
from core.informes.formato import a_entero_ms, a_iso
from core.informes.paginacion import Orden, Pagina
from core.pinot.tiempo import ahora_ms
from core.repositories.suscripciones.informes_facturacion_repository import (
    CURSOR_FACTURAS,
    CURSOR_METODOS,
    ESTADOS_EN_MORA,
    ORDEN_FACTURAS,
    ORDEN_METODOS,
    InformesFacturacionRepository,
)

DIA_MS = 86_400_000


class InformesFacturacionService:
    def __init__(
        self,
        repo: InformesFacturacionRepository | None = None,
        ahora: Callable[[], int] | None = None,
    ):
        self.repo = repo or InformesFacturacionRepository()
        self.ahora = ahora or (lambda: ahora_ms())

    # ── L2 — Facturas ────────────────────────────────────────────────────────

    def facturas(
        self,
        *,
        acotamiento: Acotamiento,
        cursor: tuple[Any, ...] | None = None,
        limit: int = 50,
        orden: Orden = ORDEN_FACTURAS,
        estado_pago: str | None = None,
        desde_ms: int | None = None,
        hasta_ms: int | None = None,
        solo_vencidas: bool = False,
    ) -> Pagina:
        ahora = self.ahora()

        crudas = self.repo.facturas(
            cursor=cursor,
            limit=limit,
            orden=orden,
            cuenta=acotamiento.titular,
            estado_pago=estado_pago,
            desde_ms=desde_ms,
            hasta_ms=hasta_ms,
            vencidas_antes_de=ahora if solo_vencidas else None,
        )
        pagina = CURSOR_FACTURAS.recortar(crudas, limit)

        cuentas = self.repo.razones_sociales([f.get("id_cliente") for f in pagina.filas])

        return pagina._replace(
            filas=[_fila_factura(f, cuentas, ahora) for f in pagina.filas]
        )

    # ── L4 — Métodos de pago vigentes ────────────────────────────────────────

    def metodos_de_pago(
        self,
        *,
        acotamiento: Acotamiento,
        cursor: tuple[Any, ...] | None = None,
        limit: int = 50,
        orden: Orden = ORDEN_METODOS,
        caduca_en_dias: int | None = None,
    ) -> Pagina:
        ahora = self.ahora()

        crudas = self.repo.metodos_de_pago(
            cursor=cursor,
            limit=limit,
            orden=orden,
            cuenta=acotamiento.titular,
            caduca_antes_de=(
                ahora + caduca_en_dias * DIA_MS if caduca_en_dias is not None else None
            ),
        )
        pagina = CURSOR_METODOS.recortar(crudas, limit)

        cuentas = self.repo.razones_sociales([f.get("idcliente") for f in pagina.filas])

        return pagina._replace(
            filas=[
                {
                    "cuenta": cuentas.get(fila.get("idcliente")),
                    "tipo": fila.get("tipo"),
                    # Los últimos dígitos identifican el método ante una persona
                    # y son inútiles para cobrar. El identificador de cobro, que
                    # sí serviría, no llega hasta aquí: la consulta no lo trae.
                    "ultimos_digitos": fila.get("ultimosdigitos"),
                    "fecha_expiracion": a_iso(fila.get("fechaexpiracion")),
                    "dias_para_caducar": _dias_hasta(ahora, fila.get("fechaexpiracion")),
                }
                for fila in pagina.filas
            ]
        )


def _fila_factura(
    cruda: dict[str, Any], cuentas: dict[int, str], ahora: int
) -> dict[str, Any]:
    fila = {
        "cuenta": cuentas.get(cruda.get("id_cliente")),
        "numero_factura": cruda.get("numero_factura"),
        "periodo": cruda.get("periodo"),
        "tipo_documento": _tipo_documento(cruda),
        "monto_base": cruda.get("monto_base"),
        "impuestos": cruda.get("impuestos"),
        "monto_total": cruda.get("monto_total"),
        "estado_pago": cruda.get("estado_pago"),
        "reintentos": cruda.get("reintentos"),
        "fecha_emision": a_iso(cruda.get("fecha_emision")),
        "fecha_vencimiento": a_iso(cruda.get("fecha_vencimiento")),
    }
    mora = _dias_mora(cruda, ahora)
    if mora is not None:
        fila["dias_mora"] = mora
    return fila


def _tipo_documento(cruda: dict[str, Any]) -> str:
    """`nota_credito` o `cargo`.

    Hoy `es_nota_credito` se escribe siempre como `False` —la operación no emite
    notas de crédito—, así que este campo tiene un solo valor. Se expone
    igualmente: cuando se emitan, un consumidor que ya lo lea no las sumará como
    cargos (research D6).
    """
    return "nota_credito" if cruda.get("es_nota_credito") else "cargo"


def _dias_mora(cruda: dict[str, Any], ahora: int) -> int | None:
    """Días de mora, o `None` si la factura no está en mora.

    **`None` y no `0`.** Una factura pagada o en disputa no lleva cero días de
    mora: no lleva ninguno, porque no está en mora. Un `0` se leería como «vence
    hoy» y pondría en la misma línea un cobro urgente y uno detenido a propósito.
    """
    if cruda.get("estado_pago") not in ESTADOS_EN_MORA:
        return None
    vencimiento = a_entero_ms(cruda.get("fecha_vencimiento"))
    if vencimiento is None or vencimiento >= ahora:
        return None
    return (ahora - vencimiento) // DIA_MS


def _dias_hasta(ahora: int, expiracion: Any) -> int | None:
    """Días completos que faltan para caducar, o `None` si no hay fecha."""
    fin = a_entero_ms(expiracion)
    if fin is None:
        return None
    return max(0, (fin - ahora) // DIA_MS)
