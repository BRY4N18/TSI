"""Job depuración GPS histórico."""

from apps.seguimiento.services.gps_depuracion_service import GpsDepuracionService


def run_gps_depuracion_job() -> dict:
    return GpsDepuracionService().depurar()
