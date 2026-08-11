"""Fact_APIIntegracion — una fila por llamada ATENDIDA (RF-APM-004).

Es la base de todas las metricas y del calculo de excedente.

Tres reglas que gobiernan este archivo
--------------------------------------
1. **Append-only** (RNF-APM-005). No hay `update` ni `delete`, y no es una
   convencion: son metodos que no existen. El detalle es el respaldo de la
   tarificacion.
2. **`llamadas` vale siempre 1** (RN-APM-003). El agregado se calcula al
   consultar, nunca se acumula al escribir. Acumular obligaria a leer-modificar-
   escribir sobre una tabla append-only.
3. **Toda agregacion filtra por `entorno` y lleva `LIMIT` explicito**
   (RN-APM-001). Pinot aplica un `LIMIT 10` implicito y silencioso, y pruebas y
   produccion no se mezclan jamas, ni para el mismo partner.

Lo que NO se registra aqui
--------------------------
Una peticion rechazada con 429 no genera fila: no se atendio, no es consumo
facturable (§ 15 D2). Va a `Fact_LogLlamadaAPI` con su codigo.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from django.conf import settings

from core.pinot.client import PinotClient
from core.repositories.partners.kafka_writer import KafkaWriter

ENTORNOS_VALIDOS = ("Sandbox", "Producción")

UMBRAL_ERROR_HTTP = 400


class EntornoRequeridoError(Exception):
    """Se intento agregar sin filtrar por entorno.

    RN-APM-001 lo prohibe: mezclar pruebas y produccion falsearia tanto las
    metricas que ve el partner como el excedente que se le factura.
    """


class ApiIntegracionRepository:
    TOPIC = settings.KAFKA_TOPICS["api_integracion"]

    def __init__(self, pinot: PinotClient | None = None, kafka: KafkaWriter | None = None):
        self.pinot = pinot or PinotClient()
        self.kafka = kafka or KafkaWriter()

    @staticmethod
    def _now_ms() -> int:
        return int(datetime.now(timezone.utc).timestamp() * 1000)

    def _next_id(self) -> int:
        filas = self.pinot.query(
            "SELECT MAX(idapiintegracion) AS max_id FROM Fact_APIIntegracion LIMIT 1", {}
        )
        return int(filas[0]["max_id"] or 0) + 1 if filas else 1

    @staticmethod
    def _exigir_entorno(entorno: str | None) -> str:
        if entorno not in ENTORNOS_VALIDOS:
            raise EntornoRequeridoError(
                f"Toda agregacion debe filtrar por entorno (RN-APM-001). "
                f"Recibido {entorno!r}; esperado uno de {ENTORNOS_VALIDOS}"
            )
        return entorno

    # --- Escritura (solo INSERT) ---------------------------------------------

    def registrar(
        self,
        *,
        idpartner: int,
        idcliente: int,
        idservicio: int,
        idestadointegracion: int,
        entorno: str,
        codigohttp: int,
        latencia: float,
        fechahora: int | None = None,
    ) -> dict[str, Any]:
        """Registra UNA llamada atendida. Nunca actualiza una fila existente."""
        self._exigir_entorno(entorno)
        ahora = self._now_ms()
        fila = {
            "idapiintegracion": self._next_id(),
            "idpartner": int(idpartner),
            "idcliente": int(idcliente),
            "idservicio": int(idservicio),
            "idestadointegracion": int(idestadointegracion),
            "entorno": entorno,
            # Siempre 1: el agregado se calcula al consultar (RN-APM-003).
            "llamadas": 1,
            "errores": 1 if int(codigohttp) >= UMBRAL_ERROR_HTTP else 0,
            "latencia": float(latencia),
            "activo": True,
            "fechahora": fechahora if fechahora is not None else ahora,
            "fecha_actualizacion": ahora,
        }
        self.kafka.publish(self.TOPIC, fila)
        return fila

    # --- Agregaciones (siempre con entorno y LIMIT explicitos) ---------------

    def consumo_del_partner(
        self, idpartner: int, *, entorno: str, desde_ms: int, hasta_ms: int
    ) -> dict[str, Any]:
        """Llamadas, errores y latencia media del partner en la ventana dada."""
        self._exigir_entorno(entorno)
        filas = self.pinot.query(
            "SELECT SUM(llamadas) AS llamadas, SUM(errores) AS errores, "
            "AVG(latencia) AS latencia_media FROM Fact_APIIntegracion "
            "WHERE idpartner = %(idpartner)s AND entorno = %(entorno)s "
            "AND fechahora >= %(desde)s AND fechahora < %(hasta)s LIMIT 1",
            {
                "idpartner": idpartner,
                "entorno": entorno,
                "desde": desde_ms,
                "hasta": hasta_ms,
            },
        )
        if not filas:
            return {"llamadas": 0, "errores": 0, "latencia_media": 0.0}
        f = filas[0]
        return {
            "llamadas": int(f.get("llamadas") or 0),
            "errores": int(f.get("errores") or 0),
            "latencia_media": float(f.get("latencia_media") or 0.0),
        }

    def consumo_por_servicio(
        self, idpartner: int, *, entorno: str, desde_ms: int, hasta_ms: int, limit: int = 100
    ) -> list[dict[str, Any]]:
        """Desglose por servicio. `LIMIT` explicito, nunca implicito."""
        self._exigir_entorno(entorno)
        return self.pinot.query(
            "SELECT idservicio, SUM(llamadas) AS llamadas, SUM(errores) AS errores "
            "FROM Fact_APIIntegracion "
            "WHERE idpartner = %(idpartner)s AND entorno = %(entorno)s "
            "AND fechahora >= %(desde)s AND fechahora < %(hasta)s "
            "GROUP BY idservicio ORDER BY llamadas DESC LIMIT %(limit)s",
            {
                "idpartner": idpartner,
                "entorno": entorno,
                "desde": desde_ms,
                "hasta": hasta_ms,
                "limit": limit,
            },
        )

    def llamadas_del_periodo(
        self, idpartner: int, *, entorno: str, desde_ms: int, hasta_ms: int
    ) -> int:
        """Total de llamadas — la cifra que se compara contra el cupo (CU-O53)."""
        return self.consumo_del_partner(
            idpartner, entorno=entorno, desde_ms=desde_ms, hasta_ms=hasta_ms
        )["llamadas"]
