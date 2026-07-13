import pytest

from apps.seguimiento.jobs.gps_senal_perdida_job import run_gps_senal_perdida_job


@pytest.mark.service
class TestGpsSenalPerdidaJob:
    def test_run_when_sin_gps_genera_alertas(
        self,
        mock_pinot,
        mock_kafka,
        accidente_activo,
        despacho_confirmado_unidad,
    ):
        # Arrange

        # Act
        result = run_gps_senal_perdida_job(idusuario_operador=2)

        # Assert
        assert result["alertas_generadas"] >= 1
        assert len(result["detalle"]) >= 1
