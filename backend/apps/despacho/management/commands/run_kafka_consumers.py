"""Worker de consumo de Kafka del despacho (B27).

Sin este proceso, los handlers que `DespachoConfig.ready()` inscribe con
`register_consumer` quedan en un diccionario que nadie lee: la asignación
automática al reportarse un accidente y la reasignación al vencer un despacho
nunca se ejecutan.

Uso:
  python manage.py run_kafka_consumers            # bucle continuo (worker)
  python manage.py run_kafka_consumers --once     # un solo sondeo (diagnóstico)
  python manage.py run_kafka_consumers --group-id otro
"""

from __future__ import annotations

import logging
import signal

from django.core.management.base import BaseCommand

from apps.despacho.consumers import get_consumer_handlers
from apps.despacho.consumers.runner import (
    DEFAULT_GROUP_ID,
    DEFAULT_POLL_TIMEOUT_MS,
    ConsumerRunner,
)

logger = logging.getLogger("tsi.despacho.consumer.runner")


class Command(BaseCommand):
    help = "Consume los topics de Kafka del despacho e invoca sus handlers registrados"

    def add_arguments(self, parser):
        parser.add_argument(
            "--once",
            action="store_true",
            help="Sondea una sola vez y termina (diagnóstico, no despliegue)",
        )
        parser.add_argument(
            "--group-id",
            default=DEFAULT_GROUP_ID,
            help=f"Grupo de consumo de Kafka (default: {DEFAULT_GROUP_ID})",
        )
        parser.add_argument(
            "--poll-timeout-ms",
            type=int,
            default=DEFAULT_POLL_TIMEOUT_MS,
            help=f"Espera máxima por sondeo (default: {DEFAULT_POLL_TIMEOUT_MS})",
        )

    def handle(self, *args, **options):
        runner = ConsumerRunner(
            get_consumer_handlers(),
            group_id=options["group_id"],
            poll_timeout_ms=options["poll_timeout_ms"],
        )

        if options["once"]:
            procesados = runner.run_once()
            self.stdout.write(
                self.style.SUCCESS(f"Sondeo único: {procesados} mensaje(s) procesado(s)")
            )
            return

        for sig in (signal.SIGTERM, signal.SIGINT):
            signal.signal(sig, lambda *_: runner.stop())

        self.stdout.write(
            self.style.SUCCESS(
                "Worker de despacho escuchando: " + ", ".join(runner.topics)
            )
        )
        runner.run_forever()
        self.stdout.write(self.style.SUCCESS("Worker de despacho detenido"))
