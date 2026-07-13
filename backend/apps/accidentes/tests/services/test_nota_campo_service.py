import pytest

from apps.accidentes.services.nota_campo_service import NotaCampoService


@pytest.mark.service
class TestNotaCampoService:
    def test_registrar_when_caso_activo_returns_sincronizado(
        self, mock_pinot, mock_kafka, accidente_activo
    ):
        # Arrange
        service = NotaCampoService()

        # Act
        result = service.registrar(
            idaccidente=accidente_activo,
            idusuario=7,
            nota="Condiciones de lluvia",
            tipo="Condiciones del sitio",
        )

        # Assert
        assert result["sincronizado"] is True
        assert result["tipo"] == "Condiciones del sitio"
