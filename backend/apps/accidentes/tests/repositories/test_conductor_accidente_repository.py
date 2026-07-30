import pytest

from core.repositories.evidencia.conductor_accidente_repository import (
    ConductorAccidenteRepository,
)
from core.repositories.evidencia.conductor_repository import ConductorRepository
from core.repositories.evidencia.vehiculo_repository import VehiculoRepository


@pytest.mark.repository
class TestConductorAccidenteRepository:
    def test_create_and_soft_delete_when_valid(self, mock_pinot, mock_kafka):
        # Arrange
        conductor = ConductorRepository().create(
            {"identificacion": "099", "nombres": "Luis", "apellidos": "Ruiz"}
        )
        vehiculo = VehiculoRepository().create({"tipovehiculo": "Moto"})
        repo = ConductorAccidenteRepository()

        # Act
        vinculo = repo.create(
            idaccidente="ACC-1",
            idconductor=conductor["idconductor"],
            idestadoconductor=1,
            idvehiculo=vehiculo["idvehiculo"],
            idusuario=7,
        )
        deleted = repo.soft_delete(
            idconductoraccidente=vinculo["idconductoraccidente"], idusuario=7
        )
        activos = repo.list_activos_by_accidente("ACC-1")

        # Assert
        assert deleted["activo"] is False
        assert activos == []
