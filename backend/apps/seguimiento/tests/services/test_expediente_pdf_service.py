import pytest

from apps.seguimiento.services.cerrar_caso_service import CerrarCasoService
from apps.seguimiento.services.expediente_pdf_service import ExpedientePdfService
from apps.seguimiento.services.registrar_llegada_service import RegistrarLlegadaService


@pytest.mark.service
class TestExpedientePdfService:
    def test_generar_bytes_when_cerrado_returns_pdf(
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
            payload={"resultado_atencion": "PDF service test"},
        )
        svc = ExpedientePdfService()

        # Act
        pdf = svc.generar_bytes(accidente_activo, condados_permitidos={1})

        # Assert
        assert pdf is not None
        assert pdf.startswith(b"%PDF")
        assert accidente_activo.encode() in pdf

    def test_generar_bytes_when_activo_returns_none(
        self,
        mock_pinot,
        mock_kafka,
        accidente_activo,
        despacho_confirmado_unidad,
    ):
        # Arrange
        svc = ExpedientePdfService()

        # Act
        pdf = svc.generar_bytes(accidente_activo, condados_permitidos={1})

        # Assert
        assert pdf is None
