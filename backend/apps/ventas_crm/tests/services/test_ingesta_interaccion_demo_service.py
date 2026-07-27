import pytest

from apps.ventas_crm.domain import ForbiddenError
from apps.ventas_crm.services.ingesta_interaccion_demo_service import IngestaInteraccionDemoService

pytestmark = pytest.mark.service


def test_ingesta_interaccion_ok(mock_pinot, mock_kafka, demo_session_auth_headers):
    # Arrange
    idp = demo_session_auth_headers["idprospecto"]
    # Act
    row = IngestaInteraccionDemoService().registrar(
        idprospecto_token=idp,
        data={
            "idprospecto": idp,
            "tipo_evento": "tiempo_seccion",
            "seccion": "precios",
            "metadata": {"duracion_ms": 300000},
            "timestamp_evento": 1_000,
        },
    )
    # Assert
    assert row["tipo_evento"] == "tiempo_seccion"


def test_ingesta_rechaza_id_mismatch(mock_pinot, mock_kafka, demo_session_auth_headers):
    # Arrange / Act / Assert
    with pytest.raises(ForbiddenError):
        IngestaInteraccionDemoService().registrar(
            idprospecto_token=demo_session_auth_headers["idprospecto"],
            data={
                "idprospecto": 999999,
                "tipo_evento": "click",
                "seccion": "precios",
                "timestamp_evento": 1,
            },
        )
