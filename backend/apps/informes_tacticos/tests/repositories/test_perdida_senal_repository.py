from unittest.mock import MagicMock

import pytest

from core.repositories.informes_tacticos.perdida_senal_repository import PerdidaSenalRepository


@pytest.mark.repository
class TestPerdidaSenalRepository:
    def test_returns_rows_and_ultima_corrida_when_materializado(self):
        # Arrange
        ch = MagicMock()
        fila = {"idunidademergencia": 1, "idaccidente": "A1", "duracion_seg": 200}
        ch.query.side_effect = [[fila], [{"ultima": "2026-08-02 04:15:15"}]]
        pinot = MagicMock()
        pinot.query.return_value = [{"idunidademergencia": 1, "unidademergencia": "Humo", "placa": "HUMO-99"}]
        repo = PerdidaSenalRepository(clickhouse=ch, pinot=pinot)

        # Act
        rows, ultima = repo.consultar("2026-08-01", "2026-08-31")

        # Assert
        assert rows == [{**fila, "unidad_nombre": "Humo", "unidad_placa": "HUMO-99"}]
        assert ultima == "2026-08-02 04:15:15"

    def test_returns_empty_list_when_no_gaps_but_dag_already_ran(self):
        # Arrange: sin filas para el período, pero sí hay corridas previas (otro período)
        ch = MagicMock()
        ch.query.side_effect = [[], [{"ultima": "2026-08-02 04:15:15"}]]
        repo = PerdidaSenalRepository(clickhouse=ch, pinot=MagicMock())

        # Act
        rows, ultima = repo.consultar("1999-01-01", "1999-01-31")

        # Assert
        assert rows == []
        assert ultima == "2026-08-02 04:15:15"

    def test_returns_none_when_dag_never_ran(self):
        # Arrange: tabla completamente vacía (FR-008: "no materializado todavía")
        ch = MagicMock()
        ch.query.side_effect = [[], [{"ultima": None}]]
        repo = PerdidaSenalRepository(clickhouse=ch, pinot=MagicMock())

        # Act
        rows, ultima = repo.consultar("2026-08-01", "2026-08-31")

        # Assert
        assert rows is None
        assert ultima is None
