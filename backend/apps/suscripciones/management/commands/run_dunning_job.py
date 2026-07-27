from django.core.management.base import BaseCommand

from apps.suscripciones.jobs.dunning_job import run_dunning


class Command(BaseCommand):
    help = "Ejecuta dunning D+3/D+5 (RF-SUSF-005)."

    def handle(self, *args, **options):
        result = run_dunning()
        self.stdout.write(self.style.SUCCESS(str(result)))
