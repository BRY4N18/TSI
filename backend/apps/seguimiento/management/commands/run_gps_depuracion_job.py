"""Comando de gestión para el job de depuración de histórico GPS (RNF-SEG-004).

Uso:
  python manage.py run_gps_depuracion_job              # ejecuta una vez y termina
  python manage.py run_gps_depuracion_job --loop        # loop continuo (default cada 24h)
"""

from __future__ import annotations

import logging
import time

from django.core.management.base import BaseCommand

from apps.seguimiento.jobs.gps_depuracion_job import run_gps_depuracion_job

logger = logging.getLogger("tsi.seguimiento.job.gps_depuracion")

DEFAULT_INTERVAL_SECONDS = 24 * 60 * 60


class Command(BaseCommand):
    help = "Ejecuta el job de depuración de histórico GPS (una vez, o en loop continuo con --loop)"

    def add_arguments(self, parser):
        parser.add_argument("--loop", action="store_true", help="Ejecuta en loop continuo en vez de una sola vez")
        parser.add_argument("--interval", type=int, default=DEFAULT_INTERVAL_SECONDS)

    def handle(self, *args, **options):
        if not options["loop"]:
            resultado = run_gps_depuracion_job()
            self.stdout.write(self.style.SUCCESS(f"Job de depuración GPS ejecutado: {resultado}"))
            return

        interval = options["interval"]
        self.stdout.write(self.style.SUCCESS(f"Job de depuración GPS iniciado en loop continuo (cada {interval}s)"))
        while True:
            try:
                run_gps_depuracion_job()
            except Exception:
                logger.exception("Error ejecutando job de depuración GPS")
            time.sleep(interval)
