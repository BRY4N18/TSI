"""Dispara el job de alertas de cuota (CU-O53).

Pensado para una ejecucion periodica (cron/Airflow). Es idempotente: los avisos
no se duplican dentro del mismo periodo, asi que ejecutarlo de mas no molesta
al partner.

    python manage.py run_alertas_cuota_job
"""

from django.core.management.base import BaseCommand

from apps.partners.jobs.alertas_cuota_job import AlertasCuotaJob


class Command(BaseCommand):
    help = "Evalúa el consumo de cada partner contra su cupo y emite los avisos pendientes."

    def handle(self, *args, **options):
        resumen = AlertasCuotaJob().ejecutar()
        self.stdout.write(
            "Alertas de cuota — "
            f"evaluados: {resumen['evaluados']}, "
            f"avisados: {resumen['avisados']}, "
            f"sin aviso pendiente: {resumen['omitidos']}, "
            f"fallidos: {resumen['fallidos']}"
        )
        if resumen["fallidos"]:
            # El job es fail-open por partner, pero el operador debe enterarse.
            self.stderr.write(
                f"{resumen['fallidos']} partner(s) fallaron; ver el log tsi.partners.alertas_cuota"
            )
