import pytest

from apps.accidentes.domain_constants import ESTADO_CERRADO, ESTADO_EN_ATENCION
from apps.despacho.services.asignacion_manual_service import AsignacionManualService
from apps.despacho.services.confirmar_despacho_service import ConfirmarDespachoService
from apps.seguimiento.services.cerrar_caso_service import CerrarCasoService
from apps.seguimiento.services.finalizar_atencion_unidad_service import (
    FinalizarAtencionUnidadService,
)
from apps.seguimiento.services.forzar_retiro_service import ForzarRetiroService
from apps.seguimiento.services.registrar_llegada_service import RegistrarLlegadaService
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
    def test_el_caso_no_cierra_hasta_que_se_retiran_todas_las_unidades(
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

        # Act / Assert — la primera unidad termina su parte; el caso sigue
        # abierto porque la segunda continúa trabajando (SRS §3.6.4: "no existe
        # el cierre parcial").
        FinalizarAtencionUnidadService().finalizar(
            iddespacho=iddespacho1, idunidademergencia=1, idusuario=6
        )
        with pytest.raises(ValueError, match="sin retirarse"):
            CerrarCasoService().cerrar(
                idaccidente=accidente_activo,
                idusuario=2,
                payload={"resultado_atencion": "Cierre multi-despacho"},
            )
        assert EstadoAccidenteRepository().get_current_estado(accidente_activo) == ESTADO_EN_ATENCION

        # El Operador fuerza el retiro de la que falta: queda marcado como
        # forzado y, al completarse el conjunto, el caso se cierra.
        forzado = ForzarRetiroService().forzar(iddespacho=iddespacho2, idusuario=2)

        # Assert
        assert forzado["caso_cerrado"] is True
        assert forzado["estado_caso"] == ESTADO_CERRADO
        estado2, _ = HistorialDespachoRepository().get_current_estado(iddespacho2)
        assert estado2 == ESTADO_RETIRADO
        assert EstadoAccidenteRepository().get_current_estado(accidente_activo) == ESTADO_CERRADO
