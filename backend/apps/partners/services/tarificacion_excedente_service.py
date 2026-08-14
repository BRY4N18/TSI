"""Tarificacion del excedente al cierre del periodo (CU-O54, RF-APM-011 a 014).

Este es el unico servicio del modulo que mueve dinero. Cuatro reglas lo
gobiernan, y las cuatro protegen al cliente antes que al negocio:

1. **Nunca facturar dos veces** (RF-APM-012). Antes de emitir se comprueba si ya
   existe factura de ese `id_cliente` + `periodo` + `tipo='excedente_api'`. Un
   doble cobro es peor que no cobrar: no cuesta dinero, cuesta confianza.

2. **Sin tarifa configurada NO se emite factura de cero** (RF-APM-011). El
   centinela `-1.0` significa «nadie configuro el precio», no «es gratis».
   Emitir cero seria ingreso real no cobrado, en silencio. Se alerta y se deja
   pendiente de emision manual.

3. **Los reintentos son estado persistido, nunca `sleep`** (RF-APM-013). Tres
   intentos con espera creciente —1 h, 6 h, 24 h— guardados en la propia
   factura. Con `sleep`, un reinicio del contenedor perderia el reintento y el
   cobro se quedaria a medias sin que nadie se entere.

4. **Una factura en disputa se excluye del cobro** (RF-APM-014). Este modulo no
   abre ni resuelve disputas: solo respeta la exclusion.

Determinismo (RNF-APM-001): dos ejecuciones sobre el mismo periodo y los mismos
datos producen el mismo importe. Es la base de poder discutir una factura.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from apps.partners.services.metricas_consumo_service import MetricasConsumoService
from core.pinot.client import PinotClient
from core.repositories.partners.api_integracion_repository import (
    ApiIntegracionRepository,
)
from core.repositories.partners.kafka_writer import KafkaWriter
from core.repositories.partners.partner_repository import PartnerRepository
from core.repositories.partners.plan_read_repository import PlanReadRepository

logger = logging.getLogger("tsi.partners.tarificacion")

ENTORNO_PRODUCCION = "Producción"
TIPO_EXCEDENTE = "excedente_api"
ESTADO_PENDIENTE = "Pendiente"
ESTADO_DISPUTA = "En disputa"

SIN_CUPO = -1
# `Dim_Plan.precio_excedente_llamada` sin tarifa configurada.
SIN_TARIFA = -1.0

# RN-APM-013: tres reintentos con espera creciente, en milisegundos.
ESPERAS_REINTENTO_MS = (
    1 * 60 * 60 * 1000,    # 1 h
    6 * 60 * 60 * 1000,    # 6 h
    24 * 60 * 60 * 1000,   # 24 h
)
MAX_REINTENTOS = len(ESPERAS_REINTENTO_MS)

TOPIC_FACTURA = "Fact_Factura_topic"


class TarificacionExcedenteService:
    def __init__(
        self,
        api_integracion: ApiIntegracionRepository | None = None,
        partners: PartnerRepository | None = None,
        planes: PlanReadRepository | None = None,
        pinot: PinotClient | None = None,
        kafka: KafkaWriter | None = None,
        metricas: MetricasConsumoService | None = None,
        alertas=None,
    ):
        self.pinot = pinot or PinotClient()
        self.api_integracion = api_integracion or ApiIntegracionRepository()
        self.partners = partners or PartnerRepository()
        self.planes = planes or PlanReadRepository(pinot=self.pinot)
        self.kafka = kafka or KafkaWriter()
        self.metricas = metricas or MetricasConsumoService()
        self.alertas = alertas

    @staticmethod
    def _now_ms() -> int:
        return int(datetime.now(timezone.utc).timestamp() * 1000)

    @staticmethod
    def periodo_etiqueta(anio: int, mes: int) -> str:
        """`2026-08`. Es la clave de no duplicacion junto al cliente."""
        return f"{anio:04d}-{mes:02d}"

    # --- Calculo -------------------------------------------------------------

    def calcular(self, idpartner: int, *, anio: int, mes: int) -> dict[str, Any]:
        """Separa lo incluido de lo excedente y calcula el importe.

        No emite nada: solo calcula. Es determinista — mismas entradas, mismo
        resultado — para que dos ejecuciones del corte coincidan (RNF-APM-001).
        """
        partner = self.partners.find_by_id(idpartner)
        if not partner:
            return {"emitible": False, "motivo": "partner_inexistente"}

        desde_ms, hasta_ms = self.metricas.periodo_mensual(anio, mes)
        llamadas = self.api_integracion.llamadas_del_periodo(
            idpartner, entorno=ENTORNO_PRODUCCION, desde_ms=desde_ms, hasta_ms=hasta_ms
        )
        cupo = int(partner.get("limitellamadasmes", SIN_CUPO))

        base = {
            "idpartner": idpartner,
            "idcliente": int(partner["idcliente"]),
            "periodo": self.periodo_etiqueta(anio, mes),
            "llamadas": llamadas,
            "cupo": cupo,
            "incluidas": min(llamadas, cupo) if cupo != SIN_CUPO else llamadas,
            "excedentes": max(0, llamadas - cupo) if cupo != SIN_CUPO else 0,
        }

        if base["excedentes"] == 0:
            return {**base, "emitible": False, "motivo": "sin_excedente", "importe": 0.0}

        precio = self._precio_excedente(int(partner["idcliente"]))
        if precio is None:
            # Centinela: NO se emite factura de cero. Facturar cero seria
            # ingreso real no cobrado y nadie se enteraria (RN-APM-014).
            return {
                **base,
                "emitible": False,
                "motivo": "sin_tarifa_configurada",
                "importe": None,
            }

        return {
            **base,
            "emitible": True,
            "precio_unitario": precio,
            "importe": round(base["excedentes"] * precio, 2),
        }

    def _precio_excedente(self, idcliente: int) -> float | None:
        """La tarifa del plan vigente. `None` si vale el centinela."""
        suscripcion = self.planes.suscripcion_vigente(idcliente)
        if not suscripcion:
            return None
        plan = self.planes.find_plan(int(suscripcion["idplan"]))
        if not plan:
            return None
        precio = float(plan.get("precio_excedente_llamada", SIN_TARIFA))
        return None if precio == SIN_TARIFA or precio < 0 else precio

    # --- No duplicacion ------------------------------------------------------

    def factura_existente(self, idcliente: int, periodo: str) -> dict[str, Any] | None:
        """La factura de excedente ya emitida para ese cliente y periodo.

        Es la comprobacion que impide el doble cobro (RF-APM-012): sin ella, un
        reintento sobre un proceso que SI llego a emitir cobraria dos veces.
        """
        filas = self.pinot.query(
            "SELECT * FROM Fact_Factura WHERE id_cliente = %(idcliente)s "
            "AND periodo = %(periodo)s AND tipo = %(tipo)s LIMIT 10",
            {"idcliente": idcliente, "periodo": periodo, "tipo": TIPO_EXCEDENTE},
        )
        return filas[0] if filas else None

    @staticmethod
    def en_disputa(factura: dict[str, Any]) -> bool:
        """RF-APM-014 — excluida del cobro automatico mientras se resuelve."""
        return str(factura.get("estado_pago", "")).strip().lower() == ESTADO_DISPUTA.lower()

    # --- Emision -------------------------------------------------------------

    def emitir(self, idpartner: int, *, anio: int, mes: int) -> dict[str, Any]:
        """Calcula y emite la factura de excedente si procede.

        Devuelve siempre un diccionario con `resultado`, nunca lanza: el job
        procesa muchos partners y uno no puede tumbar al resto.
        """
        calculo = self.calcular(idpartner, anio=anio, mes=mes)

        if not calculo.get("emitible"):
            motivo = calculo.get("motivo")
            if motivo == "sin_tarifa_configurada":
                self._auditar("factura_excedente_no_tarificable", calculo)
                self._alertar_no_tarificable(calculo)
                return {**calculo, "resultado": "no_tarificable"}
            return {**calculo, "resultado": "omitida"}

        self._auditar("factura_excedente_intento", calculo)

        previa = self.factura_existente(calculo["idcliente"], calculo["periodo"])
        if previa is not None:
            # Ya emitida: no se toca. Incluye el caso de la factura en disputa,
            # que ademas queda explicitamente fuera del cobro automatico.
            return {
                **calculo,
                "resultado": "en_disputa" if self.en_disputa(previa) else "ya_emitida",
                "idfactura": previa.get("id_factura"),
            }

        try:
            factura = self._publicar_factura(calculo)
        except Exception as exc:  # noqa: BLE001 — se reintenta, no se abandona
            logger.exception(
                "excedente_emision_fallida",
                extra={"idpartner": idpartner, "periodo": calculo["periodo"]},
            )
            return {**calculo, "resultado": "fallida", "error": str(exc)}

        self._auditar(
            "factura_excedente_emitida",
            calculo,
            id_factura=factura["id_factura"],
            importe=calculo["importe"],
        )
        return {**calculo, "resultado": "emitida", "idfactura": factura["id_factura"]}

    def _auditar(self, evento: str, calculo: dict[str, Any], **extra: Any) -> None:
        """Rastro estructurado de cada intento de emision y su resultado.

        Facturar es la accion con mas consecuencias del modulo: si un cliente
        discute un cobro, esto es lo que permite reconstruir **que se calculo,
        con que cifras y cuando**, sin depender de la memoria de nadie.
        """
        logger.info(
            "tarificacion_audit",
            extra={
                "evento": evento,
                "idpartner": calculo.get("idpartner"),
                "idcliente": calculo.get("idcliente"),
                "periodo": calculo.get("periodo"),
                "llamadas": calculo.get("llamadas"),
                "cupo": calculo.get("cupo"),
                "excedentes": calculo.get("excedentes"),
                "timestamp": self._now_ms(),
                **extra,
            },
        )

    def _publicar_factura(self, calculo: dict[str, Any]) -> dict[str, Any]:
        """Emite la factura de excedente.

        **El importe va en `monto_base` y `monto_total`, no en `monto`.**
        `Fact_Factura` no tiene ninguna columna llamada `monto`: hasta
        2026-08-10 se publicaba ahi y **Pinot la descartaba en silencio**, asi
        que la factura se creaba sin su importe. Es exactamente el fallo que
        RN-APM-014 quiere evitar, disfrazado: la factura existe, pero no cobra
        nada. Se detecto al mirar la cola de excepciones en la app real.
        """
        ahora = self._now_ms()
        importe = float(calculo["importe"])
        factura = {
            "id_factura": str(uuid.uuid4()),
            "id_cliente": calculo["idcliente"],
            "tipo": TIPO_EXCEDENTE,
            "periodo": calculo["periodo"],
            "monto_base": importe,
            "impuestos": 0.0,
            "monto_total": importe,
            "estado_pago": ESTADO_PENDIENTE,
            "reintentos": 0,
            "resultado_ultimo_reintento": "",
            "fecha_emision": ahora,
            "fecha_actualizacion": ahora,
            "activo": True,
        }
        self.kafka.publish(TOPIC_FACTURA, factura)
        return factura

    # --- Reintentos por estado persistido -----------------------------------

    def programar_reintento(
        self, factura: dict[str, Any], motivo: str, *, ahora_ms: int | None = None
    ) -> dict[str, Any]:
        """Agenda el siguiente intento **guardandolo**, no esperando.

        Con `sleep`, un reinicio del contenedor perderia el reintento y el cobro
        quedaria a medias sin rastro. Persistido, el job lo recoge cuando toque.
        """
        ahora = ahora_ms if ahora_ms is not None else self._now_ms()
        intentos = int(factura.get("reintentos", 0)) + 1

        if intentos > MAX_REINTENTOS:
            # Agotados: pendiente de emision manual + alerta (RF-APM-013).
            actualizada = {
                **factura,
                "reintentos": intentos,
                "resultado_ultimo_reintento": f"agotados: {motivo}",
                "fecha_actualizacion": ahora,
            }
            self.kafka.publish(TOPIC_FACTURA, actualizada)
            self._alertar_reintentos_agotados(actualizada, motivo)
            return {**actualizada, "resultado": "reintentos_agotados"}

        espera = ESPERAS_REINTENTO_MS[intentos - 1]
        actualizada = {
            **factura,
            "reintentos": intentos,
            "resultado_ultimo_reintento": motivo,
            # El "cuándo toca" NO se guarda en una columna propia: se deriva de
            # `reintentos` + `fecha_actualizacion`. Antes se publicaba
            # `proximo_reintento`, que **no existe en el esquema de
            # Fact_Factura**: Pinot lo descartaba al escribir y **rechazaba la
            # consulta** que lo filtraba, así que el job moría en cada
            # ejecución y ninguna factura de excedente llegaba a emitirse.
            # Mismo error que ya se había cometido con `monto` (ver arriba).
            "fecha_actualizacion": ahora,
        }
        self.kafka.publish(TOPIC_FACTURA, actualizada)
        return {
            **actualizada,
            "resultado": "reintento_programado",
            "espera_ms": espera,
        }

    def reintentos_vencidos(self, *, ahora_ms: int | None = None) -> list[dict[str, Any]]:
        """Facturas de excedente cuyo siguiente intento ya toca.

        El vencimiento se **deriva** de `reintentos` (cuántos van) y
        `fecha_actualizacion` (cuándo se agendó el último), que son columnas
        reales de `Fact_Factura`. No existe ninguna `proximo_reintento`: la
        versión anterior la consultaba y Pinot rechazaba la consulta entera, de
        modo que el job caía antes de emitir nada.
        """
        ahora = ahora_ms if ahora_ms is not None else self._now_ms()
        filas = self.pinot.query(
            "SELECT * FROM Fact_Factura WHERE tipo = %(tipo)s LIMIT 1000",
            {"tipo": TIPO_EXCEDENTE},
        )
        vencidas = []
        for f in filas:
            # Una factura en disputa no se reintenta aunque le toque (RF-APM-014).
            if self.en_disputa(f):
                continue
            if self.vencimiento_reintento(f, ahora_ms=ahora) is True:
                vencidas.append(f)
        return vencidas

    def vencimiento_reintento(
        self, factura: dict[str, Any], *, ahora_ms: int
    ) -> bool:
        """¿Le toca ya el siguiente intento a esta factura?

        `reintentos = 0` es una factura recién emitida sin fallo; por encima de
        `MAX_REINTENTOS` está agotada y espera emisión manual. En ambos casos no
        se reintenta.
        """
        intentos = int(factura.get("reintentos", 0) or 0)
        if not 1 <= intentos <= MAX_REINTENTOS:
            return False
        agendado = int(factura.get("fecha_actualizacion", 0) or 0)
        return agendado + ESPERAS_REINTENTO_MS[intentos - 1] <= ahora_ms

    # --- Alertas de excepcion ------------------------------------------------

    def _alertar_no_tarificable(self, calculo: dict[str, Any]) -> None:
        logger.error(
            "excedente_sin_tarifa",
            extra={
                "idpartner": calculo.get("idpartner"),
                "periodo": calculo.get("periodo"),
                "excedentes": calculo.get("excedentes"),
            },
        )
        self._avisar(
            asunto="[TSI] Excedente de API no tarificable",
            cuerpo=(
                f"El partner {calculo.get('idpartner')} tiene "
                f"{calculo.get('excedentes')} llamadas de excedente en el período "
                f"{calculo.get('periodo')}, pero su plan **no tiene tarifa de "
                f"excedente configurada**.\n\n"
                "No se emitió factura: emitir una de importe cero sería ingreso "
                "real no cobrado. Configura la tarifa del plan y vuelve a "
                "ejecutar el corte, o emite la factura manualmente."
            ),
        )

    def _alertar_reintentos_agotados(self, factura: dict[str, Any], motivo: str) -> None:
        logger.error(
            "excedente_reintentos_agotados",
            extra={"id_factura": factura.get("id_factura"), "motivo": motivo},
        )
        self._avisar(
            asunto="[TSI] Facturación de excedente pendiente de emisión manual",
            cuerpo=(
                f"La factura {factura.get('id_factura')} del período "
                f"{factura.get('periodo')} agotó sus tres reintentos.\n\n"
                f"Último error: {motivo}\n\n"
                "Queda pendiente de emisión manual."
            ),
        )

    def _avisar(self, *, asunto: str, cuerpo: str) -> None:
        """Fail-open: un buzon caido no puede tumbar el corte."""
        if self.alertas is None:
            return
        try:
            self.alertas.notificar_excepcion_facturacion(asunto=asunto, cuerpo=cuerpo)
        except Exception:  # noqa: BLE001
            logger.exception("excedente_alerta_fallida")
