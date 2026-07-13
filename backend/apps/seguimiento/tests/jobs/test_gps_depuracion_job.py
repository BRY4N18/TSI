import pytest

from apps.seguimiento.jobs.gps_depuracion_job import run_gps_depuracion_job


@pytest.mark.service
class TestGpsDepuracionJob:
    def test_run_returns_depuracion_summary(
        self,
        mock_pinot,
        mock_kafka,
        accidente_activo,
        despacho_confirmado_unidad,
    ):
        # Arrange

        # Act
        result = run_gps_depuracion_job()

        # Assert
        assert "depurados" in result
        assert "retencion_dias" in result
