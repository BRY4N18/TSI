import pytest

from core.repositories.accidentes.ubicacion_catalogo_repository import (
    UbicacionCatalogoRepository,
)


@pytest.mark.repository
class TestUbicacionCatalogoRepository:
    def test_listar_paises_returns_active_countries(self, mock_pinot):
        # Arrange
        repo = UbicacionCatalogoRepository()

        # Act
        paises = repo.listar_paises()

        # Assert
        assert paises == [{"id": 1, "nombre": "México"}]

    def test_listar_estados_filters_by_idpais(self, mock_pinot):
        # Arrange
        repo = UbicacionCatalogoRepository()

        # Act
        estados = repo.listar_estados(1)

        # Assert
        assert {e["id"] for e in estados} == {1, 2}

    def test_listar_condados_filters_by_idestado(self, mock_pinot):
        # Arrange
        repo = UbicacionCatalogoRepository()

        # Act
        condados = repo.listar_condados(1)

        # Assert
        assert {c["id"] for c in condados} == {1, 2}

    def test_listar_ciudades_filters_by_idcondado(self, mock_pinot):
        # Arrange
        repo = UbicacionCatalogoRepository()

        # Act
        ciudades = repo.listar_ciudades(1)

        # Assert
        assert ciudades == [{"id": 1, "nombre": "Ciudad de México"}]

    def test_listar_calles_filters_by_idciudad(self, mock_pinot):
        # Arrange
        repo = UbicacionCatalogoRepository()

        # Act
        calles = repo.listar_calles(1)

        # Assert
        assert calles == [{"id": 1, "nombre": "Av. Reforma"}]

    def test_listar_estados_when_idpais_has_no_children_returns_empty(self, mock_pinot):
        # Arrange
        repo = UbicacionCatalogoRepository()

        # Act
        estados = repo.listar_estados(999)

        # Assert
        assert estados == []
