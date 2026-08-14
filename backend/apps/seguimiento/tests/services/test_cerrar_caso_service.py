import pytest

from apps.accidentes.domain_constants import ESTADO_CERRADO, ESTADO_EN_ATENCION
from apps.seguimiento.services.cerrar_caso_service import CerrarCasoService
from apps.seguimiento.services.finalizar_atencion_unidad_service import (
    FinalizarAtencionUnidadService,
)
from apps.seguimiento.services.registrar_llegada_service import RegistrarLlegadaService
from core.repositories.accidentes.estado_accidente_repository import (
    EstadoAccidenteRepository,
)
from core.repositories.despacho.historial_despacho_repository import (
    ESTADO_RETIRADO,
    HistorialDespachoRepository,
)


@pytest.mark.service
class TestCerrarCasoService:
    def test_no_se_cierra_mientras_una_unidad_siga_sin_retirarse(
        self,
        mock_pinot,
        mock_kafka,
        accidente_activo,
        despacho_confirmado_unidad,
    ):
        # Arrange — SRS §3.6.4: "un caso solo pasa a cerrado cuando **todas** las
        # unidades despachadas se han retirado. No existe el cierre parcial".
        # Antes, cerrar retiraba por su cuenta a quien siguiera trabajando y lo
        # registraba como retiro normal: la regla no llegaba a aplicarse nunca.
        iddespacho = despacho_confirmado_unidad["iddespacho"]
        RegistrarLlegadaService().registrar(iddespacho=iddespacho, idunidademergencia=1, idusuario=6)
        svc = CerrarCasoService()

        # Act / Assert — la unidad sigue en el sitio, sin retirarse
        with pytest.raises(ValueError, match="sin retirarse"):
            svc.cerrar(
                idaccidente=accidente_activo,
                idusuario=2,
                payload={"resultado_atencion": "Atención finalizada"},
            )
        assert EstadoAccidenteRepository().get_current_estado(accidente_activo) != ESTADO_CERRADO

    def test_cerrar_cuando_todas_las_unidades_se_retiraron(
        self,
        mock_pinot,
        mock_kafka,
        accidente_activo,
        despacho_confirmado_unidad,
    ):
        # Arrange — la unidad termina su parte; recién entonces el caso cierra.
        iddespacho = despacho_confirmado_unidad["iddespacho"]
        RegistrarLlegadaService().registrar(iddespacho=iddespacho, idunidademergencia=1, idusuario=6)
        FinalizarAtencionUnidadService().finalizar(
            iddespacho=iddespacho, idunidademergencia=1, idusuario=6
        )
        svc = CerrarCasoService()

        # Act
        result = svc.cerrar(
            idaccidente=accidente_activo,
            idusuario=2,
            payload={"resultado_atencion": "Atención finalizada"},
        )

        # Assert
        assert result["estado_caso"] == ESTADO_CERRADO
        assert result["duracionminutos"] >= 1
        estado_d, _ = HistorialDespachoRepository().get_current_estado(iddespacho)
        assert estado_d == ESTADO_RETIRADO

    def test_cerrar_guarda_resultado_en_fact_cierre_accidente(
        self,
        mock_pinot,
        mock_kafka,
        accidente_activo,
        despacho_confirmado_unidad,
        pinot_store,
    ):
        # Arrange — RF-SEG-004 (corrección 2026-08-08): estos campos no existen
        # en Fact_Accidente, se guardan en la tabla auxiliar Fact_CierreAccidente.
        iddespacho = despacho_confirmado_unidad["iddespacho"]
        RegistrarLlegadaService().registrar(iddespacho=iddespacho, idunidademergencia=1, idusuario=6)
        FinalizarAtencionUnidadService().finalizar(
            iddespacho=iddespacho, idunidademergencia=1, idusuario=6
        )
        svc = CerrarCasoService()

        # Act
        svc.cerrar(
            idaccidente=accidente_activo,
            idusuario=2,
            payload={
                "resultado_atencion": "Atención finalizada",
                "calificacion": 5,
                "observaciones_finales": "Todo en orden",
            },
        )

        # Assert
        cierre = next(
            c
            for c in pinot_store["Fact_CierreAccidente"]
            if c["idaccidente"] == accidente_activo
        )
        assert cierre["resultado_atencion"] == "Atención finalizada"
        assert cierre["calificacion"] == 5
        assert cierre["observaciones_finales"] == "Todo en orden"
        assert EstadoAccidenteRepository().get_current_estado(accidente_activo) == ESTADO_CERRADO

    def test_cerrar_when_ya_cerrado_raises(
        self,
        mock_pinot,
        mock_kafka,
        accidente_activo,
        despacho_confirmado_unidad,
    ):
        # Arrange
        iddespacho = despacho_confirmado_unidad["iddespacho"]
        RegistrarLlegadaService().registrar(iddespacho=iddespacho, idunidademergencia=1, idusuario=6)
        FinalizarAtencionUnidadService().finalizar(
            iddespacho=iddespacho, idunidademergencia=1, idusuario=6
        )
        svc = CerrarCasoService()
        svc.cerrar(
            idaccidente=accidente_activo,
            idusuario=2,
            payload={"resultado_atencion": "Primero"},
        )

        # Act / Assert
        with pytest.raises(ValueError, match="ya cerrado"):
            svc.cerrar(
                idaccidente=accidente_activo,
                idusuario=2,
                payload={"resultado_atencion": "Segundo"},
            )
