import pytest

from apps.accidentes.domain_constants import ESTADO_FUSIONADO
from apps.accidentes.services.fusionar_reportes_service import FusionarReportesService


@pytest.mark.service
class TestFusionarReportesService:
    def test_fusionar_when_valid_marks_duplicado_fusionado(
        self, mock_pinot, mock_kafka, seed_accidente
    ):
        # Arrange
        principal = seed_accidente(idaccidente="ACC-F-P")
        duplicado = seed_accidente(idaccidente="ACC-F-D")
        service = FusionarReportesService()

        # Act
        result = service.fusionar(
            idaccidente_duplicado=duplicado,
            idaccidente_principal=principal,
            idusuario=2,
            confirmacion=True,
        )

        # Assert
        assert result["estado_duplicado"] == ESTADO_FUSIONADO

    def test_un_caso_no_puede_fusionarse_consigo_mismo(
        self, mock_pinot, mock_kafka, seed_accidente
    ):
        # Arrange — el diálogo de duplicados llegaba a proponerlo: el caso real
        # quedaba apuntándose a sí mismo, desactivado y en FUSIONADO.
        caso = seed_accidente(idaccidente="ACC-F-SELF")

        # Act / Assert
        with pytest.raises(ValueError, match="consigo mismo"):
            FusionarReportesService().fusionar(
                idaccidente_duplicado=caso,
                idaccidente_principal=caso,
                idusuario=2,
                confirmacion=True,
            )

    def test_se_fusiona_aunque_el_padre_ya_este_buscando_unidad(
        self, mock_pinot, mock_kafka, seed_accidente
    ):
        # Arrange — SRS §3.6.1: el padre "continúa su flujo normal sin
        # alteración". El duplicado llega cuando el caso real ya se está
        # despachando; exigirle BORRADOR/REPORTADO al padre impedía la fusión
        # justo en el caso normal.
        from apps.accidentes.domain_constants import ESTADO_BUSCANDO_UNIDAD
        from core.repositories.accidentes.estado_accidente_repository import (
            EstadoAccidenteRepository,
        )

        principal = seed_accidente(idaccidente="ACC-F-P2")
        duplicado = seed_accidente(idaccidente="ACC-F-D2")
        estados = EstadoAccidenteRepository()
        estados.append_estado(
            idaccidente=principal, estado=ESTADO_BUSCANDO_UNIDAD, idusuario=2
        )

        # Act
        result = FusionarReportesService().fusionar(
            idaccidente_duplicado=duplicado,
            idaccidente_principal=principal,
            idusuario=2,
            confirmacion=True,
        )

        # Assert — el duplicado se marca; el padre sigue su curso intacto
        assert result["estado_duplicado"] == ESTADO_FUSIONADO
        assert estados.get_current_estado(principal) == ESTADO_BUSCANDO_UNIDAD

    def test_no_se_fusiona_un_reporte_que_ya_tiene_despacho(
        self, mock_pinot, mock_kafka, seed_accidente
    ):
        # Arrange — §3.6.1 cubre "los caminos que terminan antes de que exista
        # cualquier despacho": el duplicado sí debe estar sin despachar.
        from apps.accidentes.domain_constants import ESTADO_ASIGNADO
        from apps.accidentes.services.confirmar_reporte_service import ConflictError
        from core.repositories.accidentes.estado_accidente_repository import (
            EstadoAccidenteRepository,
        )

        principal = seed_accidente(idaccidente="ACC-F-P3")
        duplicado = seed_accidente(idaccidente="ACC-F-D3")
        EstadoAccidenteRepository().append_estado(
            idaccidente=duplicado, estado=ESTADO_ASIGNADO, idusuario=2
        )

        # Act / Assert
        with pytest.raises(ConflictError, match="despacho"):
            FusionarReportesService().fusionar(
                idaccidente_duplicado=duplicado,
                idaccidente_principal=principal,
                idusuario=2,
                confirmacion=True,
            )
