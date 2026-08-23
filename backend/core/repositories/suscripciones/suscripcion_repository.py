"""Fact_Suscripcion repository canónico — lectura/escritura Kafka (Title Case)."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from zoneinfo import ZoneInfo

from dateutil.relativedelta import relativedelta
from django.conf import settings

from core.pinot.client import PinotClient
from core.repositories.suscripciones.kafka_writer import KafkaWriter
from core.pinot.secuencia import siguiente_id

TZ = ZoneInfo("America/Guayaquil")
ESTADO_CANCELADA = "Cancelada"
ESTADOS = frozenset({"Activa", "Suspendida", ESTADO_CANCELADA})


class SuscripcionRepository:
    TOPIC = settings.KAFKA_TOPICS["suscripcion"]

    def __init__(self, pinot: PinotClient | None = None, kafka: KafkaWriter | None = None):
        self.pinot = pinot or PinotClient()
        self.kafka = kafka or KafkaWriter()

    def _now_ms(self) -> int:
        return int(datetime.now(timezone.utc).timestamp() * 1000)

    def _next_id(self) -> int:
        return siguiente_id(self.pinot, "Fact_Suscripcion", "id_suscripcion")

    @staticmethod
    def add_calendar_month(dt: datetime) -> datetime:
        return dt + relativedelta(months=1)

    @staticmethod
    def add_cycle(dt: datetime, periodicidad: str | None) -> datetime:
        """Avanza un ciclo de facturación según Dim_Plan.periodicidad (SRS §3.3.1: 'nombre, nivel, precio, periodicidad y límites').

        Mensual -> +1 mes calendario (default si el plan no trae periodicidad, por compatibilidad con datos históricos).
        Anual -> +1 año calendario.
        """
        if periodicidad == "Anual":
            return dt + relativedelta(years=1)
        return dt + relativedelta(months=1)

    def find_by_id(self, id_suscripcion: int) -> dict[str, Any] | None:
        rows = self.pinot.query(
            "SELECT * FROM Fact_Suscripcion WHERE id_suscripcion = %(id)s",
            {"id": id_suscripcion},
        )
        return rows[0] if rows else None

    def find_activa_by_cliente(self, idcliente: int) -> dict[str, Any] | None:
        # El filtro va en SQL y el LIMIT es explícito. Sin `LIMIT`, Pinot recorta a 10
        # filas de la tabla entera antes de filtrar: en cuanto haya suscripciones de
        # once clientes, a algunos les responde "Sin suscripción activa" y se quedan
        # sin plan, sin factura y sin acceso, sin ningún error de por medio.
        #
        # Devuelve también las Suspendidas: `activo` sigue en true y hay flujos que las
        # necesitan (regularizar la mora, mostrar el estado). Quien exija que esté
        # Activa debe comprobar `estado` — lo hace `CambioPlanService.solicitar()`.
        rows = self.pinot.query(
            "SELECT * FROM Fact_Suscripcion WHERE idcliente = %(idcliente)s "
            "AND activo = true ORDER BY fecha_inicio DESC LIMIT 100",
            {"idcliente": idcliente},
        )
        return rows[0] if rows else None

    def list_elegibles_facturacion(self) -> list[dict[str, Any]]:
        rows = list(self.pinot.query("SELECT * FROM Fact_Suscripcion", {}) or [])
        return [r for r in rows if r.get("activo") and r.get("estado") == "Activa"]

    def list_elegibles_renovacion(self, *, now: datetime | None = None) -> list[dict[str, Any]]:
        now = now or datetime.now(TZ)
        out = []
        for r in self.list_elegibles_facturacion():
            if not r.get("renovacionautomatica"):
                continue
            fecha_fin = r.get("fecha_fin")
            if fecha_fin is None:
                continue
            # Accept ms epoch or ISO
            if isinstance(fecha_fin, (int, float)):
                fin_dt = datetime.fromtimestamp(fecha_fin / 1000, tz=TZ)
            else:
                fin_dt = datetime.fromisoformat(str(fecha_fin).replace("Z", "+00:00")).astimezone(TZ)
            if fin_dt <= now:
                out.append(r)
        return out

    def create(self, data: dict[str, Any]) -> dict[str, Any]:
        now = datetime.now(TZ)
        periodicidad = data.get("periodicidad") or "Mensual"
        fecha_fin = self.add_cycle(now, periodicidad)
        record = {
            "id_suscripcion": self._next_id(),
            "idcliente": data["idcliente"],
            "idplan": data["idplan"],
            "precio": float(data["precio"]),
            "periodicidad": periodicidad,
            # Congelados al alta/cambio de plan (mismo patrón que precio, RN-SUSF-006):
            # un cambio posterior del plan en Dim_Plan no debe alterar retroactivamente
            # qué severidades atiende una suscripción ya contratada (R-04 del SRS).
            "nivel": data.get("nivel"),
            "severidades_desbloqueadas": data.get("severidades_desbloqueadas", "[]"),
            "carga_lote_habilitada": bool(data.get("carga_lote_habilitada", False)),
            "estado": "Activa",
            "activo": True,
            "renovacionautomatica": bool(data.get("renovacionautomatica", True)),
            "motivocancelacion": None,
            "fechacancelacion": None,
            "fecha_inicio": int(now.timestamp() * 1000),
            "fecha_fin": int(fecha_fin.timestamp() * 1000),
            "fecha_actualizacion": self._now_ms(),
        }
        self.kafka.publish(self.TOPIC, record)
        return record

    def update(self, id_suscripcion: int, changes: dict[str, Any]) -> dict[str, Any] | None:
        current = self.find_by_id(id_suscripcion)
        if not current:
            return None
        if "estado" in changes and changes["estado"] not in ESTADOS:
            raise ValueError(f"estado inválido: {changes['estado']}")
        payload = {**current, **changes, "fecha_actualizacion": self._now_ms()}
        payload = _coherente(payload, cambios=changes)
        self.kafka.publish(self.TOPIC, payload)
        return payload

    def cancelar(
        self,
        id_suscripcion: int,
        *,
        motivocancelacion: str = "",
    ) -> dict[str, Any] | None:
        """Marca Cancelada manteniendo activo=true hasta fecha_fin (RN-017 / RF-SUSF-009)."""
        current = self.find_by_id(id_suscripcion)
        if not current:
            return None
        return self.update(
            id_suscripcion,
            {
                "estado": "Cancelada",
                "motivocancelacion": motivocancelacion or None,
                "fechacancelacion": self._now_ms(),
                # activo permanece True hasta job de mantenimiento post fecha_fin
                "activo": True,
                "renovacionautomatica": False,
            },
        )


# ── Invariantes al escribir (decisión #44) ───────────────────────────────────

#: Las tres formas de «sin motivo» que llegaron a convivir en el origen: nulo,
#: cadena vacía y la cadena literal `'null'`. El modelo analítico las unificaba a
#: ausencia **al leer**; unificarlas también al escribir evita que la cuarta
#: aparezca el día que alguien añada otra.
SIN_MOTIVO = ("", "null", "None")


def _sin_motivo(valor: Any) -> str | None:
    if valor is None:
        return None
    texto = str(valor).strip()
    return None if texto in SIN_MOTIVO else texto


def _coherente(payload: dict[str, Any], *, cambios: dict[str, Any]) -> dict[str, Any]:
    """Impide escribir las incoherencias que el modelo analítico ya sorteaba.

    ⚠️ **Tres de los cinco defectos de la decisión #44 se atajan aquí**, en el
    único punto por el que pasa todo cambio de estado. El modelo los rodeaba al
    leer —`motivo_cancelacion` solo si canceló, `vigencia_inconsistente`, motivo
    unificado a ausente— y eso sigue estando bien: lo que faltaba era dejar de
    producirlos.

    ⛔ **No se toca `activo`.** Una `Cancelada` con `activo = true` **no** es un
    defecto: RN-017 mantiene la suscripción activa hasta `fecha_fin` para que el
    cliente use lo que pagó. El modelo lo sabe y por eso `estado_derivado` no
    mira `activo`. «Corregirlo» aquí rompería una regla de negocio.
    """
    salida = dict(payload)

    # 1. Motivo de cancelación sin cancelación. El origen llegó a tener una
    #    `Activa` con motivo `'prueba fin de ciclo'`: quien leyera el motivo sin
    #    mirar el estado la contaría como baja.
    if salida.get("estado") != ESTADO_CANCELADA:
        salida["motivocancelacion"] = None
        salida["fechacancelacion"] = None
    else:
        salida["motivocancelacion"] = _sin_motivo(salida.get("motivocancelacion"))

    # 2. Vigencia invertida. Se valida **solo si el cambio toca las fechas**: una
    #    fila histórica ya invertida no puede bloquear una suspensión o un cobro
    #    —el origen sigue cobrándola y descartarla perdería un ingreso real—,
    #    pero tampoco hay motivo para dejar escribir una nueva.
    if "fecha_inicio" in cambios or "fecha_fin" in cambios:
        inicio, fin = salida.get("fecha_inicio"), salida.get("fecha_fin")
        if isinstance(inicio, int) and isinstance(fin, int) and 0 < fin < inicio:
            raise ValueError(
                "vigencia invertida: fecha_fin es anterior a fecha_inicio "
                f"({fin} < {inicio})"
            )

    return salida
