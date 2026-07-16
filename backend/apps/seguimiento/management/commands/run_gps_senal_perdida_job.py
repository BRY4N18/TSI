"""Comando de gestión para el job O37 (RF-SEG-008): detección de señal GPS perdida.

Uso:
  python manage.py run_gps_senal_perdida_job              # loop continuo cada 30s
  python manage.py run_gps_senal_perdida_job --once        # una sola pasada (para cron externo)
"""

from __future__ import annotations

import logging
import time

from django.core.management.base import BaseCommand

from apps.seguimiento.jobs.gps_senal_perdida_job import run_gps_senal_perdida_job

logger = logging.getLogger("tsi.seguimiento.job.gps_senal_perdida")

DEFAULT_INTERVAL_SECONDS = 30


class Command(BaseCommand):
    help = "Ejecuta el job O37 de detección de señal GPS perdida (una vez o en loop continuo)"

    def add_arguments(self, parser):
        parser.add_argument("--once", action="store_true")
        parser.add_argument("--interval", type=int, default=DEFAULT_INTERVAL_SECONDS)

    def handle(self, *args, **options):
        once = options["once"]
        interval = options["interval"]

        if once:
            resultado = run_gps_senal_perdida_job()
            self.stdout.write(self.style.SUCCESS(f"Job O37 ejecutado: {resultado['alertas_generadas']} alerta(s)"))
            return

        self.stdout.write(self.style.SUCCESS(f"Job O37 iniciado en loop continuo (cada {interval}s)"))
        while True:
            try:
                run_gps_senal_perdida_job()
            except Exception:
                logger.exception("Error ejecutando job O37 de señal GPS perdida")
            time.sleep(interval)
