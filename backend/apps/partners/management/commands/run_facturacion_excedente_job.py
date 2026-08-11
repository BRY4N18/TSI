"""Dispara el corte y facturacion del excedente (CU-O54).

**Ejecucion HORARIA**, no mensual. Los escalones de reintento son de 1 h, 6 h y
24 h; con una ejecucion mensual el primer reintento llegaria treinta dias tarde.
Es idempotente: la no duplicacion vive en el servicio, asi que correrlo de mas
no cobra de mas.

Por defecto corta el **mes anterior**, que es lo que tiene sentido en una
ejecucion automatica: el mes en curso todavia esta abierto.

    python manage.py run_facturacion_excedente_job
    python manage.py run_facturacion_excedente_job --anio 2026 --mes 7
"""

from datetime import datetime, timezone

from django.core.management.base import BaseCommand

from apps.partners.jobs.facturacion_excedente_job import FacturacionExcedenteJob


def _mes_anterior() -> tuple[int, int]:
    hoy = datetime.now(timezone.utc)
    return (hoy.year - 1, 12) if hoy.month == 1 else (hoy.year, hoy.month - 1)


class Command(BaseCommand):
    help = "Corta el período, factura el excedente y procesa los reintentos vencidos."

    def add_arguments(self, parser):
        anio, mes = _mes_anterior()
        parser.add_argument("--anio", type=int, default=anio)
        parser.add_argument("--mes", type=int, default=mes)

    def handle(self, *args, **options):
        anio, mes = options["anio"], options["mes"]
        if not 1 <= mes <= 12:
            self.stderr.write("mes debe estar entre 1 y 12")
            return

        r = FacturacionExcedenteJob().ejecutar(anio=anio, mes=mes)
        self.stdout.write(
            f"Corte {anio:04d}-{mes:02d} — "
            f"evaluados: {r['evaluados']}, emitidas: {r['emitidas']}, "
            f"ya emitidas: {r['ya_emitidas']}, omitidas: {r['omitidas']}, "
            f"reintentos: {r['reintentos_procesados']}"
        )
        # Estas dos exigen intervencion humana: no se pueden quedar en un log.
        if r["no_tarificables"]:
            self.stderr.write(
                f"{r['no_tarificables']} partner(s) con excedente y SIN tarifa "
                "configurada: no se les facturó. Configura el precio del plan."
            )
        if r["fallidas"]:
            self.stderr.write(
                f"{r['fallidas']} corte(s) fallaron; se reintentarán según RF-APM-013"
            )
