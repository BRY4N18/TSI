import pytest

from apps.red_operativa.services.despublicacion_automatica_service import (
    DespublicacionAutomaticaService,
)


@pytest.mark.service
class TestDespublicacionAutomaticaService:
    def test_ejecutar_when_produccion_actualiza_a_despublicada(self, mock_pinot, mock_kafka):
        # Arrange
        service = DespublicacionAutomaticaService()
        service.region_repo.update(1, {"estadoregion": "Producción"})

        # Act
        result = service.ejecutar(1)

        # Assert
        assert result["estadoregion"] == "Despublicada"
        assert "idusuario" not in result

    def test_ejecutar_when_en_alerta_actualiza_a_despublicada(self, mock_pinot, mock_kafka):
        # Arrange
        service = DespublicacionAutomaticaService()
        service.region_repo.update(1, {"estadoregion": "En_Alerta"})

        # Act
        result = service.ejecutar(1)

        # Assert
        assert result["estadoregion"] == "Despublicada"

    def test_ejecutar_es_idempotente_segunda_invocacion_no_duplica_transicion(
        self, mock_pinot, mock_kafka
    ):
        # Arrange: primera invocación despublica; una segunda invocación sobre una
        # región ya Despublicada debe fallar limpiamente en vez de re-publicar el
        # evento — evita duplicar la transición ante reintentos del disparador.
        service = DespublicacionAutomaticaService()
        service.region_repo.update(1, {"estadoregion": "Producción"})
        service.ejecutar(1)
        eventos_tras_primera = len(mock_kafka)

        # Act & Assert
        with pytest.raises(ValueError):
            service.ejecutar(1)
        assert len(mock_kafka) == eventos_tras_primera

    def test_ejecutar_when_estado_origen_invalido_raises(self, mock_pinot, mock_kafka):
        # Arrange
        service = DespublicacionAutomaticaService()
        service.region_repo.update(1, {"estadoregion": "En_Validación"})

        # Act & Assert
        with pytest.raises(ValueError):
            service.ejecutar(1)

    def test_ejecutar_when_region_inexistente_raises(self, mock_pinot, mock_kafka):
        # Arrange
        service = DespublicacionAutomaticaService()

        # Act & Assert
        with pytest.raises(LookupError):
            service.ejecutar(999)
