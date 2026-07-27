import pytest

from apps.ventas_crm.demo_tokens import issue_demo_grant, verify_demo_grant
from core.repositories.ventas_crm.interaccion_demo_repository import InteraccionDemoRepository
from core.repositories.ventas_crm.notificacion_ventas_repository import NotificacionVentasRepository
from core.repositories.ventas_crm.prospecto_repository import ProspectoRepository

pytestmark = pytest.mark.repository


def test_update_demo_expiracion_when_exists_publishes(mock_pinot, mock_kafka):
    # Arrange
    p = ProspectoRepository().create(
        {
            "nombres": "A",
            "apellidos": "B",
            "gmail": "demo.exp@example.com",
            "empresa": "C",
            "tipo_organizacion": "Privado",
            "cargo": "D",
            "telefono": "1",
            "como_nos_conocio": "web",
        }
    )
    # Act
    updated = ProspectoRepository().update_demo_expiracion(p["idprospecto"], "2026-07-25T15:00:00Z")
    # Assert
    assert updated["demo_expiracion"] == "2026-07-25T15:00:00Z"
    assert ProspectoRepository().find_by_id(p["idprospecto"])["demo_expiracion"] == "2026-07-25T15:00:00Z"


def test_interaccion_demo_create_and_list(mock_pinot, mock_kafka):
    # Arrange / Act
    row = InteraccionDemoRepository().create(
        {
            "idprospecto": 1,
            "tipo_evento": "click",
            "seccion": "precios",
            "metadata": "{}",
            "timestamp_evento": 1000,
        }
    )
    # Assert
    assert row["idinteraccion"] >= 1
    listed = InteraccionDemoRepository().list_by_prospecto(1)
    assert any(r["idinteraccion"] == row["idinteraccion"] for r in listed)


def test_notificacion_dedup_dia_utc(mock_pinot, mock_kafka):
    # Arrange
    repo = NotificacionVentasRepository()
    repo.create(
        {
            "id_prospecto": 9,
            "idinteraccion": 1,
            "idusuariogerentenotificado": 20,
            "regladisparada": "visito_pricing_3x",
            "canal": "push",
            "fechahoranotificacion": 1_721_900_000_000,
        }
    )
    # Act / Assert
    assert repo.exists_dedup_dia_utc(
        id_prospecto=9,
        regladisparada="visito_pricing_3x",
        day_start_ms=1_721_894_400_000,
        day_end_ms=1_721_980_800_000,
    )
    assert not repo.exists_dedup_dia_utc(
        id_prospecto=9,
        regladisparada="tiempo_seccion_precios_5min",
        day_start_ms=1_721_894_400_000,
        day_end_ms=1_721_980_800_000,
    )


@pytest.mark.unit
def test_demo_grant_roundtrip():
    # Arrange / Act
    grant = issue_demo_grant(42)
    # Assert
    assert verify_demo_grant(grant, 42)
    assert not verify_demo_grant(grant, 43)
    assert not verify_demo_grant("bad.grant.value", 42)
