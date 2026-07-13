import pytest

from apps.seguimiento.services.cerrar_caso_service import CerrarCasoService
from apps.seguimiento.services.expediente_service import ExpedienteService
from apps.seguimiento.services.registrar_llegada_service import RegistrarLlegadaService


@pytest.mark.service
class TestExpedienteService:
    def test_obtener_when_cerrado_returns_full_expediente(
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
            payload={"resultado_atencion": "Expediente service test"},
        )
        svc = ExpedienteService()

        # Act
        result = svc.obtener(accidente_activo, requiere_cerrado=True)

        # Assert
        assert result is not None
        assert result["accidente"]["idaccidente"] == accidente_activo
        assert "despachos" in result

    def test_obtener_when_condado_no_permitido_returns_none(
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
            payload={"resultado_atencion": "Filtro condado"},
        )
        svc = ExpedienteService()

        # Act
        result = svc.obtener(accidente_activo, condados_permitidos={99}, requiere_cerrado=True)

        # Assert
        assert result is None
