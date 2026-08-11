"""Dispara la evaluacion diaria de mora de excedente de API (CU-O55).

Pensado para una ejecucion diaria (cron/Airflow). Es idempotente: los avisos no
se duplican dentro del mismo ciclo de mora y suspender a un partner ya
suspendido no hace nada.

**Este comando puede suspender el acceso de un partner.** Ejecutarlo de mas es
inocuo; no ejecutarlo durante dias significa que nadie recibe sus avisos previos
y que un moroso sigue consumiendo.

    python manage.py run_evaluacion_mora_job
"""

from django.core.management.base import BaseCommand

from apps.partners.jobs.evaluacion_mora_job import EvaluacionMoraJob


class Command(BaseCommand):
    help = "Evalúa la mora de excedente de API: avisa (T-10, T-5) y suspende al superarse el límite."

    def handle(self, *args, **options):
        resumen = EvaluacionMoraJob().ejecutar()
        self.stdout.write(
            "Evaluación de mora — "
            f"evaluados: {resumen['evaluados']}, "
            f"avisados: {resumen['avisados']}, "
            f"suspendidos: {resumen['suspendidos']}, "
            f"sin mora: {resumen['sin_mora']}, "
            f"fallidos: {resumen['fallidos']}"
        )
        if resumen["suspendidos"]:
            # No es un error, pero es la clase de efecto que el operador debe
            # ver en la salida sin tener que abrir el log.
            self.stdout.write(
                f"{resumen['suspendidos']} partner(s) suspendidos por mora. "
                "La reactivación requiere acción manual de un Administrador."
            )
        if resumen["fallidos"]:
            self.stderr.write(
                f"{resumen['fallidos']} partner(s) fallaron; "
                "ver el log tsi.partners.evaluacion_mora"
            )
