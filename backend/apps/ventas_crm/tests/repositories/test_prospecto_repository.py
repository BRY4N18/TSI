import pytest
from core.repositories.ventas_crm.prospecto_repository import ProspectoRepository

pytestmark = pytest.mark.repository

def test_find_by_gmail_uses_pinot(mock_pinot, mock_kafka):
    prospecto = ProspectoRepository().create({"nombres": "A", "apellidos": "B", "gmail": "a@example.com",
        "empresa": "C", "tipo_organizacion": "Privado", "cargo": "D", "telefono": "1", "como_nos_conocio": "web"})
    assert ProspectoRepository().find_by_gmail("a@example.com")["idprospecto"] == prospecto["idprospecto"]
