from django.core.management.base import BaseCommand

from apps.suscripciones.jobs.facturacion_mensual_job import run_facturacion_mensual


class Command(BaseCommand):
    help = "Ejecuta facturación mensual (RF-SUSF-004)."

    def handle(self, *args, **options):
        result = run_facturacion_mensual()
        self.stdout.write(self.style.SUCCESS(str(result)))
