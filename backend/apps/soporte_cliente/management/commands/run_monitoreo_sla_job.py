"""Comando de gestión para el job CU-O96 (RNF-TIC-001): monitoreo periódico de SLA.

Uso:
  python manage.py run_monitoreo_sla_job              # loop continuo cada 60s
  python manage.py run_monitoreo_sla_job --once        # una sola pasada (para cron externo)
  python manage.py run_monitoreo_sla_job --interval 30 # cambiar el intervalo del loop
"""

from __future__ import annotations

import logging
import time

from django.core.management.base import BaseCommand

from apps.soporte_cliente.jobs.monitoreo_sla_job import run_monitoreo_sla_job

logger = logging.getLogger("tsi.soporte_cliente.job.monitoreo_sla")
DEFAULT_INTERVAL_SECONDS = 60


class Command(BaseCommand):
    help = "Ejecuta el job CU-O96 de monitoreo de SLA (una vez o en loop continuo)"

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
            help="Segundos entre pasadas cuando se ejecuta en loop continuo (default: 60)",
        )

    def handle(self, *args, **options):
        once = options["once"]
        interval = options["interval"]
        if once:
            resultado = run_monitoreo_sla_job()
            self.stdout.write(self.style.SUCCESS(f"Job CU-O96 ejecutado: {resultado}"))
            return
        self.stdout.write(self.style.SUCCESS(f"Job CU-O96 iniciado en loop continuo (cada {interval}s)"))
        while True:
            try:
                run_monitoreo_sla_job()
            except Exception:
                logger.exception("Error ejecutando job CU-O96 de monitoreo de SLA")
            time.sleep(interval)
