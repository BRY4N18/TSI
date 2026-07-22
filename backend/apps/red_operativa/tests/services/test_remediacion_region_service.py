import pytest

from apps.red_operativa.services.remediacion_region_service import RemediacionRegionService


@pytest.mark.service
class TestRemediacionRegionService:
    def test_historial_delega_a_repositorio_sin_transformar_orden(self, mock_pinot, mock_kafka):
        # Arrange
        service = RemediacionRegionService()
        service.validacion_repo.create(
            {
                "idregionoperativa": 1,
                "idusuario": 1,
                "resultado": "Rechazada",
                "motivo": "a",
                "fechahora": "2026-01-01T00:00:00+00:00",
            }
        )
        service.validacion_repo.create(
            {
                "idregionoperativa": 1,
                "idusuario": 9,
                "resultado": "Aprobada",
                "fechahora": "2026-01-02T00:00:00+00:00",
            }
        )

        # Act
        historial = service.historial(1)

        # Assert
        assert [h["resultado"] for h in historial] == ["Rechazada", "Aprobada"]

    def test_rechazo_definitivo_when_en_validacion_marca_inactivo(self, mock_pinot, mock_kafka):
        # Arrange
        service = RemediacionRegionService()
        service.region_repo.update(1, {"estadoregion": "En_Validación"})

        # Act
        result = service.rechazo_definitivo(1)

        # Assert
        assert result["activo"] is False
        region = service.region_repo.find_by_id(1)
        assert region["estadoregion"] == "En_Validación"

    def test_rechazo_definitivo_when_produccion_raises(self, mock_pinot, mock_kafka):
        # Arrange
        service = RemediacionRegionService()
        service.region_repo.update(1, {"estadoregion": "Producción"})

        # Act & Assert
        with pytest.raises(ValueError):
            service.rechazo_definitivo(1)

    def test_rechazo_definitivo_no_inserta_fila_de_validacion(self, mock_pinot, mock_kafka):
        # Arrange
        service = RemediacionRegionService()
        service.region_repo.update(1, {"estadoregion": "En_Validación"})

        # Act
        service.rechazo_definitivo(1)

        # Assert
        assert service.validacion_repo.list_by_region(1) == []

    def test_rechazo_definitivo_when_inexistente_raises(self, mock_pinot, mock_kafka):
        # Arrange
        service = RemediacionRegionService()

        # Act & Assert
        with pytest.raises(LookupError):
            service.rechazo_definitivo(999)
