import pytest

from apps.red_operativa.services.reevaluacion_region_service import ReevaluacionRegionService


@pytest.mark.service
class TestReevaluacionRegionService:
    def test_reevaluar_when_produccion_a_en_alerta_actualiza_estadoregion(
        self, mock_pinot, mock_kafka
    ):
        # Arrange
        service = ReevaluacionRegionService()
        service.region_repo.update(1, {"estadoregion": "Producción"})

        # Act
        result = service.reevaluar(1, estadoregion_nuevo="En_Alerta", motivo="Latencia alta")

        # Assert
        assert result["estadoregion"] == "En_Alerta"

    def test_reevaluar_when_produccion_a_despublicada_con_casos_activos_no_cancela(
        self, mock_pinot, mock_kafka, pinot_store
    ):
        # Arrange
        service = ReevaluacionRegionService()
        service.region_repo.update(1, {"estadoregion": "Producción"})
        pinot_store["Fact_Accidente"].append({"idaccidente": "acc-1", "idcalle": 1, "activo": True})

        # Act
        result = service.reevaluar(1, estadoregion_nuevo="Despublicada", motivo="Sin cobertura")

        # Assert: la despublicación procede igual — solo bloquea casos nuevos, no cancela existentes
        assert result["estadoregion"] == "Despublicada"
        assert pinot_store["Fact_Accidente"][0]["activo"] is True

    def test_reevaluar_when_estado_origen_invalido_raises(self, mock_pinot, mock_kafka):
        # Arrange
        service = ReevaluacionRegionService()
        service.region_repo.update(1, {"estadoregion": "En_Validación"})

        # Act & Assert
        with pytest.raises(ValueError):
            service.reevaluar(1, estadoregion_nuevo="En_Alerta", motivo="x")

    def test_reevaluar_when_region_inexistente_raises(self, mock_pinot, mock_kafka):
        # Arrange
        service = ReevaluacionRegionService()

        # Act & Assert
        with pytest.raises(LookupError):
            service.reevaluar(999, estadoregion_nuevo="En_Alerta", motivo="x")
