import pytest

from apps.accidentes.services.enriquecimiento_elemento_fisico_service import (
    EnriquecimientoElementoFisicoService,
)


@pytest.mark.service
class TestEnriquecimientoElementoFisicoService:
    def test_agregar_and_desactivar_when_valid(
        self, mock_pinot, mock_kafka, accidente_activo
    ):
        # Arrange
        service = EnriquecimientoElementoFisicoService()

        # Act
        created = service.agregar(
            idaccidente=accidente_activo, idelementofisico=1, idusuario=7
        )
        deleted = service.desactivar(
            idaccidente=accidente_activo,
            idelementosfisicosaccidente=created["idelementosfisicosaccidente"],
            idusuario=7,
        )
        items = service.listar(accidente_activo)

        # Assert
        assert created["elementofisico"] == "Semáforo"
        assert deleted["activo"] is False
        assert items == []
