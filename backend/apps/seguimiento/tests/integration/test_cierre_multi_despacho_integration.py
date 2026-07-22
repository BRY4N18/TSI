import pytest

from apps.accidentes.domain_constants import ESTADO_CERRADO, ESTADO_EN_ATENCION
from apps.despacho.services.asignacion_manual_service import AsignacionManualService
from apps.despacho.services.confirmar_despacho_service import ConfirmarDespachoService
from apps.seguimiento.services.cerrar_caso_service import CerrarCasoService
from apps.seguimiento.services.registrar_llegada_service import RegistrarLlegadaService
from apps.seguimiento.services.retiro_despacho_service import RetiroDespachoService
from core.repositories.accidentes.estado_accidente_repository import (
    EstadoAccidenteRepository,
)
from core.repositories.despacho.historial_despacho_repository import (
    ESTADO_RETIRADO,
    HistorialDespachoRepository,
)
from core.repositories.despacho.historial_estado_unidad_repository import (
    HistorialEstadoUnidadRepository,
)


@pytest.mark.critical_path
class TestCierreMultiDespachoIntegration:
    def test_cerrar_when_un_despacho_retirado_auto_retira_pendiente(
        self,
        mock_pinot,
        mock_kafka,
        accidente_activo,
        despacho_confirmado_unidad,
    ):
        # Arrange — segundo despacho manual para la misma unidad/caso
        HistorialEstadoUnidadRepository().append_estado(
            idunidademergencia=2,
            estadonuevo="Activa",
            idusuario=99,
            estadoanterior="Fuera de servicio",
        )
        asignacion = AsignacionManualService().asignar(
            idaccidente=accidente_activo,
            idunidademergencia=2,
            idusuario=2,
        )
        despacho2 = ConfirmarDespachoService().confirmar(
            idnotificaciondespacho=asignacion["idnotificaciondespacho"],
            idunidademergencia=2,
            idusuario=99,
        )
        iddespacho1 = despacho_confirmado_unidad["iddespacho"]
        iddespacho2 = despacho2["iddespacho"]
        RegistrarLlegadaService().registrar(iddespacho=iddespacho1, idunidademergencia=1, idusuario=6)
        RegistrarLlegadaService().registrar(iddespacho=iddespacho2, idunidademergencia=2, idusuario=99)
        assert EstadoAccidenteRepository().get_current_estado(accidente_activo) == ESTADO_EN_ATENCION
        RetiroDespachoService().retirar(iddespacho=iddespacho1, idusuario=2)

        # Act
        result = CerrarCasoService().cerrar(
            idaccidente=accidente_activo,
            idusuario=2,
            payload={"resultado_atencion": "Cierre multi-despacho"},
        )

        # Assert
        assert result["estado_caso"] == ESTADO_CERRADO
        assert iddespacho2 in result["despachos_retirados"]
        estado2, _ = HistorialDespachoRepository().get_current_estado(iddespacho2)
        assert estado2 == ESTADO_RETIRADO
