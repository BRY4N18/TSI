"""Bucle de consumo de Kafka para los handlers registrados del despacho.

El registro de `apps.despacho.consumers` solo guarda handlers en memoria; este
runner es el proceso que los invoca. Corre como worker aparte (ver
`docker/accidentes.yml`, servicio `despacho-worker`), no dentro de `runserver`:
un fallo del bucle no debe llevarse por delante la API, y el autoreloader de
Django duplicaría el consumidor.

Decisiones de entrega, deliberadas y documentadas en el changelog (B27):

- **`auto_offset_reset="latest"`.** Al arrancar por primera vez el worker NO
  reprocesa el historial del topic: reprocesarlo intentaría despachar todos los
  accidentes viejos del sistema.
- **Confirmación de offset manual, después de procesar** (*at-least-once*). Si
  el worker muere a mitad de un lote, ese lote se reprocesa; nunca se pierde.
- **Un handler que falla no detiene el bucle ni bloquea la partición.** Se
  registra la excepción y el mensaje se da por consumido. La alternativa
  —reintentar indefinidamente— dejaría un mensaje envenenado bloqueando todos
  los despachos siguientes, que en este departamento es peor.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Callable

logger = logging.getLogger("tsi.despacho.consumer.runner")

DEFAULT_GROUP_ID = "tsi-despacho-workers"
DEFAULT_POLL_TIMEOUT_MS = 1000


class ConsumerRunner:
    def __init__(
        self,
        handlers: dict[str, Callable[[dict[str, Any]], Any]],
        *,
        bootstrap_servers: str | None = None,
        group_id: str = DEFAULT_GROUP_ID,
        poll_timeout_ms: int = DEFAULT_POLL_TIMEOUT_MS,
        consumer_factory: Callable[[], Any] | None = None,
    ):
        if not handlers:
            raise ValueError("No hay handlers registrados que consumir")
        self.handlers = handlers
        self.group_id = group_id
        self.poll_timeout_ms = poll_timeout_ms
        self._consumer_factory = consumer_factory
        self._consumer: Any | None = None
        self._stop = False
        if bootstrap_servers is None:
            from django.conf import settings

            bootstrap_servers = settings.KAFKA_BOOTSTRAP_SERVERS
        self.bootstrap_servers = bootstrap_servers

    @property
    def topics(self) -> list[str]:
        return sorted(self.handlers)

    def stop(self) -> None:
        self._stop = True

    def _build_consumer(self) -> Any:
        if self._consumer_factory is not None:
            return self._consumer_factory()
        from kafka import KafkaConsumer

        return KafkaConsumer(
            *self.topics,
            bootstrap_servers=self.bootstrap_servers,
            group_id=self.group_id,
            enable_auto_commit=False,
            auto_offset_reset="latest",
            value_deserializer=lambda raw: json.loads(raw.decode("utf-8")),
        )

    @property
    def consumer(self) -> Any:
        if self._consumer is None:
            self._consumer = self._build_consumer()
        return self._consumer

    def run_once(self) -> int:
        """Sondea una vez, procesa lo que haya y confirma el offset. Devuelve
        cuántos mensajes se procesaron."""
        lotes = self.consumer.poll(timeout_ms=self.poll_timeout_ms)
        procesados = 0
        for registros in lotes.values():
            for registro in registros:
                self._despachar(registro)
                procesados += 1
        if procesados:
            self.consumer.commit()
        return procesados

    def run_forever(self) -> None:
        logger.info(
            "worker de despacho escuchando %s (group_id=%s)",
            ", ".join(self.topics),
            self.group_id,
        )
        while not self._stop:
            try:
                self.run_once()
            except Exception:  # noqa: BLE001 — el bucle no puede morir
                logger.exception("error sondeando Kafka; se reintenta")

    def _despachar(self, registro: Any) -> None:
        handler = self.handlers.get(registro.topic)
        if handler is None:
            logger.warning("mensaje de topic sin handler: %s", registro.topic)
            return
        evento = registro.value
        if not isinstance(evento, dict):
            logger.warning("mensaje descartado, no es un objeto: %r", evento)
            return
        try:
            resultado = handler(evento)
        except Exception:  # noqa: BLE001 — un mensaje malo no bloquea la partición
            logger.exception(
                "handler de %s falló procesando %s", registro.topic, evento
            )
            return
        logger.debug("handler de %s devolvió %s", registro.topic, resultado)
