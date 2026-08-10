import pytest

from apps.red_operativa.services.baja_unidad_service import BajaUnidadService
from apps.red_operativa.services.proveedor_access_service import ProveedorAccessError

PROVEEDOR_KW = {"roles": ["Cliente"]}
ADMIN_KW = {"roles": ["Administrador"]}


@pytest.mark.service
class TestBajaUnidadService:
    def test_dar_de_baja_when_sin_despacho_activo_updates_activo_false(
        self, mock_pinot, mock_kafka, mock_unidad_emergencia
    ):
        # Arrange
        service = BajaUnidadService()

        # Act
        result = service.dar_de_baja(
            mock_unidad_emergencia["idunidademergencia"],
            motivo="Mantenimiento",
            idusuario=3,
            **PROVEEDOR_KW,
        )

        # Assert
        assert result["activo"] is False

    def test_dar_de_baja_when_despacho_activo_sin_forzar_raises(
        self, mock_pinot, mock_kafka, mock_despacho_activo
    ):
        # Arrange — proveedor sin despacho activo forzado tampoco puede: el rol
        # se valida antes que el flag forzar (ver test_forzada_por_proveedor_raises).
        service = BajaUnidadService()

        # Act & Assert
        with pytest.raises(PermissionError, match="Administrador"):
            service.dar_de_baja(
                mock_despacho_activo["idunidademergencia"],
                motivo="Baja forzada",
                idusuario=3,
                **PROVEEDOR_KW,
            )

    def test_dar_de_baja_when_forzada_por_proveedor_raises(
        self, mock_pinot, mock_kafka, mock_despacho_activo
    ):
        # Arrange — SRS 3.5.1: única excepción al autoservicio del proveedor
        # (RF-O42.4); el proveedor no puede autoforzar su propia baja aunque
        # pase forzar=True.
        service = BajaUnidadService()

        # Act & Assert
        with pytest.raises(PermissionError, match="Administrador"):
            service.dar_de_baja(
                mock_despacho_activo["idunidademergencia"],
                motivo="Baja forzada",
                idusuario=3,
                forzar=True,
                **PROVEEDOR_KW,
            )

    def test_dar_de_baja_when_forzada_por_administrador_registra_idaccidente(
        self, mock_pinot, mock_kafka, mock_despacho_activo
    ):
        # Arrange
        service = BajaUnidadService()

        # Act
        service.dar_de_baja(
            mock_despacho_activo["idunidademergencia"],
            motivo="Baja forzada",
            idusuario=1,
            forzar=True,
            **ADMIN_KW,
        )
        bajas = service.baja_repo.list_by_unidad(mock_despacho_activo["idunidademergencia"])

        # Assert
        assert bajas[0]["tipobaja"] == "Forzada_con_reasignación"
        assert bajas[0]["idaccidente"] == mock_despacho_activo["idaccidente"]

    def test_dar_de_baja_when_administrador_sin_forzar_raises(
        self, mock_pinot, mock_kafka, mock_despacho_activo
    ):
        # Arrange
        service = BajaUnidadService()

        # Act & Assert
        with pytest.raises(ValueError, match="forzar"):
            service.dar_de_baja(
                mock_despacho_activo["idunidademergencia"],
                motivo="Baja forzada",
                idusuario=1,
                **ADMIN_KW,
            )

    def test_reactivar_when_sin_conflicto_de_placa_updates_activo_true(
        self, mock_pinot, mock_kafka, mock_unidad_emergencia
    ):
        # Arrange
        service = BajaUnidadService()
        service.dar_de_baja(
            mock_unidad_emergencia["idunidademergencia"],
            motivo="Baja",
            idusuario=3,
            **PROVEEDOR_KW,
        )

        # Act
        result = service.reactivar(
            mock_unidad_emergencia["idunidademergencia"], user_id=3, **PROVEEDOR_KW
        )

        # Assert
        assert result["activo"] is True

    def test_reactivar_when_placa_duplicada_raises(
        self, mock_pinot, mock_kafka, mock_unidad_emergencia
    ):
        # Arrange
        service = BajaUnidadService()
        service.dar_de_baja(
            mock_unidad_emergencia["idunidademergencia"],
            motivo="Baja",
            idusuario=3,
            **PROVEEDOR_KW,
        )
        service.unidad_repo.create(
            {
                "idcliente": 1,
                "idcondado": 1,
                "tipopropiedad": "Externa",
                "placa": mock_unidad_emergencia["placa"],
                "unidademergencia": "Otra unidad",
                "tipounidademergencia": "Patrulla",
                "contactoproveedor": "555",
            }
        )

        # Act & Assert
        with pytest.raises(ValueError):
            service.reactivar(
                mock_unidad_emergencia["idunidademergencia"], user_id=3, **PROVEEDOR_KW
            )

    def test_dar_de_baja_when_admin_raises(self, mock_pinot, mock_kafka, mock_unidad_emergencia):
        # Arrange
        service = BajaUnidadService()

        # Act & Assert
        with pytest.raises(ProveedorAccessError):
            service.dar_de_baja(
                mock_unidad_emergencia["idunidademergencia"],
                motivo="Hack",
                idusuario=1,
                roles=["Administrador"],
            )
