import pytest

from apps.seguimiento.services.cerrar_caso_service import CerrarCasoService
from apps.seguimiento.services.historial_emergencias_service import HistorialEmergenciasService
from apps.seguimiento.services.registrar_llegada_service import RegistrarLlegadaService


@pytest.mark.service
class TestHistorialEmergenciasService:
    def test_listar_when_cerrado_includes_item(
        self,
        mock_pinot,
        mock_kafka,
        accidente_activo,
        despacho_confirmado_unidad,
    ):
        # Arrange
        iddespacho = despacho_confirmado_unidad["iddespacho"]
        RegistrarLlegadaService().registrar(iddespacho=iddespacho, idunidademergencia=1, idusuario=6)
        CerrarCasoService().cerrar(
            idaccidente=accidente_activo,
            idusuario=2,
            payload={"resultado_atencion": "Historial test"},
        )
        svc = HistorialEmergenciasService()

        # Act
        result = svc.listar(solo_cerrados=True)

        # Assert
        assert any(i["idaccidente"] == accidente_activo for i in result["items"])

    def test_condados_desde_preferencias_parses_json(self):
        # Arrange

        # Act
        condados = HistorialEmergenciasService.condados_desde_preferencias("[1, 2]")

        # Assert
        assert condados == {1, 2}
