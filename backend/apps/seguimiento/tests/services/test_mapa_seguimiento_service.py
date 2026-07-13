import pytest

from apps.seguimiento.services.mapa_seguimiento_service import MapaSeguimientoService


@pytest.mark.service
class TestMapaSeguimientoService:
    def test_obtener_mapa_when_activo_includes_accidente(
        self,
        mock_pinot,
        mock_kafka,
        accidente_activo,
        despacho_confirmado_unidad,
    ):
        # Arrange
        svc = MapaSeguimientoService()

        # Act
        result = svc.obtener_mapa()

        # Assert
        assert "accidentes_activos" in result
        assert "unidades" in result
        assert any(a["idaccidente"] == accidente_activo for a in result["accidentes_activos"])

    def test_obtener_seguimiento_accidente_when_exists_returns_despachos(
        self,
        mock_pinot,
        mock_kafka,
        accidente_activo,
        despacho_confirmado_unidad,
    ):
        # Arrange
        svc = MapaSeguimientoService()

        # Act
        result = svc.obtener_seguimiento_accidente(accidente_activo)

        # Assert
        assert result is not None
        assert result["idaccidente"] == accidente_activo
        assert len(result["despachos"]) >= 1

    def test_obtener_seguimiento_accidente_when_missing_returns_none(
        self,
        mock_pinot,
        mock_kafka,
    ):
        # Arrange
        svc = MapaSeguimientoService()

        # Act
        result = svc.obtener_seguimiento_accidente("ACC-INEXISTENTE")

        # Assert
        assert result is None
