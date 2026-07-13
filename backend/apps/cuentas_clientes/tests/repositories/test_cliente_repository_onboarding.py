import pytest

from core.repositories.cuentas_clientes.cliente_repository import ClienteRepository


@pytest.mark.repository
class TestClienteRepositoryOnboarding:
    def test_create_publishes_dim_cliente(self, mock_pinot, mock_kafka):
        # Arrange
        repo = ClienteRepository()
        data = {
            "razon_social": "Test Corp",
            "nombre": "Test",
            "tipo": "Municipio",
            "nit_identificacion": "999888777-1",
            "fecha_inicio_contrato": 1704067200000,
            "admin_local_id": 99,
            "estado": "Activo",
        }

        # Act
        result = repo.create(data)

        # Assert
        assert result["idcliente"] == 2
        assert result["estado"] == "Activo"
        assert len(mock_kafka) == 1
        assert mock_kafka[0]["topic"].endswith("Dim_Cliente_topic")

    def test_find_by_nit_when_exists_returns_cliente(self, mock_pinot, mock_kafka):
        # Arrange
        repo = ClienteRepository()

        # Act
        result = repo.find_by_nit("900123456-1")

        # Assert
        assert result is not None
        assert result["idcliente"] == 1

    def test_find_by_admin_local_when_exists_returns_cliente(self, mock_pinot, mock_kafka):
        # Arrange
        repo = ClienteRepository()

        # Act
        result = repo.find_by_admin_local(3)

        # Assert
        assert result is not None
        assert result["admin_local_id"] == 3
