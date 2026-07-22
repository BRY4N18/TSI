from datetime import datetime, timezone

import pytest

from apps.soporte_cliente.services.monitoreo_sla_service import MonitoreoSLAService
from apps.soporte_cliente.services.registrar_ticket_service import RegistrarTicketService
from core.repositories.soporte.reclamo_repository import ReclamoRepository


_ELAPSED_REF_MS = 100_000  # 100s de referencia ya transcurridos desde fechahora


def _ticket_con_plazos(pinot_store, *, primera_respuesta_pct=None, resolucion_pct=None):
    """Crea un ticket y ajusta `fechahora`/deadlines para que el % de SLA consumido
    sea exactamente el solicitado, sin importar cuán rápido corra el test."""
    reclamo = RegistrarTicketService().registrar(
        idcliente=1, asunto="API caída", descripcion="error 500", tipo="tecnico", idusuario=3
    )
    now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
    fechahora_nueva = now_ms - _ELAPSED_REF_MS
    changes = {"fechahora": fechahora_nueva}
    if primera_respuesta_pct is not None:
        total = _ELAPSED_REF_MS / primera_respuesta_pct
        changes["sla_primera_respuesta"] = fechahora_nueva + int(total)
    if resolucion_pct is not None:
        total = _ELAPSED_REF_MS / resolucion_pct
        changes["sla_resolucion"] = fechahora_nueva + int(total)
    for row in pinot_store["Fact_Reclamo"]:
        if row["id_reclamo"] == reclamo["id_reclamo"]:
            row.update(changes)
    return reclamo["id_reclamo"]


@pytest.mark.service
class TestMonitoreoSLAService:
    def test_ejecutar_ciclo_when_bajo_80_no_cambia_nada(self, mock_pinot, mock_kafka, pinot_store):
        # Arrange
        id_reclamo = _ticket_con_plazos(pinot_store, primera_respuesta_pct=0.5, resolucion_pct=0.5)

        # Act
        resultado = MonitoreoSLAService().ejecutar_ciclo()

        # Assert
        assert resultado == {"escalados": 0, "en_riesgo": 0}
        assert ReclamoRepository().find_by_id(id_reclamo)["sla_status"] == "en curso"

    def test_ejecutar_ciclo_when_sobre_80_marca_en_riesgo(self, mock_pinot, mock_kafka, pinot_store):
        # Arrange — solo sla_primera_respuesta cruza el 80%, resolucion no
        id_reclamo = _ticket_con_plazos(pinot_store, primera_respuesta_pct=0.85, resolucion_pct=0.1)

        # Act
        resultado = MonitoreoSLAService().ejecutar_ciclo()

        # Assert
        assert resultado["en_riesgo"] == 1
        assert ReclamoRepository().find_by_id(id_reclamo)["sla_status"] == "en riesgo"

    def test_ejecutar_ciclo_when_excede_100_escala_a_supervisor(
        self, mock_pinot, mock_kafka, pinot_store
    ):
        # Arrange
        id_reclamo = _ticket_con_plazos(pinot_store, primera_respuesta_pct=1.5, resolucion_pct=0.1)

        # Act
        resultado = MonitoreoSLAService().ejecutar_ciclo()

        # Assert
        actualizado = ReclamoRepository().find_by_id(id_reclamo)
        assert resultado["escalados"] == 1
        assert actualizado["sla_status"] == "incumplido"
        assert actualizado["estado"] == "Escalado"
        assert actualizado["id_agente_asignado"] == 2  # SOPORTE_SUPERVISOR_USER_ID default
