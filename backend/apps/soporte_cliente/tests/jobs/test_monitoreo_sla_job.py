import pytest

from apps.soporte_cliente.jobs.monitoreo_sla_job import run_monitoreo_sla_job


@pytest.mark.service
class TestMonitoreoSLAJob:
    def test_run_monitoreo_sla_job_when_no_tickets_returns_zero_counts(self, mock_pinot, mock_kafka):
        # Act
        resultado = run_monitoreo_sla_job()

        # Assert
        assert resultado == {"escalados": 0, "en_riesgo": 0, "cerrados_automaticamente": 0}
