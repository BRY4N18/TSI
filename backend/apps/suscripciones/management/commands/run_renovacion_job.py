from django.core.management.base import BaseCommand

from apps.suscripciones.jobs.renovacion_job import run_renovacion


class Command(BaseCommand):
    help = "Ejecuta renovación automática (RF-SUSF-008)."

    def handle(self, *args, **options):
        result = run_renovacion()
        self.stdout.write(self.style.SUCCESS(str(result)))
