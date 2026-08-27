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
            # RN-REG-012 — obligatorio y >= 1.
            "numvehiculos": 1,
        }

        # Act
        result = service.validate_registro(data, now_ms=now)

        # Assert
        assert result.is_blocked is False
        assert result.has_advertencias is False

    def test_validate_registro_when_sin_vehiculos_bloquea(self, mock_pinot, mock_kafka):
        """RN-REG-012 (hallazgo #8): sin `numvehiculos` la unidad no podia
        registrar ni un solo conductor en sitio, porque ese numero es el tope."""
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
        assert result.is_blocked is True
        assert any(e["code"] == "numvehiculos_requerido" for e in result.blocking_errors)

    def test_validate_registro_when_severidad_incoherente_bloquea(self, mock_pinot, mock_kafka):
        """RN-SEV-COHERENCIA (hallazgo #4): 200 heridos no pueden ser 'Leve'."""
        # Arrange
        service = ValidacionAccidenteService()
        now = int(time.time() * 1000)
        data = {
            "latitudinicio": 19.43,
            "longitudinicio": -99.13,
            "fechahoraaccidente": now,
            "descripcion": "Test",
            "idcalle": 1,
            "numvehiculos": 3,
            "idseveridad": 1,
            "numheridos": 200,
        }

        # Act
        result = service.validate_registro(data, now_ms=now)

        # Assert
        assert result.is_blocked is True
        assert any(e["code"] == "severidad_incoherente" for e in result.blocking_errors)

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
