import pytest

from apps.accidentes.services.consulta_enriquecimiento_service import (
    ConsultaEnriquecimientoService,
)
from apps.accidentes.services.enriquecimiento_clima_service import (
    EnriquecimientoClimaService,
)
from apps.accidentes.services.enriquecimiento_elemento_fisico_service import (
    EnriquecimientoElementoFisicoService,
)


@pytest.mark.service
class TestConsultaEnriquecimientoService:
    def test_obtener_when_enriched_returns_sections(
        self, mock_pinot, mock_kafka, accidente_activo
    ):
        # Arrange
        EnriquecimientoClimaService().upsert(
            idaccidente=accidente_activo,
            idusuario=7,
            idperiododia=1,
            idestadoclima=2,
        )
        EnriquecimientoElementoFisicoService().agregar(
            idaccidente=accidente_activo, idelementofisico=1, idusuario=7
        )
        service = ConsultaEnriquecimientoService()

        # Act
        data = service.obtener(accidente_activo, idusuario=7)

        # Assert
        assert data["idaccidente"] == accidente_activo
        assert data["clima"]["idperiododia"] == 1
        assert len(data["elementos_fisicos"]) == 1
        assert data["conductores"] == []
        assert data["implicados"] == []
