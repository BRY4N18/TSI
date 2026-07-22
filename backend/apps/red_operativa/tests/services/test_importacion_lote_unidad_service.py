import pytest

from apps.red_operativa.services.importacion_lote_unidad_service import (
    ImportacionLoteUnidadService,
)


@pytest.mark.service
class TestImportacionLoteUnidadService:
    def _fila_valida(self, **overrides):
        fila = {
            "idcliente": 1,
            "idcondado": 1,
            "tipopropiedad": "Externa",
            "placa": "LOTE-001",
            "contactoproveedor": "555",
            "unidademergencia": "Ambulancia Lote",
            "tipounidademergencia": "Ambulancia",
        }
        fila.update(overrides)
        return fila

    def test_importar_when_todas_validas_inserta_todas(self, mock_pinot, mock_kafka):
        # Arrange
        service = ImportacionLoteUnidadService()
        filas = [self._fila_valida(placa=f"LOTE-{i}") for i in range(3)]

        # Act
        result = service.importar(filas)

        # Assert
        assert result["insertadas"] == 3
        assert result["fallidas"] == []

    def test_importar_when_una_fila_invalida_no_inserta_ninguna(self, mock_pinot, mock_kafka):
        # Arrange
        service = ImportacionLoteUnidadService()
        filas = [
            self._fila_valida(placa="LOTE-A"),
            self._fila_valida(placa="LOTE-A"),
        ]

        # Act
        result = service.importar(filas)

        # Assert
        assert result["insertadas"] == 0
        assert len(result["fallidas"]) == 1
        assert result["fallidas"][0]["fila"] == 2

    def test_importar_when_excede_500_filas_raises(self, mock_pinot, mock_kafka):
        # Arrange
        service = ImportacionLoteUnidadService()
        filas = [self._fila_valida(placa=f"LOTE-{i}") for i in range(501)]

        # Act & Assert
        with pytest.raises(ValueError):
            service.importar(filas)
