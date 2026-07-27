from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import pytest

from apps.suscripciones.services.evaluacion_acceso_service import EvaluacionAccesoService

pytestmark = pytest.mark.service
TZ = ZoneInfo("America/Guayaquil")


class TestEvaluacionAccesoService:
    def test_activa_permite(self):
        assert EvaluacionAccesoService().acceso_permitido(
            {"activo": True, "estado": "Activa"}
        )

    def test_suspendida_deniega(self):
        assert not EvaluacionAccesoService().acceso_permitido(
            {"activo": True, "estado": "Suspendida"}
        )

    def test_cancelada_hasta_fecha_fin(self):
        # Arrange
        now = datetime(2026, 7, 1, tzinfo=TZ)
        fin = now + timedelta(days=10)
        # Act / Assert
        assert EvaluacionAccesoService().acceso_permitido(
            {
                "activo": True,
                "estado": "Cancelada",
                "fecha_fin": fin.isoformat(),
            },
            now=now,
        )
        assert not EvaluacionAccesoService().acceso_permitido(
            {
                "activo": True,
                "estado": "Cancelada",
                "fecha_fin": (now - timedelta(days=1)).isoformat(),
            },
            now=now,
        )
