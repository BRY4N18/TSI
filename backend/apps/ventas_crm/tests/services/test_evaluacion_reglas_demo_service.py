from datetime import datetime, timedelta, timezone

import pytest

from apps.ventas_crm.demo_tokens import format_iso_expiracion
from apps.ventas_crm.services.evaluacion_reglas_demo_service import EvaluacionReglasDemoService
from core.repositories.ventas_crm.interaccion_demo_repository import InteraccionDemoRepository
from core.repositories.ventas_crm.prospecto_repository import ProspectoRepository

pytestmark = pytest.mark.service


def test_evaluacion_crea_notificacion_con_dueno(mock_pinot, mock_kafka):
    # Arrange
    now = datetime.now(timezone.utc)
    iso = format_iso_expiracion(now + timedelta(minutes=30))
    p = ProspectoRepository().create(
        {
            "nombres": "N",
            "apellidos": "A",
            "gmail": "eval@example.com",
            "empresa": "E",
            "tipo_organizacion": "Privado",
            "cargo": "C",
            "telefono": "1",
            "como_nos_conocio": "web",
            "demo_expiracion": None,
        }
    )
    ProspectoRepository().update(p["idprospecto"], {"idusuario": 20, "demo_expiracion": iso})
    inicio_ms = int(now.timestamp() * 1000)
    InteraccionDemoRepository().create(
        {
            "idprospecto": p["idprospecto"],
            "tipo_evento": "inicio_sesion",
            "seccion": "demo",
            "metadata": "{}",
            "timestamp_evento": inicio_ms,
        }
    )
    InteraccionDemoRepository().create(
        {
            "idprospecto": p["idprospecto"],
            "tipo_evento": "tiempo_seccion",
            "seccion": "precios",
            "metadata": '{"duracion_ms": 300000}',
            "timestamp_evento": inicio_ms + 1,
        }
    )
    # Act
    result = EvaluacionReglasDemoService().run(now=now)
    # Assert
    assert result["created"] >= 1
