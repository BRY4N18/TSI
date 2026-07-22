import pytest

from apps.red_operativa.services.registro_unidad_service import RegistroUnidadService


@pytest.mark.service
class TestRegistroUnidadService:
    def _valid_data(self, **overrides):
        data = {
            "idcliente": 1,
            "idcondado": 1,
            "tipopropiedad": "Externa",
            "placa": "SVC-001",
            "contactoproveedor": "5551234",
            "unidademergencia": "Ambulancia Sur",
            "tipounidademergencia": "Ambulancia",
        }
        data.update(overrides)
        return data

    def test_registrar_when_valid_creates_unidad(self, mock_pinot, mock_kafka):
        # Arrange
        service = RegistroUnidadService()

        # Act
        result = service.registrar(self._valid_data())

        # Assert
        assert result["placa"] == "SVC-001"
        assert result["activo"] is True

    def test_registrar_when_placa_duplicada_raises_value_error(
        self, mock_pinot, mock_kafka, mock_unidad_emergencia
    ):
        # Arrange
        service = RegistroUnidadService()
        data = self._valid_data(placa=mock_unidad_emergencia["placa"])

        # Act & Assert
        with pytest.raises(ValueError):
            service.registrar(data)

    def test_registrar_when_idcondado_invalido_raises_lookup_error(self, mock_pinot, mock_kafka):
        # Arrange
        service = RegistroUnidadService()
        data = self._valid_data(idcondado=999999)

        # Act & Assert
        with pytest.raises(LookupError):
            service.registrar(data)

    def test_registrar_when_externa_sin_contacto_raises_key_error(self, mock_pinot, mock_kafka):
        # Arrange
        service = RegistroUnidadService()
        data = self._valid_data(contactoproveedor=None)

        # Act & Assert
        with pytest.raises(KeyError):
            service.registrar(data)

    def test_registrar_when_tipopropiedad_invalido_raises_key_error(self, mock_pinot, mock_kafka):
        # Arrange
        service = RegistroUnidadService()
        data = self._valid_data(tipopropiedad="Otro")

        # Act & Assert
        with pytest.raises(KeyError):
            service.registrar(data)
