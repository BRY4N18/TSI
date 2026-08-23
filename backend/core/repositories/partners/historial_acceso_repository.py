"""Fact_HistorialAccesoPartner repository — bitacora inmutable (RF-PON-010).

SOLO INSERT. Esta clase NO expone `update` ni `delete` a proposito: la
inmutabilidad de la bitacora no es una convencion que se recuerde, es una
capacidad que no existe (RN-PON-010).

Ademas de auditoria, es la fuente operativa de la reactivacion selectiva de
#09: las filas `desactivacion_por_cascada` son las que se restituyen.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from django.conf import settings

from apps.partners.domain_constants import (
    CAMBIO_DESACTIVACION_POR_CASCADA,
    CAMBIO_REACTIVACION,
    CAMBIO_SUSPENSION_AUTOMATICA,
    CAMBIO_SUSPENSION_MANUAL,
    SIN_CREDENCIAL,
    SIN_MOTIVO,
)
from core.pinot.client import PinotClient
from core.repositories.partners.kafka_writer import KafkaWriter
from core.pinot.secuencia import siguiente_id

_TIPOS_SUSPENSION = frozenset({CAMBIO_SUSPENSION_AUTOMATICA, CAMBIO_SUSPENSION_MANUAL})

# Eventos que cierran un ciclo de acceso hacia atras: al encontrarlos, lo que
# venga despues pertenece a una suspension anterior y NO debe restituirse.
_TIPOS_CIERRE_DE_CICLO = _TIPOS_SUSPENSION | {CAMBIO_REACTIVACION}


class HistorialAccesoRepository:
    TOPIC = settings.KAFKA_TOPICS["historial_acceso_partner"]

    def __init__(self, pinot: PinotClient | None = None, kafka: KafkaWriter | None = None):
        self.pinot = pinot or PinotClient()
        self.kafka = kafka or KafkaWriter()

    @staticmethod
    def _now_ms() -> int:
        return int(datetime.now(timezone.utc).timestamp() * 1000)

    def _next_id(self) -> int:
        return siguiente_id(self.pinot, "Fact_HistorialAccesoPartner", "idhistorial")

    # --- Lecturas -----------------------------------------------------------

    def list_by_partner(self, idpartner: int, *, limit: int = 200) -> list[dict[str, Any]]:
        return self.pinot.query(
            # Desempate por idhistorial: dos eventos del mismo flujo pueden caer
            # en el mismo milisegundo, y entonces `fecha_cambio` sola no basta
            # para saber cual es el ultimo.
            "SELECT * FROM Fact_HistorialAccesoPartner WHERE idpartner = %(idpartner)s "
            "ORDER BY fecha_cambio DESC, idhistorial DESC LIMIT %(limit)s",
            {"idpartner": idpartner, "limit": limit},
        )

    def ultimo_evento(self, idpartner: int) -> dict[str, Any] | None:
        eventos = self.list_by_partner(idpartner, limit=1)
        return eventos[0] if eventos else None

    def existe_evento(
        self,
        idpartner: int,
        tipo_cambio: str,
        *,
        motivo: str | None = None,
        desde_ms: int | None = None,
    ) -> bool:
        """Para las reglas de no duplicacion (avisos de vencimiento y de mora)."""
        for ev in self.list_by_partner(idpartner, limit=500):
            if ev.get("tipo_cambio") != tipo_cambio:
                continue
            if motivo is not None and ev.get("motivo") != motivo:
                continue
            if desde_ms is not None and int(ev.get("fecha_cambio", 0)) < desde_ms:
                continue
            return True
        return False

    def ultima_suspension(self, idpartner: int) -> dict[str, Any] | None:
        """El ultimo evento de suspension del partner (automatica o manual).

        Es el ancla temporal de la reactivacion selectiva: marca desde cuando
        cuentan las filas de cascada que hay que restituir (#09 § 15 D1).
        """
        for ev in self.list_by_partner(idpartner, limit=500):
            if ev.get("tipo_cambio") in _TIPOS_SUSPENSION:
                return ev
        return None

    def credenciales_de_la_ultima_cascada(self, idpartner: int) -> list[int]:
        """Los `idcredencial` que desactivo la ultima suspension.

        **Esta lista ES la reactivacion selectiva** (RN-PAC-011). Se recorre el
        historial de mas reciente a mas antiguo y se para en cuanto aparece una
        suspension ANTERIOR a la ultima: asi solo se devuelven las filas del
        ciclo vigente y no las de suspensiones pasadas.

        Una credencial que ya estaba inactiva cuando llego la suspension —porque
        el partner la revoco, o porque expiro— **no genero fila de cascada**, asi
        que no aparece aqui y no se restituye. La regla de seguridad se cumple
        POR CONSTRUCCION, no por una comprobacion aparte que alguien pudiera
        olvidar al refactorizar.

        El ciclo se delimita por POSICION, nunca por reloj
        --------------------------------------------------
        Una version anterior anclaba el corte en `fecha_cambio` del evento de
        suspension. Era incorrecto: las filas de cascada se escriben ANTES que
        ese evento, y si el milisegundo avanzaba entre medias quedaban "antes
        del corte" y se descartaban. El resultado era que la reactivacion **no
        restituia nada, en silencio** — el partner se quedaba sin credenciales y
        nada en el log lo delataba. Ocurria de forma intermitente, solo cuando la
        maquina iba lenta.

        Se recorre el historial de mas nuevo a mas viejo: primero el evento de
        suspension, despues sus filas de cascada, y se para en el limite del
        ciclo anterior (otra suspension o una reactivacion). Los empates de
        milisegundo ya no importan porque `list_by_partner` desempata por
        `idhistorial`, que es monotono.
        """
        historial = self.list_by_partner(idpartner, limit=500)

        inicio = next(
            (
                i
                for i, ev in enumerate(historial)
                if ev.get("tipo_cambio") in _TIPOS_SUSPENSION
            ),
            None,
        )
        if inicio is None:
            return []

        ids: list[int] = []
        for ev in historial[inicio + 1:]:
            tipo = ev.get("tipo_cambio")
            if tipo in _TIPOS_CIERRE_DE_CICLO:
                # Empieza el ciclo anterior: lo suyo ya no se restituye.
                break
            if tipo != CAMBIO_DESACTIVACION_POR_CASCADA:
                continue
            idcredencial = int(ev.get("idcredencial", SIN_CREDENCIAL))
            if idcredencial != SIN_CREDENCIAL and idcredencial not in ids:
                ids.append(idcredencial)
        return ids

    # --- Escritura (solo INSERT) --------------------------------------------

    def registrar(
        self,
        *,
        idpartner: int,
        tipo_cambio: str,
        ejecutado_por: str,
        estado_nuevo: str,
        estado_anterior: str = SIN_MOTIVO,
        motivo: str = SIN_MOTIVO,
        idcredencial: int = SIN_CREDENCIAL,
    ) -> dict[str, Any]:
        """Inserta un evento. Nunca actualiza: cada evento es una fila nueva.

        `idcredencial` vale el centinela -1 cuando el evento es sobre el partner
        en general (registro, plan, solicitud, aprobacion, rechazo) y lleva el id
        real cuando afecta a una credencial concreta (emision, expiracion).
        """
        fila = {
            "idhistorial": self._next_id(),
            "idpartner": int(idpartner),
            "idcredencial": int(idcredencial),
            "tipo_cambio": tipo_cambio,
            "ejecutado_por": ejecutado_por,
            "motivo": motivo,
            "estado_anterior": estado_anterior,
            "estado_nuevo": estado_nuevo,
            "fecha_cambio": self._now_ms(),
            "fecha_actualizacion": self._now_ms(),
        }
        self.kafka.publish(self.TOPIC, fila)
        return fila
