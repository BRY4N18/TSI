from unittest.mock import MagicMock

import pytest

from core.repositories.informes_tacticos.indice_calidad_repository import IndiceCalidadRepository


@pytest.mark.repository
class TestIndiceCalidadRepository:
    def test_returns_full_series_not_just_last_value(self):
        # Arrange (Acceptance Scenario 2 de la spec: serie completa, no solo el último)
        ch = MagicMock()
        serie = [
            {"periodo": "2026-07-01", "indice_consolidado": 0.8},
            {"periodo": "2026-07-02", "indice_consolidado": 0.85},
        ]
        ch.query.side_effect = [serie, [{"ultima": "2026-08-02 05:00:00"}]]
        repo = IndiceCalidadRepository(clickhouse=ch)

        # Act
        rows, ultima = repo.consultar("2026-07-01", "2026-07-31")

        # Assert
        assert rows == serie
        assert len(rows) == 2
        assert ultima == "2026-08-02 05:00:00"

    def test_returns_none_when_never_ran(self):
        ch = MagicMock()
        ch.query.side_effect = [[], [{"ultima": None}]]
        repo = IndiceCalidadRepository(clickhouse=ch)

        rows, ultima = repo.consultar("2026-07-01", "2026-07-31")

        assert rows is None
        assert ultima is None
