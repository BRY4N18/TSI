import pytest

from apps.ventas_crm.demo_tokens import issue_demo_grant
from core.repositories.ventas_crm.prospecto_repository import ProspectoRepository

pytestmark = pytest.mark.api


def test_demo_interacciones_contract(api_client, mock_kafka):
    # Arrange
    p = ProspectoRepository().create(
        {
            "nombres": "N",
            "apellidos": "A",
            "gmail": "api.inter@example.com",
            "empresa": "E",
            "tipo_organizacion": "Privado",
            "cargo": "C",
            "telefono": "1",
            "como_nos_conocio": "web",
        }
    )
    grant = issue_demo_grant(p["idprospecto"])
    ses = api_client.post(
        "/api/v1/ventas-crm/demo/sesiones",
        {"idprospecto": p["idprospecto"], "demo_grant": grant},
        format="json",
    )
    token = ses.data["data"]["demo_session_token"]
    # Act
    r2 = api_client.post(
        "/api/v1/ventas-crm/demo/interacciones",
        {
            "idprospecto": p["idprospecto"],
            "tipo_evento": "click",
            "seccion": "precios",
            "timestamp_evento": 123,
        },
        format="json",
        HTTP_AUTHORIZATION=f"Bearer {token}",
    )
    # Assert
    assert r2.status_code == 201


def test_interaccion_requiere_demo_token(api_client, auth_headers):
    # Arrange / Act
    r = api_client.post(
        "/api/v1/ventas-crm/demo/interacciones",
        {"idprospecto": 1, "tipo_evento": "click", "seccion": "precios", "timestamp_evento": 1},
        format="json",
        **auth_headers,
    )
    # Assert
    assert r.status_code in (401, 403)
