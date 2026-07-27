import pytest

from apps.ventas_crm.demo_tokens import issue_demo_grant
from apps.ventas_crm.domain import UnauthorizedError
from apps.ventas_crm.services.demo_sesion_service import DemoSesionService
from core.repositories.ventas_crm.prospecto_repository import ProspectoRepository

pytestmark = pytest.mark.service


def test_demo_sesion_primer_canje_y_resume(mock_pinot, mock_kafka):
    # Arrange
    p = ProspectoRepository().create(
        {
            "nombres": "N",
            "apellidos": "A",
            "gmail": "sesion@example.com",
            "empresa": "E",
            "tipo_organizacion": "Privado",
            "cargo": "C",
            "telefono": "1",
            "como_nos_conocio": "web",
            "demo_expiracion": None,
        }
    )
    grant = issue_demo_grant(p["idprospecto"])
    svc = DemoSesionService()
    # Act
    first = svc.abrir(idprospecto=p["idprospecto"], demo_grant=grant)
    second = svc.abrir(idprospecto=p["idprospecto"], demo_grant=grant)
    # Assert
    assert first["modo"] == "primer_canje"
    assert second["modo"] == "resume"
    assert first["demo_expiracion"] == second["demo_expiracion"]


def test_demo_sesion_grant_invalido(mock_pinot, mock_kafka):
    # Arrange
    p = ProspectoRepository().create(
        {
            "nombres": "N",
            "apellidos": "A",
            "gmail": "badgrant@example.com",
            "empresa": "E",
            "tipo_organizacion": "Privado",
            "cargo": "C",
            "telefono": "1",
            "como_nos_conocio": "web",
        }
    )
    # Act / Assert
    with pytest.raises(UnauthorizedError):
        DemoSesionService().abrir(idprospecto=p["idprospecto"], demo_grant="1.x.bad")
