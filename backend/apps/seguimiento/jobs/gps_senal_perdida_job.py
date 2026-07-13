"""Job O37 — señal GPS perdida."""

from apps.seguimiento.services.gps_senal_perdida_service import GpsSenalPerdidaService


def run_gps_senal_perdida_job(*, idusuario_operador: int = 0) -> dict:
    alertas = GpsSenalPerdidaService().evaluar_unidades_en_camino(
        idusuario_operador=idusuario_operador
    )
    return {"alertas_generadas": len(alertas), "detalle": alertas}
