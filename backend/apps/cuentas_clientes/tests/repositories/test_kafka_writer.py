import pytest

from core.repositories.cuentas_clientes.kafka_writer import KafkaWriter


@pytest.mark.repository
class TestKafkaWriter:
    def test_publish_when_called_stores_message(self, mock_kafka):
        # Arrange
        writer = KafkaWriter()

        # Act
        writer.publish("Fact_Session_topic", {"idsession": 99, "estadosession": "Inicio sesion"})

        # Assert
        assert len(mock_kafka) == 1
        assert mock_kafka[0]["topic"] == "Fact_Session_topic"
        assert mock_kafka[0]["payload"]["idsession"] == 99
