import pytest

from apps.ventas_crm.services.registro_prospecto_service import RegistroProspectoService

pytestmark = pytest.mark.service


def test_registro_incluye_demo_grant(mock_pinot, mock_kafka):
    # Arrange / Act
    result = RegistroProspectoService().registrar(
        {
            "nombres": "Neo",
            "apellidos": "Ada",
            "gmail": "grant.user@example.com",
            "empresa": "Acme",
            "tipo_organizacion": "Privado",
            "cargo": "Compras",
            "telefono": "3000000000",
            "como_nos_conocio": "web",
        }
    )
    # Assert
    assert result["demo_grant"]
    assert result["demo_grant"].startswith(f"{result['idprospecto']}.")
