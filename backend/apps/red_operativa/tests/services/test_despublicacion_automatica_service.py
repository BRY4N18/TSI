import pytest

from apps.red_operativa.services.despublicacion_automatica_service import (
    DespublicacionAutomaticaService,
)


def _sin_cobertura(pinot_store):
    """Desactiva unidades en condados de la región 1 para permitir O62."""
    for u in pinot_store["Dim_UnidadEmergencia"]:
        if u.get("idcondado") in (1, 2):
            u["activo"] = False


@pytest.mark.service
class TestDespublicacionAutomaticaService:
    def test_ejecutar_when_produccion_sin_cobertura_despublica(
        self, mock_pinot, mock_kafka, pinot_store
    ):
        _sin_cobertura(pinot_store)
        service = DespublicacionAutomaticaService()
        service.region_repo.update(1, {"estadoregion": "Producción"})

        result = service.ejecutar(1)

        assert result["estadoregion"] == "Despublicada"
        assert result["unidades_activas"] == 0
        assert "idusuario" not in result

    def test_ejecutar_when_en_alerta_sin_cobertura_despublica(
        self, mock_pinot, mock_kafka, pinot_store
    ):
        _sin_cobertura(pinot_store)
        service = DespublicacionAutomaticaService()
        service.region_repo.update(1, {"estadoregion": "En_Alerta"})

        result = service.ejecutar(1)

        assert result["estadoregion"] == "Despublicada"

    def test_ejecutar_when_hay_unidades_activas_raises(self, mock_pinot, mock_kafka):
        service = DespublicacionAutomaticaService()
        service.region_repo.update(1, {"estadoregion": "Producción"})

        with pytest.raises(ValueError, match="unidad"):
            service.ejecutar(1)

    def test_ejecutar_es_idempotente_segunda_invocacion_no_duplica_transicion(
        self, mock_pinot, mock_kafka, pinot_store
    ):
        _sin_cobertura(pinot_store)
        service = DespublicacionAutomaticaService()
        service.region_repo.update(1, {"estadoregion": "Producción"})
        service.ejecutar(1)
        eventos_tras_primera = len(mock_kafka)

        with pytest.raises(ValueError):
            service.ejecutar(1)
        assert len(mock_kafka) == eventos_tras_primera

    def test_ejecutar_when_estado_origen_invalido_raises(self, mock_pinot, mock_kafka):
        service = DespublicacionAutomaticaService()
        service.region_repo.update(1, {"estadoregion": "En_Validación"})

        with pytest.raises(ValueError):
            service.ejecutar(1)

    def test_ejecutar_when_region_inexistente_raises(self, mock_pinot, mock_kafka):
        service = DespublicacionAutomaticaService()

        with pytest.raises(LookupError):
            service.ejecutar(999)
