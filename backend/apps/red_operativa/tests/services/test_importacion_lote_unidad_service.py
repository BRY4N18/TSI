from unittest.mock import MagicMock

import pytest

from apps.red_operativa.services.importacion_lote_unidad_service import (
    ImportacionLoteUnidadService,
)

PROVEEDOR = {"user_id": 3, "roles": ["Cliente"]}


@pytest.mark.service
class TestImportacionLoteUnidadService:
    def _fila_valida(self, **overrides):
        fila = {
            "idcondado": 1,
            "tipopropiedad": "Externa",
            "placa": "LOTE-001",
            "contactoproveedor": "555",
            "unidademergencia": "Ambulancia Lote",
            "tipounidademergencia": "Ambulancia",
            "gmail": "lote001@test.com",
        }
        fila.update(overrides)
        return fila

    def test_importar_when_todas_validas_inserta_todas(self, mock_pinot, mock_kafka):
        # Arrange
        service = ImportacionLoteUnidadService()
        filas = [
            self._fila_valida(placa=f"LOTE-{i}", gmail=f"lote{i}@test.com") for i in range(3)
        ]

        # Act
        result = service.importar(filas, **PROVEEDOR)

        # Assert
        assert result["insertadas"] == 3
        assert result["usuarios_creados"] == 3
        assert result["fallidas"] == []

    def test_importar_when_una_fila_invalida_no_inserta_ninguna(self, mock_pinot, mock_kafka):
        # Arrange
        service = ImportacionLoteUnidadService()
        filas = [
            self._fila_valida(placa="LOTE-A", gmail="a@test.com"),
            self._fila_valida(placa="LOTE-A", gmail="b@test.com"),
        ]

        # Act
        result = service.importar(filas, **PROVEEDOR)

        # Assert
        assert result["insertadas"] == 0
        assert len(result["fallidas"]) == 1
        assert result["fallidas"][0]["fila"] == 2

    def test_importar_when_excede_500_filas_raises(self, mock_pinot, mock_kafka):
        # Arrange
        service = ImportacionLoteUnidadService()
        filas = [
            self._fila_valida(placa=f"LOTE-{i}", gmail=f"x{i}@t.com") for i in range(501)
        ]

        # Act & Assert
        with pytest.raises(ValueError):
            service.importar(filas, **PROVEEDOR)

    def test_importar_when_credencial_falla_revierte_lote(self, mock_pinot, mock_kafka, pinot_store):
        # Arrange
        service = ImportacionLoteUnidadService()
        service.credential_repo = MagicMock()
        service.credential_repo.create_temporary.side_effect = RuntimeError("smtp/cred fail")
        before = len(pinot_store["Dim_UnidadEmergencia"])
        filas = [
            self._fila_valida(placa="LOTE-C1", gmail="c1@test.com"),
            self._fila_valida(placa="LOTE-C2", gmail="c2@test.com"),
        ]

        # Act
        result = service.importar(filas, **PROVEEDOR)

        # Assert
        assert result["insertadas"] == 0
        assert result["usuarios_creados"] == 0
        assert result["fallidas"]
        activas_nuevas = [
            u
            for u in pinot_store["Dim_UnidadEmergencia"][before:]
            if u.get("placa", "").startswith("LOTE-C") and u.get("activo")
        ]
        assert activas_nuevas == []
