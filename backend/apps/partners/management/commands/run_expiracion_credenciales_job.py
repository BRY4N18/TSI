"""Comando de gestión del job RF-PON-006 (expiración de credenciales de pruebas).

Uso:
  python manage.py run_expiracion_credenciales_job            # loop continuo (1 h)
  python manage.py run_expiracion_credenciales_job --once     # una pasada (cron externo)
  python manage.py run_expiracion_credenciales_job --interval 600
"""

from __future__ import annotations

import logging
import time

from django.core.management.base import BaseCommand

from apps.partners.jobs.expiracion_credenciales_job import (
    run_expiracion_credenciales_job,
)

logger = logging.getLogger("tsi.partners.job.expiracion_credenciales")
# La vigencia se mide en dias, asi que una pasada por hora sobra.
DEFAULT_INTERVAL_SECONDS = 3600


class Command(BaseCommand):
    help = "Ejecuta el job RF-PON-006 de expiración de credenciales (una vez o en loop)"

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
            help=f"Segundos entre pasadas en loop continuo (default: {DEFAULT_INTERVAL_SECONDS})",
        )

    def handle(self, *args, **options):
        if options["once"]:
            resultado = run_expiracion_credenciales_job()
            self.stdout.write(self.style.SUCCESS(f"Job RF-PON-006 ejecutado: {resultado}"))
            return

        interval = options["interval"]
        self.stdout.write(
            self.style.SUCCESS(f"Job RF-PON-006 iniciado en loop continuo (cada {interval}s)")
        )
        while True:
            try:
                run_expiracion_credenciales_job()
            except Exception:
                logger.exception("Error ejecutando job RF-PON-006 de expiración de credenciales")
            time.sleep(interval)
