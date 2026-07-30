import pytest

from apps.accidentes.services.enriquecimiento_clima_service import (
    EnriquecimientoClimaService,
)


@pytest.mark.service
class TestEnriquecimientoClimaService:
    def test_upsert_when_valid_returns_activo(self, mock_pinot, mock_kafka, accidente_activo):
        # Arrange
        service = EnriquecimientoClimaService()

        # Act
        result = service.upsert(
            idaccidente=accidente_activo,
            idusuario=7,
            idperiododia=1,
            idestadoclima=2,
        )

        # Assert
        assert result["activo"] is True
        assert result["idperiododia"] == 1

    def test_upsert_when_caso_inactivo_raises(self, mock_pinot, mock_kafka, seed_accidente):
        # Arrange
        from apps.accidentes.domain_constants import ESTADO_CERRADO

        idaccidente = seed_accidente(idaccidente="ACC-INACTIVO", estado=ESTADO_CERRADO)
        service = EnriquecimientoClimaService()

        # Act / Assert
        with pytest.raises(ValueError, match="no está activo"):
            service.upsert(
                idaccidente=idaccidente,
                idusuario=7,
                idperiododia=1,
                idestadoclima=None,
            )
