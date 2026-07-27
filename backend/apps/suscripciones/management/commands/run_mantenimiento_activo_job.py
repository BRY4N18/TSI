from django.core.management.base import BaseCommand

from apps.suscripciones.jobs.mantenimiento_activo_job import run_mantenimiento_activo


class Command(BaseCommand):
    help = "Desactiva suscripciones Canceladas post fecha_fin."

    def handle(self, *args, **options):
        result = run_mantenimiento_activo()
        self.stdout.write(self.style.SUCCESS(str(result)))
