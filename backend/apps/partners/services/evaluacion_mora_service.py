"""RF-PAC-003 y RF-PAC-007 — mora de excedente: avisos y suspension (CU-O55).

Ante mora, el sistema avisa antes de actuar
--------------------------------------------
Dos avisos previos (T-10 y T-5 por defecto) y suspension al superarse el limite
(15 dias). Nadie se lleva una suspension por sorpresa.

Que cuenta como mora AQUI (§ 15 D3) — y por que importa tanto
--------------------------------------------------------------
**Solo** las facturas `tipo='excedente_api'` con `estado_pago='Pendiente'` y
vencidas, resueltas por `Dim_Partner.idcliente -> Fact_Factura.id_cliente`
(esa tabla NO tiene `idpartner`).

`Fallida` queda fuera **a proposito**: es el disparador de la suspension de
suscripcion de `subscriptions-and-billing` (RF-SUSF-007). Si contase tambien
aqui, dos modulos suspenderian por la misma factura con umbrales distintos, y la
reactivacion se volveria ambigua — Suscripciones reactiva sola tras el cobro
(RN-SUSF-011) y aqui el sistema **nunca** reactiva solo (RN-PAC-009).

`En disputa` tambien queda fuera (RN-PAC-015): suspender por una factura que el
partner esta cuestionando lo castigaria por ejercer su derecho a reclamar.

La regularizacion no necesita logica de cancelacion
----------------------------------------------------
Si el partner paga, la factura deja de estar `Pendiente` y **desaparece de la
condicion de entrada**. El aviso pendiente sencillamente nunca se evalua
(RN-PAC-007). Es una propiedad del diseno, no una rama de codigo que mantener.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from django.conf import settings

from apps.partners.domain_constants import (
    CAMBIO_AVISO_PREVIO_SUSPENSION,
    EJECUTADO_POR_SISTEMA,
    ESTADO_ACCESO_ACTIVO,
    MORA_AVISOS_DIAS,
    MORA_LIMITE_DIAS,
)
from apps.partners.services.partner_notificacion_service import (
    PartnerNotificacionService,
)
from apps.partners.services.suspender_partner_service import (
    SuspenderPartnerError,
    SuspenderPartnerService,
)
from core.repositories.partners.historial_acceso_repository import (
    HistorialAccesoRepository,
)
from core.repositories.partners.partner_repository import PartnerRepository
from core.repositories.suscripciones.factura_repository import FacturaRepository

MS_POR_DIA = 86_400_000


class EvaluacionMoraService:
    def __init__(
        self,
        partners: PartnerRepository | None = None,
        facturas: FacturaRepository | None = None,
        historial: HistorialAccesoRepository | None = None,
        suspension: SuspenderPartnerService | None = None,
        notificacion: PartnerNotificacionService | None = None,
    ):
        self.partners = partners or PartnerRepository()
        self.facturas = facturas or FacturaRepository()
        self.historial = historial or HistorialAccesoRepository()
        self.suspension = suspension or SuspenderPartnerService()
        self.notificacion = notificacion or PartnerNotificacionService()

    # --- Parametros configurables (RNF-PAC-005) -----------------------------

    @property
    def limite_dias(self) -> int:
        return int(getattr(settings, "PARTNERS_MORA_LIMITE_DIAS", MORA_LIMITE_DIAS))

    @property
    def avisos_dias(self) -> tuple[int, ...]:
        crudo = getattr(settings, "PARTNERS_MORA_AVISOS_DIAS", MORA_AVISOS_DIAS)
        # De mayor a menor: T-10 antes que T-5.
        return tuple(sorted((int(d) for d in crudo), reverse=True))

    @staticmethod
    def _now_ms() -> int:
        return int(datetime.now(timezone.utc).timestamp() * 1000)

    @staticmethod
    def etiqueta_aviso(dias_antes: int) -> str:
        """`T-10`, `T-5`… Es lo que va en `motivo` y lo que evita duplicarlos."""
        return f"T-{int(dias_antes)}"

    # --- Evaluacion ----------------------------------------------------------

    def estado_de_mora(self, partner: dict[str, Any], *, ahora_ms: int | None = None) -> dict[str, Any]:
        """Dias de mora y factura que origina el ciclo. Sin efectos.

        La usan tanto el job como la consulta de estado y la cola del
        Administrador: la mora **no esta persistida** en ninguna columna
        (RN-PAC-012), se deriva cada vez que se pregunta.
        """
        ahora = int(ahora_ms if ahora_ms is not None else self._now_ms())
        vencidas = self.facturas.vencidas_impagadas_de_excedente(
            int(partner["idcliente"]), ahora_ms=ahora
        )
        if not vencidas:
            return {"en_mora": False, "dias_mora": 0, "factura": None}

        # El ciclo lo delimita la MAS ANTIGUA: es la que lleva mas tiempo sin
        # pagarse y la que decide si toca avisar o suspender.
        origen = vencidas[0]
        dias = (ahora - int(origen.get("fecha_vencimiento") or 0)) // MS_POR_DIA
        return {"en_mora": True, "dias_mora": int(dias), "factura": origen}

    def _aviso_que_toca(self, dias_mora: int) -> int | None:
        """El aviso mas avanzado alcanzado, o None si aun no toca ninguno.

        Con T-10 y T-5 sobre un limite de 15: a los 5 dias de mora faltan 10
        para el limite -> toca T-10. A los 10, faltan 5 -> toca T-5.
        """
        alcanzados = [d for d in self.avisos_dias if dias_mora >= self.limite_dias - d]
        return min(alcanzados) if alcanzados else None

    def evaluar_partner(self, partner: dict[str, Any], *, ahora_ms: int | None = None) -> dict[str, Any]:
        """Decide y ejecuta: avisar, suspender o no hacer nada."""
        idpartner = int(partner["idpartner"])
        mora = self.estado_de_mora(partner, ahora_ms=ahora_ms)

        if not mora["en_mora"]:
            return {"idpartner": idpartner, "accion": "sin_mora", "dias_mora": 0}

        dias = int(mora["dias_mora"])

        if dias >= self.limite_dias:
            try:
                self.suspension.suspender(
                    idpartner=idpartner,
                    motivo=(
                        f"Mora de {dias} días en facturas de excedente de API "
                        f"(límite {self.limite_dias})"
                    ),
                    automatica=True,
                )
            except SuspenderPartnerError as exc:
                # Ya suspendido: el job es diario e idempotente por naturaleza,
                # no es un error que deba detener la pasada.
                return {"idpartner": idpartner, "accion": "ya_suspendido", "detalle": exc.code}
            return {"idpartner": idpartner, "accion": "suspendido", "dias_mora": dias}

        aviso = self._aviso_que_toca(dias)
        if aviso is None:
            return {"idpartner": idpartner, "accion": "en_mora_sin_aviso", "dias_mora": dias}

        etiqueta = self.etiqueta_aviso(aviso)

        # RN-PAC-006 — no duplicar el mismo aviso dentro del mismo ciclo. El
        # ciclo empieza al vencer la factura que lo origina: se acota por ahi
        # para que una mora NUEVA vuelva a avisar desde cero.
        inicio_ciclo = int(mora["factura"].get("fecha_vencimiento") or 0)
        if self.historial.existe_evento(
            idpartner,
            CAMBIO_AVISO_PREVIO_SUSPENSION,
            motivo=etiqueta,
            desde_ms=inicio_ciclo,
        ):
            return {"idpartner": idpartner, "accion": "aviso_ya_enviado", "aviso": etiqueta}

        self.notificacion.notificar_aviso_mora(
            partner=partner,
            etiqueta=etiqueta,
            dias_mora=dias,
            limite_dias=self.limite_dias,
        )

        # El aviso NO cambia el estado del partner: sigue activo. Por eso
        # `estado_anterior` y `estado_nuevo` son iguales (RF-PAC-003).
        self.historial.registrar(
            idpartner=idpartner,
            tipo_cambio=CAMBIO_AVISO_PREVIO_SUSPENSION,
            ejecutado_por=EJECUTADO_POR_SISTEMA,
            motivo=etiqueta,
            estado_anterior=ESTADO_ACCESO_ACTIVO,
            estado_nuevo=ESTADO_ACCESO_ACTIVO,
        )
        return {"idpartner": idpartner, "accion": "avisado", "aviso": etiqueta, "dias_mora": dias}

    def evaluar_todos(self, *, ahora_ms: int | None = None) -> list[dict[str, Any]]:
        """Barrido diario sobre los partners ACTIVOS.

        Los suspendidos se saltan: ya no hay nada que cortarles, y el sistema no
        los reactiva aunque paguen (RN-PAC-009).
        """
        resultados = []
        cursor = None
        while True:
            pagina, cursor = self.partners.list(limit=200, cursor=cursor)
            for partner in pagina:
                if not partner.get("activo", False):
                    continue
                resultados.append(self.evaluar_partner(partner, ahora_ms=ahora_ms))
            if not cursor:
                break
        return resultados
