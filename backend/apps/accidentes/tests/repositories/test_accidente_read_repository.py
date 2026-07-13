import pytest

from apps.accidentes.domain_constants import ESTADO_CERRADO, ESTADO_REPORTADO
from core.repositories.accidentes.accidente_repository import AccidenteRepository
from core.repositories.accidentes.estado_accidente_repository import EstadoAccidenteRepository
from core.repositories.evidencia.accidente_read_repository import AccidenteReadRepository


@pytest.mark.repository
class TestAccidenteReadRepository:
    def test_is_caso_activo_when_reportado_returns_true(self, mock_pinot, mock_kafka):
        # Arrange
        repo = AccidenteReadRepository()
        AccidenteRepository().create({"idaccidente": "ACC-ACT", "activo": True})
        EstadoAccidenteRepository().append_estado(
            idaccidente="ACC-ACT", estado=ESTADO_REPORTADO, idusuario=2
        )

        # Act
        result = repo.is_caso_activo("ACC-ACT")

        # Assert
        assert result is True

    def test_is_caso_activo_when_cerrado_returns_false(self, mock_pinot, mock_kafka):
        # Arrange
        repo = AccidenteReadRepository()
        AccidenteRepository().create({"idaccidente": "ACC-CLO", "activo": True})
        EstadoAccidenteRepository().append_estado(
            idaccidente="ACC-CLO", estado=ESTADO_CERRADO, idusuario=2
        )

        # Act
        result = repo.is_caso_activo("ACC-CLO")

        # Assert
        assert result is False
