import pytest

from apps.cuentas_clientes.services.transferencia_propiedad_service import (
    TransferenciaPropiedadService,
)


@pytest.mark.service
class TestTransferenciaPropiedadService:
    def test_transferir_when_valid_updates_admin_local(self, mock_pinot, mock_kafka):
        # Arrange
        service = TransferenciaPropiedadService()

        # Act
        result = service.transferir(
            user_id=3,
            roles=["Cliente"],
            cliente_id=1,
            nuevo_responsable_id=4,
            ip_address="127.0.0.1",
        )

        # Assert
        assert result["nuevo_admin_local_id"] == 4
        assert result["admin_local_anterior_id"] == 3

    def test_rechaza_transferir_a_alguien_de_otra_organizacion(self, mock_pinot, mock_kafka):
        """SRS §3.2.3: el nuevo responsable debe ser «de su misma organización».

        Antes se listaba y se aceptaba a cualquier usuario activo con rol
        Cliente del sistema entero, así que el responsable de una empresa podía
        entregar el control de su cuenta a alguien de otra. La comprobación de
        pertenencia no existía, pese a que el mensaje de error ya la nombraba.
        """
        # Arrange — el usuario 1 es de otra cuenta, no de la 1.
        from conftest import PINOT_STORE

        assert not any(
            m["idusuario"] == 1 and m["idcliente"] == 1
            for m in PINOT_STORE["Dim_Usuario_Cliente"]
        )
        service = TransferenciaPropiedadService()

        # Act / Assert
        with pytest.raises(Exception) as exc:
            service.transferir(
                user_id=3,
                roles=["Cliente"],
                cliente_id=1,
                nuevo_responsable_id=1,
            )
        assert "no pertenece" in str(exc.value)

    def test_solo_lista_candidatos_de_la_propia_organizacion(self, mock_pinot, mock_kafka):
        # Arrange
        service = TransferenciaPropiedadService()

        # Act
        elegibles = service.list_usuarios_elegibles(user_id=3, roles=["Cliente"], cliente_id=1)

        # Assert — 3 y 4 pertenecen a la cuenta 1; nadie más aparece.
        assert {u["idusuario"] for u in elegibles} <= {3, 4}
        assert any(u["es_admin_local_actual"] for u in elegibles)
