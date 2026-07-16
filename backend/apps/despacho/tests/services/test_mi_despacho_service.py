import pytest

from apps.despacho.services.mi_despacho_service import MiDespachoService


@pytest.mark.service
class TestMiDespachoService:
    def test_listar_pendientes_when_unidad_activa_incluye_datos_de_unidad(
        self, mock_pinot, mock_kafka, accidente_activo, unidad_con_estado_activa, despacho_pendiente_unidad
    ):
        # Arrange
        service = MiDespachoService()

        # Act
        pendientes = service.listar_pendientes(idusuario=6)

        # Assert
        assert len(pendientes) >= 1
        item = pendientes[0]
        assert item["idunidademergencia"] == 1
        assert item["unidademergencia"] == "Ambulancia 01"
        assert item["unidad_latitud"] == 19.43
        assert item["unidad_longitud"] == -99.13

    def test_listar_pendientes_when_usuario_sin_unidad_raises(self, mock_pinot, mock_kafka):
        # Arrange
        service = MiDespachoService()

        # Act / Assert
        with pytest.raises(LookupError):
            service.listar_pendientes(idusuario=9999)

    def test_obtener_detalle_when_own_notificacion_incluye_datos_de_unidad(
        self, mock_pinot, mock_kafka, accidente_activo, unidad_con_estado_activa, despacho_pendiente_unidad
    ):
        # Arrange
        service = MiDespachoService()
        idnotif = despacho_pendiente_unidad["idnotificaciondespacho"]

        # Act
        detalle = service.obtener_detalle(idnotificaciondespacho=idnotif, idunidademergencia=1)

        # Assert
        assert detalle["unidademergencia"] == "Ambulancia 01"
        assert detalle["unidad_latitud"] == 19.43
