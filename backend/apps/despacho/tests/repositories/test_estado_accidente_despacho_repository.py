import pytest

from apps.accidentes.domain_constants import ESTADO_ASIGNADO, ESTADO_BUSCANDO_UNIDAD, ESTADO_REPORTADO
from core.repositories.accidentes.estado_accidente_repository import EstadoAccidenteRepository
from core.repositories.despacho.estado_accidente_despacho_repository import (
    EstadoAccidenteDespachoRepository,
)


@pytest.mark.repository
class TestEstadoAccidenteDespachoRepository:
    def test_publish_buscando_unidad_if_first_when_reportado_transitions(
        self, mock_pinot, mock_kafka
    ):
        # Arrange
        estado_repo = EstadoAccidenteRepository()
        estado_repo.append_estado(idaccidente="ACC-EST-1", estado=ESTADO_REPORTADO, idusuario=2)
        repo = EstadoAccidenteDespachoRepository(estado_repo=estado_repo)

        # Act
        record = repo.publish_buscando_unidad_if_first(idaccidente="ACC-EST-1", idusuario=2)
        current = estado_repo.get_current_estado("ACC-EST-1")

        # Assert
        assert record is not None
        assert current == ESTADO_BUSCANDO_UNIDAD

    def test_publish_asignado_if_first_confirmed_when_not_yet_asignado(
        self, mock_pinot, mock_kafka
    ):
        # Arrange
        estado_repo = EstadoAccidenteRepository()
        estado_repo.append_estado(idaccidente="ACC-EST-2", estado=ESTADO_REPORTADO, idusuario=2)
        estado_repo.append_estado(
            idaccidente="ACC-EST-2", estado=ESTADO_BUSCANDO_UNIDAD, idusuario=2
        )
        repo = EstadoAccidenteDespachoRepository(estado_repo=estado_repo)

        # Act
        record = repo.publish_asignado_if_first_confirmed(idaccidente="ACC-EST-2", idusuario=2)
        current = estado_repo.get_current_estado("ACC-EST-2")

        # Assert
        assert record is not None
        assert current == ESTADO_ASIGNADO

    def test_publish_buscando_unidad_if_first_when_already_buscando_returns_none(
        self, mock_pinot, mock_kafka
    ):
        # Arrange
        estado_repo = EstadoAccidenteRepository()
        estado_repo.append_estado(
            idaccidente="ACC-EST-3", estado=ESTADO_BUSCANDO_UNIDAD, idusuario=2
        )
        repo = EstadoAccidenteDespachoRepository(estado_repo=estado_repo)

        # Act
        record = repo.publish_buscando_unidad_if_first(idaccidente="ACC-EST-3", idusuario=2)

        # Assert
        assert record is None
