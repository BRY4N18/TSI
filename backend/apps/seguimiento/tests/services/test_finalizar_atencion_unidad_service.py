import pytest

from apps.seguimiento.services.finalizar_atencion_unidad_service import (
    FinalizarAtencionUnidadService,
)
from apps.seguimiento.services.registrar_llegada_service import RegistrarLlegadaService
from core.repositories.despacho.despacho_repository import DespachoRepository
from core.repositories.despacho.historial_despacho_repository import (
    ESTADO_RETIRADO,
    HistorialDespachoRepository,
)
from core.repositories.despacho.historial_estado_unidad_repository import (
    ESTADO_ACTIVA,
    HistorialEstadoUnidadRepository,
)


@pytest.mark.service
class TestFinalizarAtencionUnidadService:
    def test_la_unidad_cierra_su_parte_y_vuelve_a_estar_disponible(
        self, mock_pinot, mock_kafka, accidente_activo, despacho_confirmado_unidad
    ):
        # Arrange — SRS §3.6.4: la vía normal por la que un despacho llega a
        # "Retirado". Antes no existía: solo llegada o aborto.
        iddespacho = despacho_confirmado_unidad["iddespacho"]
        RegistrarLlegadaService().registrar(
            iddespacho=iddespacho, idunidademergencia=1, idusuario=6
        )
        svc = FinalizarAtencionUnidadService()

        # Act
        result = svc.finalizar(
            iddespacho=iddespacho, idunidademergencia=1, idusuario=6
        )

        # Assert
        assert result["caso_listo_para_cierre"] is True
        assert result["unidades_sin_retirar"] == 0
        estado, _ = HistorialDespachoRepository().get_current_estado(iddespacho)
        assert estado == ESTADO_RETIRADO
        estado_unidad, _ = HistorialEstadoUnidadRepository().get_current_estado(1)
        assert estado_unidad == ESTADO_ACTIVA

    def test_no_marca_el_retiro_como_forzado(
        self, mock_pinot, mock_kafka, accidente_activo, despacho_confirmado_unidad
    ):
        # Arrange — la distinción que pide el SRS: esto es una finalización
        # normal, no un cierre decidido desde central.
        iddespacho = despacho_confirmado_unidad["iddespacho"]
        RegistrarLlegadaService().registrar(
            iddespacho=iddespacho, idunidademergencia=1, idusuario=6
        )

        # Act
        FinalizarAtencionUnidadService().finalizar(
            iddespacho=iddespacho, idunidademergencia=1, idusuario=6
        )

        # Assert
        despacho = DespachoRepository().find_by_id(iddespacho)
        assert despacho["retiro_forzado"] is False

    def test_una_unidad_no_puede_finalizar_el_despacho_de_otra(
        self, mock_pinot, mock_kafka, accidente_activo, despacho_confirmado_unidad
    ):
        # Arrange
        iddespacho = despacho_confirmado_unidad["iddespacho"]

        # Act / Assert
        with pytest.raises(PermissionError):
            FinalizarAtencionUnidadService().finalizar(
                iddespacho=iddespacho, idunidademergencia=99, idusuario=6
            )

    def test_no_se_finaliza_dos_veces(
        self, mock_pinot, mock_kafka, accidente_activo, despacho_confirmado_unidad
    ):
        # Arrange
        iddespacho = despacho_confirmado_unidad["iddespacho"]
        RegistrarLlegadaService().registrar(
            iddespacho=iddespacho, idunidademergencia=1, idusuario=6
        )
        svc = FinalizarAtencionUnidadService()
        svc.finalizar(iddespacho=iddespacho, idunidademergencia=1, idusuario=6)

        # Act / Assert
        with pytest.raises(ValueError):
            svc.finalizar(iddespacho=iddespacho, idunidademergencia=1, idusuario=6)
