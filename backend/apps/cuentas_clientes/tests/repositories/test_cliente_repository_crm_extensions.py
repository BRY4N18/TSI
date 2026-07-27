import pytest

from core.repositories.cuentas_clientes.cliente_repository import ClienteRepository


@pytest.mark.repository
def test_exists_by_nit_any_includes_all_estados(mock_pinot, mock_kafka):
    # Arrange
    repo = ClienteRepository()
    repo.create(
        {
            "razon_social": "X",
            "nombre": "Y",
            "tipo": "Municipio",
            "nit_identificacion": "NIT-ANY-1",
            "estado": "Rechazado_Anulado",
            "admin_local_id": None,
        }
    )
    # Act / Assert
    assert repo.exists_by_nit_any("NIT-ANY-1") is True
    assert repo.exists_by_nit_any("NIT-MISSING") is False
