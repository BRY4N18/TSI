import pytest

from apps.cuentas_clientes.services.autorregistro_proveedor_service import (
    AutorregistroProveedorError,
    AutorregistroProveedorService,
)


@pytest.mark.service
class TestAutorregistroProveedorService:
    def test_autorregistrar_when_valid_creates_pendiente(self, mock_pinot, mock_kafka):
        # Arrange
        service = AutorregistroProveedorService()
        data = {
            "razon_social": "Gruas Andinas S.A.",
            "nombre": "Gruas Andinas",
            "tipo": "Proveedor",
            "nit_identificacion": "800111222-3",
            "admin_local": {
                "nombres": "Ana",
                "apellidos": "Proveedor",
                "gmail": "ana.proveedor@tsi.com",
            },
        }

        # Act
        result = service.autorregistrar(data=data)

        # Assert
        assert result["estado"] == "Pendiente_Aprobación"
        assert result["admin_local_gmail"] == "ana.proveedor@tsi.com"
        assert "idcliente" in result
        assert len(mock_kafka) >= 3

    def test_autorregistrar_when_duplicate_nit_raises(self, mock_pinot, mock_kafka):
        # Arrange
        service = AutorregistroProveedorService()
        data = {
            "razon_social": "Dup",
            "nombre": "Dup",
            "tipo": "Proveedor",
            "nit_identificacion": "900123456-1",
            "admin_local": {
                "nombres": "A",
                "apellidos": "B",
                "gmail": "unique.prov@tsi.com",
            },
        }

        # Act / Assert
        with pytest.raises(AutorregistroProveedorError, match="NIT"):
            service.autorregistrar(data=data)
