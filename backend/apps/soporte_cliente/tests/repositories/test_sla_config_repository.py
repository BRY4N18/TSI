import pytest

from core.repositories.soporte.sla_config_repository import SLAConfigRepository


@pytest.mark.repository
class TestSLAConfigRepository:
    def test_find_vigente_when_match_returns_row(self, mock_pinot, mock_kafka):
        # Arrange
        repo = SLAConfigRepository()

        # Act
        regla = repo.find_vigente(idplan=1, tipoincidencia="tecnica", prioridad="alta")

        # Assert
        assert regla is not None
        assert regla["idslaconfig"] == 1

    def test_modificar_regla_when_valid_desactiva_anterior_y_crea_nueva(self, mock_pinot, mock_kafka):
        # Arrange
        repo = SLAConfigRepository()

        # Act
        nueva = repo.modificar_regla(1, tiemporespuestamax=1800, tiemporesolucionmax=43200)
        anterior = repo.find_by_id(1)

        # Assert
        assert anterior["activo"] is False
        assert nueva["activo"] is True
        assert nueva["tiemporespuestamax"] == 1800
        assert len(mock_kafka) == 2

    def test_desactivar_when_not_found_raises(self, mock_pinot, mock_kafka):
        # Arrange
        repo = SLAConfigRepository()

        # Act / Assert
        with pytest.raises(LookupError):
            repo.desactivar(999)
