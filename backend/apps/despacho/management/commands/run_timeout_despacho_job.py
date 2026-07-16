"""Comando de gestión para el job O35 (RF-DES-005): escaneo periódico de timeouts de despacho.

Uso:
  python manage.py run_timeout_despacho_job              # loop continuo cada 30s
  python manage.py run_timeout_despacho_job --once        # una sola pasada (para cron externo)
  python manage.py run_timeout_despacho_job --interval 15 # cambiar el intervalo del loop
"""

from __future__ import annotations

import logging
import time

from django.core.management.base import BaseCommand

from apps.despacho.jobs.timeout_despacho_job import run_timeout_despacho_job

logger = logging.getLogger("tsi.despacho.job.timeout")

DEFAULT_INTERVAL_SECONDS = 30


class Command(BaseCommand):
    help = "Ejecuta el job O35 de escaneo de despachos en timeout (una vez o en loop continuo)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--once",
            action="store_true",
            help="Ejecuta una sola pasada y termina (para invocación vía cron externo)",
        )
        parser.add_argument(
            "--interval",
            type=int,
            default=DEFAULT_INTERVAL_SECONDS,
            help="Segundos entre pasadas cuando se ejecuta en loop continuo (default: 30)",
        )

    def handle(self, *args, **options):
        once = options["once"]
        interval = options["interval"]

        if once:
            eventos = run_timeout_despacho_job()
            self.stdout.write(self.style.SUCCESS(f"Job O35 ejecutado: {len(eventos)} evento(s) timeout"))
            return

        self.stdout.write(self.style.SUCCESS(f"Job O35 iniciado en loop continuo (cada {interval}s)"))
        while True:
            try:
                run_timeout_despacho_job()
            except Exception:
                logger.exception("Error ejecutando job O35 de timeout de despacho")
            time.sleep(interval)
