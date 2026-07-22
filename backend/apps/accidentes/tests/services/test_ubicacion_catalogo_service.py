from unittest.mock import MagicMock

import pytest

from apps.accidentes.services.ubicacion_catalogo_service import UbicacionCatalogoService


@pytest.mark.service
class TestUbicacionCatalogoService:
    def test_listar_paises_delegates_to_repo(self):
        # Arrange
        repo = MagicMock()
        repo.listar_paises.return_value = [{"id": 1, "nombre": "México"}]
        service = UbicacionCatalogoService(repo=repo)

        # Act
        result = service.listar_paises()

        # Assert
        assert result == [{"id": 1, "nombre": "México"}]
        repo.listar_paises.assert_called_once()

    def test_listar_calles_delegates_to_repo_with_idciudad(self):
        # Arrange
        repo = MagicMock()
        repo.listar_calles.return_value = [{"id": 1, "nombre": "Av. Reforma"}]
        service = UbicacionCatalogoService(repo=repo)

        # Act
        result = service.listar_calles(1)

        # Assert
        assert result == [{"id": 1, "nombre": "Av. Reforma"}]
        repo.listar_calles.assert_called_once_with(1)
