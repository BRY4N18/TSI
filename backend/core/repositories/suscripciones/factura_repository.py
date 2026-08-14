"""Fact_Factura repository — RF-SUSF-004/005 (seq RN-026)."""

from __future__ import annotations

import json
import re
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any
from zoneinfo import ZoneInfo

from django.conf import settings

from apps.partners.domain_constants import FACTURA_PENDIENTE, FACTURA_TIPO_EXCEDENTE
from core.pinot.client import PinotClient
from core.repositories.suscripciones.kafka_writer import KafkaWriter

TZ = ZoneInfo("America/Guayaquil")
_SEQ_RE = re.compile(r"^FAC-(\d{6})-(\d{8})$")


class FacturaRepository:
    TOPIC = settings.KAFKA_TOPICS["factura"]

    def __init__(self, pinot: PinotClient | None = None, kafka: KafkaWriter | None = None):
        self.pinot = pinot or PinotClient()
        self.kafka = kafka or KafkaWriter()

    def _now_ms(self) -> int:
        return int(datetime.now(timezone.utc).timestamp() * 1000)

    @classmethod
    def _hidratar(cls, row: dict[str, Any] | None) -> dict[str, Any] | None:
        """Devuelve `desglose_cargos` como lista de conceptos.

        En Pinot se guarda como JSON en una columna STRING (ver `_desglose_json`),
        pero quien la consume —la pantalla de facturas— la recorre como lista.
        """
        if not row or "desglose_cargos" not in row:
            return row
        valor = row["desglose_cargos"]
        if isinstance(valor, str):
            try:
                row = {**row, "desglose_cargos": json.loads(valor or "[]")}
            except json.JSONDecodeError:
                row = {**row, "desglose_cargos": []}
        return row

    def find_by_id(self, id_factura: str) -> dict[str, Any] | None:
        rows = self.pinot.query(
            "SELECT * FROM Fact_Factura WHERE id_factura = %(id)s",
            {"id": id_factura},
        )
        return self._hidratar(rows[0]) if rows else None

    def list_by_cliente(self, idcliente: int, *, limit: int = 20) -> list[dict[str, Any]]:
        rows = self.pinot.query(
            "SELECT * FROM Fact_Factura WHERE id_cliente = %(idcliente)s "
            "ORDER BY fecha_emision DESC LIMIT %(limit)s",
            {"idcliente": idcliente, "limit": int(limit)},
        )
        return [self._hidratar(r) for r in (rows or [])]

    def vencidas_impagadas_de_excedente(
        self, idcliente: int, *, ahora_ms: int | None = None, limit: int = 200
    ) -> list[dict[str, Any]]:
        """Facturas de excedente de API vencidas y sin pagar de un cliente.

        La usa la evaluacion de mora de #09 (§ 15 D3). Tres precisiones que NO
        son detalles de implementacion:

        1. **Se consulta por `id_cliente`.** `Fact_Factura` NO tiene `idpartner`:
           el puente es `Dim_Partner.idcliente`. Una consulta contra `idpartner`
           no fallaria, devolveria **cero morosos en silencio**.
        2. **Solo `estado_pago='Pendiente'`.** `Fallida` es el disparador de la
           suspension de suscripcion (RF-SUSF-007); contarla aqui haria que dos
           modulos suspendieran por la misma factura. `En disputa` se excluye
           porque el partner esta ejerciendo su derecho a reclamar (RN-PAC-015).
        3. **`limit` alto por defecto.** El de 20 de `list_by_cliente` es para
           una pantalla; un job que decide suspensiones no puede quedarse corto.

        Devuelve de la mas antigua a la mas reciente: la primera es la que
        origina el ciclo de mora.
        """
        ahora = int(ahora_ms if ahora_ms is not None else self._now_ms())
        rows = self.pinot.query(
            "SELECT * FROM Fact_Factura WHERE id_cliente = %(idcliente)s "
            "AND tipo = %(tipo)s AND estado_pago = %(estado)s "
            "AND fecha_vencimiento < %(ahora)s "
            "ORDER BY fecha_vencimiento ASC LIMIT %(limit)s",
            {
                "idcliente": int(idcliente),
                "tipo": FACTURA_TIPO_EXCEDENTE,
                "estado": FACTURA_PENDIENTE,
                "ahora": ahora,
                "limit": int(limit),
            },
        )
        # Segunda guarda en Python: si el doble de tests o una version de Pinot
        # ignorase alguno de los filtros, aqui no pasaria una factura que no toca.
        return [
            f
            for f in (rows or [])
            if str(f.get("tipo")) == FACTURA_TIPO_EXCEDENTE
            and str(f.get("estado_pago")) == FACTURA_PENDIENTE
            and int(f.get("fecha_vencimiento") or 0) < ahora
        ]

    def find_by_suscripcion_periodo(self, id_suscripcion: int, periodo: str) -> dict[str, Any] | None:
        rows = self.pinot.query(
            "SELECT * FROM Fact_Factura WHERE id_suscripcion = %(id_suscripcion)s "
            "AND periodo = %(periodo)s LIMIT 1",
            {"id_suscripcion": id_suscripcion, "periodo": periodo},
        )
        return rows[0] if rows else None

    def _facturas_del_periodo(self, periodo: str) -> list[dict[str, Any]]:
        """Acota el escaneo al período (RN-SUSF-026): numero_factura es único por periodo,
        así que nunca hace falta leer la tabla completa para calcular el siguiente seq."""
        rows = self.pinot.query(
            "SELECT numero_factura FROM Fact_Factura WHERE periodo = %(periodo)s",
            {"periodo": periodo},
        )
        return list(rows or [])

    def _next_seq(self, yyyymm: str, *, del_periodo: list[dict[str, Any]]) -> int:
        max_seq = 0
        for r in del_periodo:
            m = _SEQ_RE.match(str(r.get("numero_factura") or ""))
            if m and m.group(1) == yyyymm:
                max_seq = max(max_seq, int(m.group(2)))
        return max_seq + 1

    @staticmethod
    def _desglose_json(valor: Any) -> str:
        """`desglose_cargos` es una columna STRING de valor único, no un array.

        Publicar la lista de conceptos tal cual hacía que Pinot descartara la fila
        entera (`Cannot read single-value from Collection`): la factura respondía como
        creada y no existía. Se guarda como JSON, que es lo que ya tenían las filas
        sembradas.
        """
        if valor is None:
            return "[]"
        if isinstance(valor, str):
            return valor
        return json.dumps(valor, ensure_ascii=False)

    def create(self, data: dict[str, Any]) -> dict[str, Any]:
        now = datetime.now(TZ)
        periodo = data["periodo"]
        yyyymm = periodo.replace("-", "")
        del_periodo = self._facturas_del_periodo(periodo)
        seq = self._next_seq(yyyymm, del_periodo=del_periodo)
        numero = f"FAC-{yyyymm}-{seq:08d}"
        existing = {r.get("numero_factura") for r in del_periodo}
        while numero in existing:
            seq += 1
            numero = f"FAC-{yyyymm}-{seq:08d}"
        emision = now
        vencimiento = emision + timedelta(days=7)
        record = {
            "id_factura": str(uuid.uuid4()),
            "id_cliente": data["id_cliente"],
            "id_suscripcion": data["id_suscripcion"],
            "idmetodopago": data.get("idmetodopago"),
            "numero_factura": numero,
            "periodo": periodo,
            "estado_pago": "Pendiente",
            "desglose_cargos": self._desglose_json(data.get("desglose_cargos")),
            "monto_base": float(data["monto_base"]),
            "impuestos": 0.0,
            "monto_total": float(data["monto_base"]),
            "fecha_emision": int(emision.timestamp() * 1000),
            "fecha_vencimiento": int(vencimiento.timestamp() * 1000),
            "reintentos": 0,
            "resultado_ultimo_reintento": None,
            "es_nota_credito": False,
            "id_factura_original": None,
            "motivo_anulacion": None,
            "fecha_actualizacion": self._now_ms(),
        }
        self.kafka.publish(self.TOPIC, record)
        # Se publica el JSON, pero quien recibe la factura recién creada la trata igual
        # que una leída: con el desglose ya como lista.
        return self._hidratar(record)

    def update(self, id_factura: str, changes: dict[str, Any]) -> dict[str, Any] | None:
        current = self.find_by_id(id_factura)
        if not current:
            return None
        return self.update_from(current, changes)

    def update_from(
        self, current: dict[str, Any], changes: dict[str, Any]
    ) -> dict[str, Any]:
        """Republica la fila completa a partir de una copia ya en memoria.

        La tabla es upsert por clave primaria, así que hay que reenviar todas las
        columnas. Esta variante existe para cobrar una factura recién emitida: releerla
        por id contra Pinot devuelve vacío durante 5-15 s.
        """
        payload = {**current, **changes, "fecha_actualizacion": self._now_ms()}
        # La tabla es upsert y se republica la fila entera: si `current` viene ya
        # hidratado, el desglose volvería a salir como lista y Pinot descartaría la fila.
        payload["desglose_cargos"] = self._desglose_json(payload.get("desglose_cargos"))
        self.kafka.publish(self.TOPIC, payload)
        return self._hidratar(payload)
