import time

import pytest

from apps.accidentes.services.validacion_accidente_service import (
    ValidacionAccidenteService,
)


@pytest.mark.service
class TestValidacionAccidenteService:
    def test_validate_registro_when_valid_returns_no_blockers(self, mock_pinot, mock_kafka):
        # Arrange
        service = ValidacionAccidenteService()
        now = int(time.time() * 1000)
        data = {
            "latitudinicio": 19.43,
            "longitudinicio": -99.13,
            "fechahoraaccidente": now,
            "descripcion": "Test",
            "idcalle": 1,
        }

        # Act
        result = service.validate_registro(data, now_ms=now)

        # Assert
        assert result.is_blocked is False
        assert result.has_advertencias is False

    def test_validate_registro_when_retrospective_without_justification_blocks(
        self, mock_pinot, mock_kafka
    ):
        # Arrange
        service = ValidacionAccidenteService()
        now = int(time.time() * 1000)
        data = {
            "latitudinicio": 19.43,
            "longitudinicio": -99.13,
            "fechahoraaccidente": now - (25 * 60 * 60 * 1000),
            "descripcion": "Test",
            "idcalle": 1,
        }

        # Act
        result = service.validate_registro(data, now_ms=now)

        # Assert
        assert result.is_blocked is True
