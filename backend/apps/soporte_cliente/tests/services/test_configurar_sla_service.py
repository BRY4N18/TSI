import pytest

from apps.soporte_cliente.services.configurar_sla_service import ConfigurarSLAService


@pytest.mark.service
class TestConfigurarSLAService:
    def test_crear_when_valido_publica_regla_activa(self, mock_pinot, mock_kafka):
        # Arrange
        service = ConfigurarSLAService()

        # Act
        regla = service.crear(
            idplan=1,
            tipoincidencia="consulta_general",
            prioridad="baja",
            tiemporespuestamax=3600,
            tiemporesolucionmax=86400,
        )

        # Assert
        assert regla["activo"] is True
        assert regla["fechavigenciahasta"] is None

    def test_crear_when_tiempos_invalidos_raises(self, mock_pinot, mock_kafka):
        # Arrange
        service = ConfigurarSLAService()

        # Act / Assert
        with pytest.raises(ValueError):
            service.crear(
                idplan=1,
                tipoincidencia="x",
                prioridad="baja",
                tiemporespuestamax=100,
                tiemporesolucionmax=50,
            )

    def test_modificar_when_valido_desactiva_y_crea_nueva(self, mock_pinot, mock_kafka):
        # Arrange
        service = ConfigurarSLAService()

        # Act
        nueva = service.modificar(1, tiemporespuestamax=1800, tiemporesolucionmax=43200)

        # Assert
        assert nueva["idslaconfig"] != 1
        assert nueva["tiemporespuestamax"] == 1800
