from types import SimpleNamespace

import pytest

from apps.accidentes.domain_constants import ESTADO_BORRADOR, ESTADO_DESCARTADO
from apps.accidentes.services.confirmar_reporte_service import ConflictError
from apps.accidentes.services.descartar_caso_service import DescartarCasoService


@pytest.mark.service
class TestDescartarCasoService:
    def test_descartar_when_borrador_sets_inactivo(self, mock_pinot, mock_kafka, seed_accidente):
        # Arrange
        aid = seed_accidente(idaccidente="ACC-D-SVC", estado=ESTADO_BORRADOR)
        service = DescartarCasoService()

        # Act
        result = service.descartar(idaccidente=aid, idusuario=2, motivo="test")

        # Assert
        assert result["estado"] == ESTADO_DESCARTADO

    def test_descartar_when_sin_motivo_sets_inactivo(
        self, mock_pinot, mock_kafka, seed_accidente
    ):
        # Arrange — SRS 3.6.1 / RF-REG-007.4: el motivo es opcional, no obligatorio.
        aid = seed_accidente(idaccidente="ACC-D-SVC3", estado=ESTADO_BORRADOR)
        service = DescartarCasoService()

        # Act
        result = service.descartar(idaccidente=aid, idusuario=2)

        # Assert
        assert result["estado"] == ESTADO_DESCARTADO

    def test_descartar_reportado_sin_despacho_es_posible(
        self, mock_pinot, mock_kafka, seed_accidente
    ):
        """SRS §3.6.1: la falsa alarma se descarta *mientras no exista despacho*.

        La guarda exigía BORRADOR, que es otra condición. Como el registro se
        autoconfirma a REPORTADO cuando no hay advertencias, una falsa alarma limpia
        no se podía descartar nunca aunque no se hubiera despachado a nadie.
        """
        # Arrange
        aid = seed_accidente(idaccidente="ACC-D-SVC2", estado="REPORTADO")
        service = DescartarCasoService()

        # Act
        result = service.descartar(idaccidente=aid, idusuario=2)

        # Assert
        assert result["estado"] == ESTADO_DESCARTADO

    def test_descartar_con_despacho_creado_raises(
        self, mock_pinot, mock_kafka, seed_accidente
    ):
        """Con un despacho ya creado, descartar deja de ser posible."""
        # Arrange
        aid = seed_accidente(idaccidente="ACC-D-SVC4", estado="REPORTADO")
        service = DescartarCasoService()
        service.despacho_repo = SimpleNamespace(
            list_by_accidente=lambda _id: [{"iddespacho": 1}]
        )

        # Act / Assert
        with pytest.raises(ConflictError, match="despachos"):
            service.descartar(idaccidente=aid, idusuario=2)

    def test_descartar_caso_ya_cerrado_raises(
        self, mock_pinot, mock_kafka, seed_accidente
    ):
        # Arrange
        aid = seed_accidente(idaccidente="ACC-D-SVC5", estado="CERRADO")
        service = DescartarCasoService()

        # Act / Assert
        with pytest.raises(ConflictError):
            service.descartar(idaccidente=aid, idusuario=2)
