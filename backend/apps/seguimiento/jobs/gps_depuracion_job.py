"""Job de reporte de retención GPS — no borra nada (decisión 2026-08-08)."""

from apps.seguimiento.services.gps_depuracion_service import GpsDepuracionService


def run_gps_depuracion_job() -> dict:
    return GpsDepuracionService().depurar()
