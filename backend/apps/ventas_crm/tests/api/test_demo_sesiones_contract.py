import pytest

from apps.ventas_crm.demo_tokens import issue_demo_grant
from core.repositories.ventas_crm.prospecto_repository import ProspectoRepository

pytestmark = pytest.mark.api


def test_demo_sesiones_contract(api_client, mock_kafka):
    # Arrange
    p = ProspectoRepository().create(
        {
            "nombres": "N",
            "apellidos": "A",
            "gmail": "api.sesion@example.com",
            "empresa": "E",
            "tipo_organizacion": "Privado",
            "cargo": "C",
            "telefono": "1",
            "como_nos_conocio": "web",
        }
    )
    grant = issue_demo_grant(p["idprospecto"])
    # Act
    r1 = api_client.post(
        "/api/v1/ventas-crm/demo/sesiones",
        {"idprospecto": p["idprospecto"], "demo_grant": grant},
        format="json",
    )
    # Assert
    assert r1.status_code == 200
    assert r1.data["data"]["modo"] == "primer_canje"

    bad = api_client.post(
        "/api/v1/ventas-crm/demo/sesiones",
        {"idprospecto": p["idprospecto"], "demo_grant": "x.y.z"},
        format="json",
    )
    assert bad.status_code == 401
