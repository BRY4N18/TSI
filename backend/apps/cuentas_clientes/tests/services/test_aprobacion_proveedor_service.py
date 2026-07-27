import pytest

from apps.cuentas_clientes.services.aprobacion_proveedor_service import (
    AprobacionProveedorError,
    AprobacionProveedorService,
)
from apps.cuentas_clientes.services.autorregistro_proveedor_service import (
    AutorregistroProveedorService,
)


@pytest.mark.service
class TestAprobacionProveedorService:
    def _solicitud(self, nit="810999888-1", gmail="carlos.norte@tsi.com"):
        return AutorregistroProveedorService().autorregistrar(
            data={
                "razon_social": "Flota Norte CIA",
                "nombre": "Flota Norte",
                "tipo": "Proveedor",
                "nit_identificacion": nit,
                "admin_local": {
                    "nombres": "Carlos",
                    "apellidos": "Norte",
                    "gmail": gmail,
                },
            }
        )

    def test_aprobar_sets_activo_and_onboarding_pendiente(self, mock_pinot, mock_kafka):
        # Arrange
        created = self._solicitud()
        service = AprobacionProveedorService()

        # Act
        result = service.decidir(
            user_id=1,
            roles=["Administrador"],
            cliente_id=created["idcliente"],
            decision="aprobar",
        )

        # Assert
        assert result["estado"] == "Activo"
        assert result["estado_onboarding"] == "Pendiente"

    def test_rechazar_requires_motivo(self, mock_pinot, mock_kafka):
        # Arrange
        created = self._solicitud()
        service = AprobacionProveedorService()

        # Act / Assert
        with pytest.raises(AprobacionProveedorError, match="motivo"):
            service.decidir(
                user_id=1,
                roles=["Administrador"],
                cliente_id=created["idcliente"],
                decision="rechazar",
            )

    def test_listar_solicitudes_pendientes(self, mock_pinot, mock_kafka):
        # Arrange
        self._solicitud()
        service = AprobacionProveedorService()

        # Act
        rows = service.listar_solicitudes(roles=["Administrador"])

        # Assert
        assert any(r["nit_identificacion"] == "810999888-1" for r in rows)

    def test_anular_rechazo_libera_nit_para_nuevo_autorregistro(self, mock_pinot, mock_kafka):
        # Arrange
        created = self._solicitud(nit="820111222-3", gmail="anular@tsi.com")
        service = AprobacionProveedorService()
        service.decidir(
            user_id=1,
            roles=["Administrador"],
            cliente_id=created["idcliente"],
            decision="rechazar",
            motivo="Documentacion incompleta",
        )

        # Act
        anulado = service.anular_rechazo(
            user_id=1,
            roles=["Administrador"],
            cliente_id=created["idcliente"],
        )
        nuevo = AutorregistroProveedorService().autorregistrar(
            data={
                "razon_social": "Flota Norte CIA 2",
                "nombre": "Flota Norte 2",
                "tipo": "Proveedor",
                "nit_identificacion": "820111222-3",
                "admin_local": {
                    "nombres": "Carlos",
                    "apellidos": "Norte",
                    "gmail": "anular@tsi.com",
                },
            }
        )

        # Assert
        assert anulado["estado"] == "Rechazado_Anulado"
        assert nuevo["estado"] == "Pendiente_Aprobación"
        assert nuevo["idcliente"] != created["idcliente"]
