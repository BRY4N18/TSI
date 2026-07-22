import pytest

from apps.soporte_cliente.services.clasificacion_automatica_service import (
    ClasificacionAutomaticaService,
)


@pytest.mark.service
class TestClasificacionAutomaticaService:
    def test_clasificar_when_emergencia_activa_returns_critico(
        self, mock_pinot, mock_kafka, accidente_activo
    ):
        # Arrange
        service = ClasificacionAutomaticaService()

        # Act
        resultado = service.clasificar(
            tipo="tecnico",
            asunto="Consulta",
            descripcion="Sobre mi caso",
            idaccidente=accidente_activo,
        )

        # Assert
        assert resultado == {"tipo_incidencia": "emergencia_activa", "prioridad": "crítico"}

    def test_clasificar_when_keyword_tecnica_returns_tipo_tecnica(self, mock_pinot, mock_kafka):
        # Arrange
        service = ClasificacionAutomaticaService()

        # Act
        resultado = service.clasificar(
            tipo="tecnico", asunto="La API no responde", descripcion="error 500 constante"
        )

        # Assert
        assert resultado == {"tipo_incidencia": "tecnica", "prioridad": "alta"}

    def test_clasificar_when_no_match_returns_none(self, mock_pinot, mock_kafka):
        # Arrange
        service = ClasificacionAutomaticaService()

        # Act
        resultado = service.clasificar(tipo="otro", asunto="xyz", descripcion="qwerty")

        # Assert
        assert resultado is None
