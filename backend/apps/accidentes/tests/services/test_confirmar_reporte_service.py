import pytest

from apps.accidentes.services.confirmar_reporte_service import ConfirmarReporteService, ConflictError
from core.repositories.accidentes.estado_accidente_repository import EstadoAccidenteRepository


@pytest.mark.service
class TestConfirmarReporteService:
    def test_confirmar_when_borrador_transitions_to_reportado(self, mock_pinot, mock_kafka):
        # Arrange
        estado_repo = EstadoAccidenteRepository()
        estado_repo.append_estado(idaccidente="ACC-1", estado="BORRADOR", idusuario=2)
        service = ConfirmarReporteService(estado_repo=estado_repo)

        # Act
        result = service.confirmar(idaccidente="ACC-1", idusuario=2, confirmacion=True)

        # Assert
        assert result["estado"] == "REPORTADO"

    def test_confirmar_when_not_borrador_raises_conflict(self, mock_pinot, mock_kafka):
        # Arrange
        estado_repo = EstadoAccidenteRepository()
        estado_repo.append_estado(idaccidente="ACC-2", estado="REPORTADO", idusuario=2)
        service = ConfirmarReporteService(estado_repo=estado_repo)

        # Act / Assert
        with pytest.raises(ConflictError):
            service.confirmar(idaccidente="ACC-2", idusuario=2, confirmacion=True)
