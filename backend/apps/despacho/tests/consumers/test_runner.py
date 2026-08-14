"""B27 — el bucle que invoca los handlers registrados de Kafka."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from apps.despacho.consumers import get_consumer_handlers
from apps.despacho.consumers.runner import ConsumerRunner


class FakeConsumer:
    """Doble mínimo de KafkaConsumer: solo `poll` y `commit`."""

    def __init__(self, lotes: list[dict]):
        self._lotes = list(lotes)
        self.commits = 0

    def poll(self, timeout_ms=None):
        return self._lotes.pop(0) if self._lotes else {}

    def commit(self):
        self.commits += 1


def _registro(topic: str, value):
    return SimpleNamespace(topic=topic, value=value)


def _runner(handlers, lotes):
    consumidor = FakeConsumer(lotes)
    runner = ConsumerRunner(
        handlers,
        bootstrap_servers="fake:9092",
        consumer_factory=lambda: consumidor,
    )
    return runner, consumidor


@pytest.mark.service
class TestConsumerRunner:
    def test_entrega_cada_mensaje_al_handler_de_su_topic(self):
        # Arrange
        vistos: list[tuple[str, dict]] = []
        handlers = {
            "topic-a": lambda e: vistos.append(("a", e)),
            "topic-b": lambda e: vistos.append(("b", e)),
        }
        lotes = [{"p0": [_registro("topic-a", {"x": 1}), _registro("topic-b", {"x": 2})]}]
        runner, consumidor = _runner(handlers, lotes)

        # Act
        procesados = runner.run_once()

        # Assert
        assert procesados == 2
        assert vistos == [("a", {"x": 1}), ("b", {"x": 2})]
        assert consumidor.commits == 1

    def test_no_confirma_offset_si_no_hubo_mensajes(self):
        # Arrange
        runner, consumidor = _runner({"topic-a": lambda e: None}, [])

        # Act
        procesados = runner.run_once()

        # Assert
        assert procesados == 0
        assert consumidor.commits == 0

    def test_un_handler_que_falla_no_detiene_el_lote_ni_bloquea_la_particion(self):
        # Arrange — un mensaje envenenado no puede impedir que se despache el
        # siguiente accidente: se registra el fallo y se sigue.
        procesados_ok: list[dict] = []

        def explota(evento):
            raise RuntimeError("handler roto")

        handlers = {"topic-a": explota, "topic-b": procesados_ok.append}
        lotes = [{"p0": [_registro("topic-a", {"x": 1}), _registro("topic-b", {"x": 2})]}]
        runner, consumidor = _runner(handlers, lotes)

        # Act
        procesados = runner.run_once()

        # Assert
        assert procesados == 2
        assert procesados_ok == [{"x": 2}]
        assert consumidor.commits == 1

    def test_ignora_mensajes_de_topic_sin_handler_y_payloads_no_objeto(self):
        # Arrange
        vistos: list[dict] = []
        lotes = [
            {
                "p0": [
                    _registro("topic-desconocido", {"x": 1}),
                    _registro("topic-a", "no soy un objeto"),
                    _registro("topic-a", {"x": 3}),
                ]
            }
        ]
        runner, _ = _runner({"topic-a": vistos.append}, lotes)

        # Act
        runner.run_once()

        # Assert
        assert vistos == [{"x": 3}]

    def test_run_forever_termina_cuando_se_le_pide_parar(self):
        # Arrange
        handlers = {"topic-a": lambda e: None}
        runner, _ = _runner(handlers, [])
        runner.stop()

        # Act / Assert — no debe colgarse
        runner.run_forever()

    def test_exige_al_menos_un_handler_registrado(self):
        # Act / Assert
        with pytest.raises(ValueError):
            ConsumerRunner({}, bootstrap_servers="fake:9092")


@pytest.mark.service
class TestRegistroDeHandlers:
    def test_el_worker_cubre_los_dos_topics_que_dispara_el_despacho(self, settings):
        # Arrange — B27: los handlers estaban registrados y nadie los leía. El
        # worker consume exactamente lo que `DespachoConfig.ready()` inscribe.
        handlers = get_consumer_handlers()

        # Act
        runner = ConsumerRunner(handlers, bootstrap_servers="fake:9092")

        # Assert
        assert settings.KAFKA_TOPICS["accidente_estado"] in runner.topics
        assert settings.KAFKA_TOPICS["despacho_timeout"] in runner.topics
