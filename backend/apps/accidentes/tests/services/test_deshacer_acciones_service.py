import pytest

from apps.accidentes.services.confirmar_reporte_service import ConflictError
from apps.accidentes.services.descartar_caso_service import DescartarCasoService
from apps.accidentes.services.deshacer_descarte_service import DeshacerDescarteService
from apps.accidentes.services.deshacer_fusion_service import DeshacerFusionService
from apps.accidentes.services.fusionar_reportes_service import FusionarReportesService


@pytest.mark.service
class TestDeshacerDescarteService:
    def test_deshacer_when_descartado_restores_borrador(
        self, mock_pinot, mock_kafka, seed_accidente
    ):
        aid = seed_accidente(estado="BORRADOR")
        DescartarCasoService().descartar(
            idaccidente=aid, idusuario=2, motivo="falso positivo"
        )
        result = DeshacerDescarteService().deshacer(idaccidente=aid, idusuario=2)
        assert result["estado"] == "BORRADOR"
        assert result["idaccidente"] == aid

    def test_deshacer_when_not_descartado_raises(
        self, mock_pinot, mock_kafka, seed_accidente
    ):
        aid = seed_accidente(estado="BORRADOR")
        with pytest.raises(ConflictError):
            DeshacerDescarteService().deshacer(idaccidente=aid, idusuario=2)


@pytest.mark.service
class TestDeshacerFusionService:
    def test_deshacer_when_fusionado_restores_activo(
        self, mock_pinot, mock_kafka, seed_accidente
    ):
        principal = seed_accidente(estado="REPORTADO")
        duplicado = seed_accidente(estado="REPORTADO")
        FusionarReportesService().fusionar(
            idaccidente_duplicado=duplicado,
            idaccidente_principal=principal,
            idusuario=2,
            confirmacion=True,
        )
        result = DeshacerFusionService().deshacer(
            idaccidente_duplicado=duplicado, idusuario=2
        )
        assert result["idaccidente"] == duplicado
        assert result["estado"] in {"BORRADOR", "REPORTADO"}
