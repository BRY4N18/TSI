import time

import pytest

from apps.accidentes.services.validacion_accidente_service import ValidacionAccidenteService
from core.repositories.accidentes.accidente_repository import AccidenteRepository


@pytest.mark.service
class TestDuplicadoDetection:
    def test_validate_when_nearby_within_5min_adds_advertencia(self, mock_pinot, mock_kafka):
        # Arrange
        now = int(time.time() * 1000)
        repo = AccidenteRepository()
        repo.create(
            {
                "idaccidente": "ACC-OLD",
                "latitudinicio": 19.4326,
                "longitudinicio": -99.1332,
                "fechahoraaccidente": now,
                "activo": True,
            }
        )
        service = ValidacionAccidenteService()
        data = {
            "latitudinicio": 19.43261,
            "longitudinicio": -99.13321,
            "fechahoraaccidente": now + 60_000,
            "descripcion": "dup",
            "idcalle": 1,
        }

        # Act
        result = service.validate_registro(data, now_ms=now + 60_000)

        # Assert
        assert result.has_advertencias
        assert any(a["code"] == "duplicado_posible" for a in result.advertencias)
        assert result.duplicate_candidates[0]["idaccidente"] == "ACC-OLD"

    def test_suggest_parent_returns_oldest_candidate(self, mock_pinot, mock_kafka):
        # Arrange
        service = ValidacionAccidenteService()
        candidates = [
            {"idaccidente": "ACC-NEW", "fechahoraaccidente": 2000},
            {"idaccidente": "ACC-OLD", "fechahoraaccidente": 1000},
        ]

        # Act
        parent = service.suggest_parent_id(candidates)

        # Assert
        assert parent == "ACC-OLD"
