"""Excepciones de facturacion de excedente (BE-DELTA-04 y BE-DELTA-05).

Por que existe este servicio
-----------------------------
RF-APM-013 dice que una factura que agota sus tres reintentos queda «pendiente
de emision manual», y RN-APM-014 que **una factura de excedente nunca debe
quedar silenciosamente sin crearse, porque eso ocultaria ingreso real no
cobrado**.

Hasta 2026-08-10 esa regla se cumplia a medias: los dos casos se auditaban y se
mandaba un correo, pero **no habia forma de consultarlos**. El unico aviso era
un mensaje en un buzon, que es exactamente el silencio que la regla prohibe.

Los dos casos NO son el mismo problema
---------------------------------------
| Tipo | Que paso | Hay factura | Que hay que hacer |
|---|---|---|---|
| `reintentos_agotados` | La factura existe; su emision fallo 3 veces | Si | Emitirla a mano |
| `no_tarificable` | El plan no tiene `precio_excedente_llamada` | **No** | Configurar la tarifa y reejecutar el corte |

Presentarlos juntos sin distinguir haria que un Administrador buscase una
factura que en el segundo caso **no existe**. Por eso el discriminador `tipo` es
obligatorio en la respuesta, y el importe del segundo va a `None` y **nunca a
0.0**: un cero diria «se facturo nada», y la verdad es que no se pudo calcular.
"""

from __future__ import annotations

from typing import Any

from apps.partners.services.tarificacion_excedente_service import (
    TIPO_EXCEDENTE,
    TarificacionExcedenteService,
)
from core.pinot.client import PinotClient
from core.repositories.partners.partner_repository import PartnerRepository

TIPO_REINTENTOS_AGOTADOS = "reintentos_agotados"
TIPO_NO_TARIFICABLE = "no_tarificable"

# Prefijo que `programar_reintento` escribe al agotar los tres intentos.
PREFIJO_AGOTADOS = "agotados:"


class ExcepcionesFacturacionService:
    def __init__(
        self,
        pinot: PinotClient | None = None,
        partners: PartnerRepository | None = None,
        tarificacion: TarificacionExcedenteService | None = None,
    ):
        self.pinot = pinot or PinotClient()
        self.partners = partners or PartnerRepository()
        self.tarificacion = tarificacion or TarificacionExcedenteService(pinot=self.pinot)

    # --- BE-DELTA-04 ---------------------------------------------------------

    def reintentos_agotados(self, *, periodo: str | None = None) -> list[dict[str, Any]]:
        """Facturas de excedente que agotaron sus tres reintentos.

        Se identifican por el prefijo que deja `programar_reintento`, no por un
        estado propio: no hay columna de «pendiente de emision manual» y crear
        una seria una segunda verdad sobre `resultado_ultimo_reintento`.
        """
        filas = self.pinot.query(
            "SELECT * FROM Fact_Factura WHERE tipo = %(tipo)s LIMIT 1000",
            {"tipo": TIPO_EXCEDENTE},
        )
        excepciones = []
        for factura in filas or []:
            resultado = str(factura.get("resultado_ultimo_reintento", ""))
            if not resultado.startswith(PREFIJO_AGOTADOS):
                continue
            if periodo and str(factura.get("periodo")) != periodo:
                continue
            excepciones.append(self._como_excepcion(factura))
        return excepciones

    def _como_excepcion(self, factura: dict[str, Any]) -> dict[str, Any]:
        idcliente = int(factura.get("id_cliente", 0) or 0)
        partner = self.partners.find_by_cliente(idcliente)
        return {
            "tipo": TIPO_REINTENTOS_AGOTADOS,
            "idpartner": int(partner["idpartner"]) if partner else -1,
            "nombrepartner": str(partner.get("nombrepartner", "")) if partner else "",
            "periodo": factura.get("periodo", ""),
            "id_factura": factura.get("id_factura"),
            # `monto_total`, no `monto`: esa columna no existe en el esquema
            # y publicarla hacia que Pinot la descartara en silencio.
            "importe": factura.get("monto_total"),
            "intentos": int(factura.get("reintentos", 0) or 0),
            "ultimo_resultado": str(factura.get("resultado_ultimo_reintento", "")),
        }

    # --- BE-DELTA-05 ---------------------------------------------------------

    def no_tarificables(self, *, anio: int, mes: int) -> list[dict[str, Any]]:
        """Partners con excedente que **no se pudo tarificar** en el período.

        Se derivan del mismo calculo que hace el corte (`calcular`), sin emitir
        nada: es una consulta. Antes de BE-DELTA-05 este caso solo existia como
        un correo, y si el correo se perdia el ingreso se perdia con el.
        """
        excepciones = []
        cursor = None
        while True:
            pagina, cursor = self.partners.list(limit=200, cursor=cursor)
            for partner in pagina:
                calculo = self.tarificacion.calcular(
                    int(partner["idpartner"]), anio=anio, mes=mes
                )
                if calculo.get("motivo") != "sin_tarifa_configurada":
                    continue
                excepciones.append({
                    "tipo": TIPO_NO_TARIFICABLE,
                    "idpartner": int(partner["idpartner"]),
                    "nombrepartner": str(partner.get("nombrepartner", "")),
                    "periodo": calculo.get("periodo", ""),
                    # No hay factura ni importe: el plan no tiene tarifa con la
                    # que calcularlo. `None`, jamas 0.0.
                    "id_factura": None,
                    "importe": None,
                    "intentos": None,
                    "ultimo_resultado": (
                        f"{calculo.get('excedentes', 0)} llamadas excedentes sin tarifa "
                        "configurada en el plan"
                    ),
                })
            if not cursor:
                break
        return excepciones

    # --- Vista unificada -----------------------------------------------------

    def listar(self, *, anio: int, mes: int) -> list[dict[str, Any]]:
        """Los dos tipos juntos, cada uno con su discriminador.

        Ordenados con los no tarificables primero: son los que llevan mas tiempo
        sin resolverse sin que nadie lo sepa, porque ni siquiera dejaron factura.
        """
        periodo = self.tarificacion.periodo_etiqueta(anio, mes)
        return [
            *self.no_tarificables(anio=anio, mes=mes),
            *self.reintentos_agotados(periodo=periodo),
        ]
