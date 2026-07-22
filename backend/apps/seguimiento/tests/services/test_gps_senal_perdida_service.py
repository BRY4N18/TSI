import pytest

from apps.seguimiento.services.gps_senal_perdida_service import GpsSenalPerdidaService


@pytest.mark.service
class TestGpsSenalPerdidaService:
    def test_evaluar_when_sin_gps_genera_alerta(
        self,
        mock_pinot,
        mock_kafka,
        accidente_activo,
        despacho_confirmado_unidad,
    ):
        # Arrange — despacho confirmado sin posiciones GPS recientes
        svc = GpsSenalPerdidaService()

        # Act
        alertas = svc.evaluar_unidades_en_camino(idusuario_operador=2)

        # Assert
        assert len(alertas) >= 1
        assert alertas[0]["iddespacho"] == despacho_confirmado_unidad["iddespacho"]

    def test_evaluar_when_gps_reciente_no_alerta(
        self,
        mock_pinot,
        mock_kafka,
        accidente_activo,
        despacho_confirmado_unidad,
    ):
        # Arrange
        from datetime import datetime, timezone

        from apps.seguimiento.services.registrar_posicion_gps_service import (
            RegistrarPosicionGpsService,
        )

        now = int(datetime.now(timezone.utc).timestamp() * 1000)
        RegistrarPosicionGpsService().registrar(
            idunidademergencia=1,
            idaccidente=accidente_activo,
            latitud=19.4326,
            longitud=-99.1332,
            fechahora=now,
            idusuario=6,
        )
        svc = GpsSenalPerdidaService()

        # Act
        alertas = svc.evaluar_unidades_en_camino(idusuario_operador=2)

        # Assert
        assert len(alertas) == 0
